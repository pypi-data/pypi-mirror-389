"""Unit tests for the validation engine."""

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock

import pytest

from riveter.models.core import RuleResult, Severity, TerraformResource, ValidationSummary
from riveter.models.rules import Rule, RuleCondition
from riveter.validation.engine import ValidationEngine, ValidationEngineConfig
from riveter.validation.evaluator import RuleEvaluator
from riveter.validation.result import ValidationResult


class TestValidationContext:
    """Test cases for the ValidationContext data class."""

    def test_validation_context_creation(self):
        """Test creating a ValidationContext instance."""
        resources = [
            TerraformResource("aws_instance", "web", {"type": "t3.micro"}),
            TerraformResource("aws_s3_bucket", "data", {"bucket": "my-bucket"}),
        ]

        rules = [
            Rule(
                "rule1", "aws_instance", "Test rule", [RuleCondition("type", "equals", "t3.micro")]
            )
        ]

        context = ValidationContext(
            resources=resources,
            rules=rules,
            config={"strict_mode": True},
            metadata={"scan_id": "test-123"},
        )

        assert len(context.resources) == 2
        assert len(context.rules) == 1
        assert context.config["strict_mode"] is True
        assert context.metadata["scan_id"] == "test-123"

    def test_validation_context_immutable(self):
        """Test that ValidationContext is immutable."""
        context = ValidationContext([], [], {}, {})

        with pytest.raises(AttributeError):
            context.resources = []  # type: ignore

    def test_validation_context_get_resources_by_type(self):
        """Test getting resources by type from ValidationContext."""
        resources = [
            TerraformResource("aws_instance", "web1", {}),
            TerraformResource("aws_instance", "web2", {}),
            TerraformResource("aws_s3_bucket", "data", {}),
        ]

        context = ValidationContext(resources, [], {}, {})

        ec2_resources = context.get_resources_by_type("aws_instance")
        s3_resources = context.get_resources_by_type("aws_s3_bucket")
        rds_resources = context.get_resources_by_type("aws_rds_instance")

        assert len(ec2_resources) == 2
        assert len(s3_resources) == 1
        assert len(rds_resources) == 0

    def test_validation_context_get_rules_for_resource_type(self):
        """Test getting applicable rules for resource type."""
        rules = [
            Rule("rule1", "aws_instance", "EC2 rule", [RuleCondition("path", "op", "val")]),
            Rule("rule2", "aws_s3_bucket", "S3 rule", [RuleCondition("path", "op", "val")]),
            Rule("rule3", "*", "Universal rule", [RuleCondition("path", "op", "val")]),
        ]

        context = ValidationContext([], rules, {}, {})

        ec2_rules = context.get_rules_for_resource_type("aws_instance")
        s3_rules = context.get_rules_for_resource_type("aws_s3_bucket")
        rds_rules = context.get_rules_for_resource_type("aws_rds_instance")

        assert len(ec2_rules) == 2  # specific + universal
        assert len(s3_rules) == 2  # specific + universal
        assert len(rds_rules) == 1  # universal only


class TestValidationEngine:
    """Test cases for the ValidationEngine class."""

    def test_validation_engine_creation(self):
        """Test creating a ValidationEngine instance."""
        evaluator = Mock(spec=RuleEvaluator)
        engine = ValidationEngine(evaluator)

        assert engine.evaluator == evaluator

    def test_validation_engine_validate_empty_context(self):
        """Test validation with empty context."""
        evaluator = Mock(spec=RuleEvaluator)
        engine = ValidationEngine(evaluator)

        context = ValidationContext([], [], {}, {})
        result = engine.validate(context)

        assert isinstance(result, ValidationResult)
        assert len(result.rule_results) == 0
        assert result.summary.total_rules == 0
        assert result.summary.total_resources == 0

    def test_validation_engine_validate_single_rule_single_resource(self):
        """Test validation with single rule and resource."""
        # Mock evaluator
        evaluator = Mock(spec=RuleEvaluator)
        mock_rule_result = RuleResult(
            rule_id="test-rule",
            resource=TerraformResource("aws_instance", "web", {}),
            status=True,
            message="Validation passed",
            severity=Severity.INFO,
            assertion_results=[],
            execution_time=0.1,
        )
        evaluator.evaluate.return_value = mock_rule_result

        engine = ValidationEngine(evaluator)

        # Create context
        resources = [TerraformResource("aws_instance", "web", {"type": "t3.micro"})]
        rules = [
            Rule("test-rule", "aws_instance", "Test", [RuleCondition("type", "equals", "t3.micro")])
        ]
        context = ValidationContext(resources, rules, {}, {})

        # Execute validation
        result = engine.validate(context)

        # Verify results
        assert len(result.rule_results) == 1
        assert result.rule_results[0].rule_id == "test-rule"
        assert result.rule_results[0].status is True
        assert result.summary.total_rules == 1
        assert result.summary.total_resources == 1
        assert result.summary.passed_rules == 1
        assert result.summary.failed_rules == 0

        # Verify evaluator was called correctly
        evaluator.evaluate.assert_called_once()
        call_args = evaluator.evaluate.call_args[0]
        assert call_args[0].id == "test-rule"
        assert call_args[1].name == "web"

    def test_validation_engine_validate_multiple_rules_resources(self):
        """Test validation with multiple rules and resources."""
        # Mock evaluator with different results
        evaluator = Mock(spec=RuleEvaluator)

        def mock_evaluate(rule, resource):
            if rule.id == "rule1":
                return RuleResult(
                    rule_id="rule1",
                    resource=resource,
                    status=True,
                    message="Passed",
                    severity=Severity.INFO,
                    assertion_results=[],
                )
            else:
                return RuleResult(
                    rule_id="rule2",
                    resource=resource,
                    status=False,
                    message="Failed",
                    severity=Severity.ERROR,
                    assertion_results=[],
                )

        evaluator.evaluate.side_effect = mock_evaluate

        engine = ValidationEngine(evaluator)

        # Create context with multiple resources and rules
        resources = [
            TerraformResource("aws_instance", "web1", {}),
            TerraformResource("aws_instance", "web2", {}),
        ]
        rules = [
            Rule("rule1", "aws_instance", "Rule 1", [RuleCondition("path1", "op", "val")]),
            Rule("rule2", "aws_instance", "Rule 2", [RuleCondition("path2", "op", "val")]),
        ]
        context = ValidationContext(resources, rules, {}, {})

        # Execute validation
        result = engine.validate(context)

        # Should have 4 results (2 rules × 2 resources)
        assert len(result.rule_results) == 4
        assert result.summary.total_rules == 2
        assert result.summary.total_resources == 2

        # Count passed/failed results
        passed_results = [r for r in result.rule_results if r.status]
        failed_results = [r for r in result.rule_results if not r.status]

        assert len(passed_results) == 2  # rule1 applied to both resources
        assert len(failed_results) == 2  # rule2 applied to both resources

    def test_validation_engine_validate_with_filters(self):
        """Test validation with rule filters."""
        evaluator = Mock(spec=RuleEvaluator)
        mock_result = RuleResult(
            rule_id="filtered-rule",
            resource=TerraformResource("aws_instance", "prod", {}),
            status=True,
            message="Passed",
            severity=Severity.INFO,
            assertion_results=[],
        )
        evaluator.evaluate.return_value = mock_result

        engine = ValidationEngine(evaluator)

        # Create resources - one matching filter, one not
        resources = [
            TerraformResource("aws_instance", "prod", {"tags": {"Environment": "production"}}),
            TerraformResource("aws_instance", "test", {"tags": {"Environment": "staging"}}),
        ]

        # Create rule with filter (this would need actual filter implementation)
        rules = [
            Rule(
                "filtered-rule",
                "aws_instance",
                "Filtered rule",
                [RuleCondition("path", "op", "val")],
            )
        ]

        context = ValidationContext(resources, rules, {}, {})
        result = engine.validate(context)

        # For now, without filter implementation, both resources would be evaluated
        assert len(result.rule_results) == 2

    def test_validation_engine_validate_with_severity_filtering(self):
        """Test validation with minimum severity filtering."""
        evaluator = Mock(spec=RuleEvaluator)

        def mock_evaluate(rule, resource):
            return RuleResult(
                rule_id=rule.id,
                resource=resource,
                status=True,
                message="Passed",
                severity=rule.severity,
                assertion_results=[],
            )

        evaluator.evaluate.side_effect = mock_evaluate

        engine = ValidationEngine(evaluator)

        # Create rules with different severities
        resources = [TerraformResource("aws_instance", "web", {})]
        rules = [
            Rule(
                "error-rule",
                "aws_instance",
                "Error rule",
                [RuleCondition("p", "o", "v")],
                Severity.ERROR,
            ),
            Rule(
                "warning-rule",
                "aws_instance",
                "Warning rule",
                [RuleCondition("p", "o", "v")],
                Severity.WARNING,
            ),
            Rule(
                "info-rule",
                "aws_instance",
                "Info rule",
                [RuleCondition("p", "o", "v")],
                Severity.INFO,
            ),
        ]

        # Test with minimum severity WARNING
        context = ValidationContext(resources, rules, {"min_severity": Severity.WARNING}, {})
        result = engine.validate(context)

        # Should only include ERROR and WARNING rules
        assert len(result.rule_results) == 2
        rule_ids = [r.rule_id for r in result.rule_results]
        assert "error-rule" in rule_ids
        assert "warning-rule" in rule_ids
        assert "info-rule" not in rule_ids

    def test_validation_engine_validate_performance_tracking(self):
        """Test that validation engine tracks performance metrics."""
        evaluator = Mock(spec=RuleEvaluator)
        mock_result = RuleResult(
            rule_id="perf-rule",
            resource=TerraformResource("aws_instance", "web", {}),
            status=True,
            message="Passed",
            severity=Severity.INFO,
            assertion_results=[],
            execution_time=0.05,
        )
        evaluator.evaluate.return_value = mock_result

        engine = ValidationEngine(evaluator)

        resources = [TerraformResource("aws_instance", "web", {})]
        rules = [Rule("perf-rule", "aws_instance", "Perf rule", [RuleCondition("p", "o", "v")])]
        context = ValidationContext(resources, rules, {}, {})

        result = engine.validate(context)

        # Check that execution time is tracked
        assert result.summary.execution_time > 0
        assert result.rule_results[0].execution_time == 0.05

    def test_validation_engine_validate_error_handling(self):
        """Test validation engine error handling."""
        evaluator = Mock(spec=RuleEvaluator)
        evaluator.evaluate.side_effect = Exception("Evaluation error")

        engine = ValidationEngine(evaluator)

        resources = [TerraformResource("aws_instance", "web", {})]
        rules = [Rule("error-rule", "aws_instance", "Error rule", [RuleCondition("p", "o", "v")])]
        context = ValidationContext(resources, rules, {}, {})

        # Should handle errors gracefully
        result = engine.validate(context)

        # Should have a result indicating the error
        assert len(result.rule_results) == 1
        assert result.rule_results[0].status is False
        assert "error" in result.rule_results[0].message.lower()

    def test_validation_engine_validate_with_parallel_execution(self):
        """Test validation engine with parallel execution enabled."""
        evaluator = Mock(spec=RuleEvaluator)
        mock_result = RuleResult(
            rule_id="parallel-rule",
            resource=TerraformResource("aws_instance", "web", {}),
            status=True,
            message="Passed",
            severity=Severity.INFO,
            assertion_results=[],
        )
        evaluator.evaluate.return_value = mock_result

        engine = ValidationEngine(evaluator)

        resources = [TerraformResource("aws_instance", f"web{i}", {}) for i in range(10)]
        rules = [
            Rule("parallel-rule", "aws_instance", "Parallel rule", [RuleCondition("p", "o", "v")])
        ]

        # Enable parallel execution
        context = ValidationContext(resources, rules, {"parallel": True, "max_workers": 4}, {})
        result = engine.validate(context)

        # Should have results for all resources
        assert len(result.rule_results) == 10
        assert all(r.status for r in result.rule_results)

    def test_validation_engine_validate_summary_calculation(self):
        """Test that validation summary is calculated correctly."""
        evaluator = Mock(spec=RuleEvaluator)

        def mock_evaluate(rule, resource):
            # Make some rules pass and some fail based on rule ID
            status = rule.id.startswith("pass")
            return RuleResult(
                rule_id=rule.id,
                resource=resource,
                status=status,
                message="Passed" if status else "Failed",
                severity=Severity.ERROR if not status else Severity.INFO,
                assertion_results=[],
            )

        evaluator.evaluate.side_effect = mock_evaluate

        engine = ValidationEngine(evaluator)

        resources = [
            TerraformResource("aws_instance", "web1", {}),
            TerraformResource("aws_instance", "web2", {}),
        ]
        rules = [
            Rule("pass-rule1", "aws_instance", "Passing rule 1", [RuleCondition("p", "o", "v")]),
            Rule("pass-rule2", "aws_instance", "Passing rule 2", [RuleCondition("p", "o", "v")]),
            Rule("fail-rule1", "aws_instance", "Failing rule 1", [RuleCondition("p", "o", "v")]),
        ]

        context = ValidationContext(resources, rules, {}, {})
        result = engine.validate(context)

        # Verify summary calculations
        summary = result.summary
        assert summary.total_rules == 3
        assert summary.total_resources == 2
        assert summary.passed_rules == 4  # 2 passing rules × 2 resources
        assert summary.failed_rules == 2  # 1 failing rule × 2 resources
        assert summary.error_count == 2  # Failed rules have ERROR severity
        assert summary.info_count == 4  # Passed rules have INFO severity
        assert summary.success_rate == 4 / 6  # 4 passed out of 6 total evaluations

    def test_validation_engine_validate_resource_type_matching(self):
        """Test that rules are only applied to matching resource types."""
        evaluator = Mock(spec=RuleEvaluator)
        mock_result = RuleResult(
            rule_id="ec2-rule",
            resource=TerraformResource("aws_instance", "web", {}),
            status=True,
            message="Passed",
            severity=Severity.INFO,
            assertion_results=[],
        )
        evaluator.evaluate.return_value = mock_result

        engine = ValidationEngine(evaluator)

        resources = [
            TerraformResource("aws_instance", "web", {}),
            TerraformResource("aws_s3_bucket", "data", {}),
            TerraformResource("aws_rds_instance", "db", {}),
        ]
        rules = [
            Rule("ec2-rule", "aws_instance", "EC2 rule", [RuleCondition("p", "o", "v")]),
            Rule("universal-rule", "*", "Universal rule", [RuleCondition("p", "o", "v")]),
        ]

        context = ValidationContext(resources, rules, {}, {})
        result = engine.validate(context)

        # ec2-rule should only apply to aws_instance (1 result)
        # universal-rule should apply to all resources (3 results)
        # Total: 4 results
        assert len(result.rule_results) == 4

        # Verify rule applications
        ec2_rule_results = [r for r in result.rule_results if r.rule_id == "ec2-rule"]
        universal_rule_results = [r for r in result.rule_results if r.rule_id == "universal-rule"]

        assert len(ec2_rule_results) == 1
        assert len(universal_rule_results) == 3
        assert ec2_rule_results[0].resource.type == "aws_instance"


class TestValidationEngineIntegration:
    """Integration tests for ValidationEngine with real components."""

    def test_validation_engine_with_real_evaluator(self):
        """Test ValidationEngine with a real RuleEvaluator implementation."""
        # This would require implementing a real evaluator
        # For now, we'll use a mock that simulates real behavior

        class MockRealEvaluator:
            def evaluate(self, rule: Rule, resource: TerraformResource) -> RuleResult:
                # Simulate real evaluation logic
                passed = True
                message = "All checks passed"

                # Simple evaluation: check if resource has required attributes
                for condition in rule.conditions:
                    if condition.property_path == "tags.Environment":
                        if condition.operator == "present":
                            if not resource.has_attribute("tags.Environment"):
                                passed = False
                                message = "Required tag 'Environment' is missing"
                                break
                        elif condition.operator == "equals":
                            actual = resource.get_attribute("tags.Environment")
                            if actual != condition.expected_value:
                                passed = False
                                message = f"Tag 'Environment' has value '{actual}' but expected '{condition.expected_value}'"
                                break

                return RuleResult(
                    rule_id=rule.id,
                    resource=resource,
                    status=passed,
                    message=message,
                    severity=rule.severity,
                    assertion_results=[],
                )

        evaluator = MockRealEvaluator()
        engine = ValidationEngine(evaluator)

        # Test with resources that should pass and fail
        resources = [
            TerraformResource(
                "aws_instance",
                "prod_web",
                {"tags": {"Environment": "production", "Name": "web-server"}},
            ),
            TerraformResource(
                "aws_instance",
                "test_web",
                {"tags": {"Name": "test-server"}},  # Missing Environment tag
            ),
            TerraformResource(
                "aws_instance",
                "staging_web",
                {"tags": {"Environment": "staging", "Name": "staging-server"}},
            ),
        ]

        rules = [
            Rule(
                "env-present",
                "aws_instance",
                "Environment tag must be present",
                [RuleCondition("tags.Environment", "present", None)],
                Severity.ERROR,
            ),
            Rule(
                "env-production",
                "aws_instance",
                "Environment must be production",
                [RuleCondition("tags.Environment", "equals", "production")],
                Severity.WARNING,
            ),
        ]

        context = ValidationContext(resources, rules, {}, {})
        result = engine.validate(context)

        # Should have 6 results (2 rules × 3 resources)
        assert len(result.rule_results) == 6

        # Check specific results
        env_present_results = [r for r in result.rule_results if r.rule_id == "env-present"]
        env_production_results = [r for r in result.rule_results if r.rule_id == "env-production"]

        # env-present rule: should pass for prod_web and staging_web, fail for test_web
        passed_present = [r for r in env_present_results if r.status]
        failed_present = [r for r in env_present_results if not r.status]
        assert len(passed_present) == 2
        assert len(failed_present) == 1
        assert failed_present[0].resource.name == "test_web"

        # env-production rule: should pass only for prod_web
        passed_production = [r for r in env_production_results if r.status]
        failed_production = [r for r in env_production_results if not r.status]
        assert len(passed_production) == 1
        assert len(failed_production) == 2
        assert passed_production[0].resource.name == "prod_web"
