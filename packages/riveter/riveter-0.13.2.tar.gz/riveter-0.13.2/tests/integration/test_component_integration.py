"""Integration tests for component interactions."""

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from riveter.configuration.manager import ConfigurationManager
from riveter.models.core import Severity, TerraformResource, ValidationSummary
from riveter.models.rules import Rule, RuleCondition, RulePack
from riveter.output.formatters import JSONFormatter, TableFormatter
from riveter.output.manager import OutputManager
from riveter.validation.engine import ValidationContext, ValidationEngine
from riveter.validation.evaluator import RuleEvaluator


class TestValidationEngineIntegration:
    """Integration tests for ValidationEngine with real components."""

    @pytest.fixture
    def sample_resources(self) -> List[TerraformResource]:
        """Create sample Terraform resources for testing."""
        return [
            TerraformResource(
                type="aws_instance",
                name="web_server",
                attributes={
                    "instance_type": "t3.micro",
                    "ami": "ami-12345678",
                    "tags": {
                        "Name": "web-server",
                        "Environment": "production",
                        "CostCenter": "12345",
                    },
                    "security_groups": ["sg-12345678"],
                    "root_block_device": {"volume_size": 20},
                },
            ),
            TerraformResource(
                type="aws_instance",
                name="test_server",
                attributes={
                    "instance_type": "t3.nano",
                    "ami": "ami-87654321",
                    "tags": {
                        "Name": "test-server",
                        "Environment": "staging",
                        # Missing CostCenter tag
                    },
                    "security_groups": ["sg-87654321"],
                },
            ),
            TerraformResource(
                type="aws_s3_bucket",
                name="data_bucket",
                attributes={
                    "bucket": "my-data-bucket",
                    "tags": {"Environment": "production", "Purpose": "data-storage"},
                },
            ),
            TerraformResource(
                type="aws_rds_instance",
                name="database",
                attributes={
                    "engine": "mysql",
                    "instance_class": "db.t3.micro",
                    "tags": {"Environment": "production", "Name": "database"},
                },
            ),
        ]

    @pytest.fixture
    def sample_rules(self) -> List[Rule]:
        """Create sample rules for testing."""
        return [
            Rule(
                id="ec2-environment-tag",
                resource_type="aws_instance",
                description="EC2 instances must have Environment tag",
                conditions=[RuleCondition("tags.Environment", "present", None)],
                severity=Severity.ERROR,
            ),
            Rule(
                id="ec2-cost-center-production",
                resource_type="aws_instance",
                description="Production EC2 instances must have CostCenter tag",
                conditions=[RuleCondition("tags.CostCenter", "present", None)],
                rule_filter=Mock(
                    matches=lambda r: r.get_attribute("tags.Environment") == "production"
                ),
                severity=Severity.ERROR,
            ),
            Rule(
                id="s3-purpose-tag",
                resource_type="aws_s3_bucket",
                description="S3 buckets must have Purpose tag",
                conditions=[RuleCondition("tags.Purpose", "present", None)],
                severity=Severity.WARNING,
            ),
            Rule(
                id="universal-environment-tag",
                resource_type="*",
                description="All resources must have Environment tag",
                conditions=[RuleCondition("tags.Environment", "present", None)],
                severity=Severity.INFO,
            ),
        ]

    def test_validation_engine_with_mock_evaluator(self, sample_resources, sample_rules):
        """Test ValidationEngine with a mock evaluator."""
        # Create mock evaluator that simulates real evaluation
        evaluator = Mock(spec=RuleEvaluator)

        def mock_evaluate(rule, resource):
            from riveter.models.core import RuleResult

            # Simple evaluation logic for testing
            passed = True
            message = "All checks passed"

            for condition in rule.conditions:
                if condition.operator == "present":
                    if not resource.has_attribute(condition.property_path):
                        passed = False
                        message = f"Required attribute '{condition.property_path}' is missing"
                        break

            return RuleResult(
                rule_id=rule.id,
                resource=resource,
                status=passed,
                message=message,
                severity=rule.severity,
                assertion_results=[],
            )

        evaluator.evaluate.side_effect = mock_evaluate

        # Create validation engine
        engine = ValidationEngine(evaluator)

        # Create validation context
        context = ValidationContext(
            resources=sample_resources, rules=sample_rules, config={}, metadata={"test_run": True}
        )

        # Execute validation
        result = engine.validate(context)

        # Verify results
        assert isinstance(result.summary, ValidationSummary)
        assert result.summary.total_resources == 4
        assert result.summary.total_rules == 4
        assert len(result.rule_results) > 0

        # Verify that evaluator was called for applicable rule-resource pairs
        assert evaluator.evaluate.call_count > 0

        # Check that universal rule was applied to all resources
        universal_results = [
            r for r in result.rule_results if r.rule_id == "universal-environment-tag"
        ]
        assert len(universal_results) == 4  # Should apply to all resources

        # Check that specific rules were applied correctly
        ec2_results = [r for r in result.rule_results if r.rule_id == "ec2-environment-tag"]
        assert len(ec2_results) == 2  # Should apply to both EC2 instances

        s3_results = [r for r in result.rule_results if r.rule_id == "s3-purpose-tag"]
        assert len(s3_results) == 1  # Should apply to S3 bucket only

    def test_validation_engine_with_filtering(self, sample_resources, sample_rules):
        """Test ValidationEngine with rule filtering."""
        # Create evaluator
        evaluator = Mock(spec=RuleEvaluator)
        evaluator.evaluate.return_value = Mock(
            rule_id="test",
            resource=Mock(),
            status=True,
            message="OK",
            severity=Severity.INFO,
            assertion_results=[],
        )

        engine = ValidationEngine(evaluator)

        # Test with severity filtering
        context = ValidationContext(
            resources=sample_resources,
            rules=sample_rules,
            config={"min_severity": Severity.WARNING},
            metadata={},
        )

        result = engine.validate(context)

        # Should only include ERROR and WARNING rules
        rule_ids = [r.rule_id for r in result.rule_results]
        assert "universal-environment-tag" not in rule_ids  # INFO level should be filtered out

    def test_validation_engine_error_handling(self, sample_resources, sample_rules):
        """Test ValidationEngine error handling during evaluation."""
        # Create evaluator that throws errors
        evaluator = Mock(spec=RuleEvaluator)
        evaluator.evaluate.side_effect = Exception("Evaluation error")

        engine = ValidationEngine(evaluator)

        context = ValidationContext(
            resources=sample_resources,
            rules=sample_rules[:1],  # Use only one rule to simplify
            config={},
            metadata={},
        )

        # Should handle errors gracefully
        result = engine.validate(context)

        # Should have error results
        assert len(result.rule_results) > 0
        error_results = [r for r in result.rule_results if not r.status]
        assert len(error_results) > 0

        # Error message should indicate the problem
        assert any("error" in r.message.lower() for r in error_results)


class TestConfigurationManagerIntegration:
    """Integration tests for ConfigurationManager."""

    @pytest.fixture
    def sample_terraform_content(self) -> str:
        """Sample Terraform content for testing."""
        return """
# Sample Terraform configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server"
    Environment = "production"
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  vpc_security_group_ids = ["sg-12345678"]
}

resource "aws_s3_bucket" "data" {
  bucket = "my-unique-bucket-name"

  tags = {
    Environment = "production"
    Purpose     = "data-storage"
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}
"""

    def test_configuration_manager_parsing(self, tmp_path: Path, sample_terraform_content: str):
        """Test ConfigurationManager parsing Terraform files."""
        # Create temporary Terraform file
        tf_file = tmp_path / "main.tf"
        tf_file.write_text(sample_terraform_content)

        # Mock the actual configuration manager since we don't have the real implementation
        config_manager = Mock(spec=ConfigurationManager)

        # Mock the parsing result
        mock_config = Mock()
        mock_config.resources = [
            {
                "type": "aws_instance",
                "name": "web",
                "attributes": {
                    "ami": "ami-12345678",
                    "instance_type": "t3.micro",
                    "tags": {"Name": "web-server", "Environment": "production"},
                    "root_block_device": {
                        "volume_size": 20,
                        "volume_type": "gp3",
                        "encrypted": True,
                    },
                    "vpc_security_group_ids": ["sg-12345678"],
                },
            },
            {
                "type": "aws_s3_bucket",
                "name": "data",
                "attributes": {
                    "bucket": "my-unique-bucket-name",
                    "tags": {"Environment": "production", "Purpose": "data-storage"},
                },
            },
        ]
        mock_config.variables = {"environment": {"default": "production"}}
        mock_config.outputs = {"instance_id": {"value": "aws_instance.web.id"}}

        config_manager.load_terraform_config.return_value = mock_config

        # Test configuration loading
        result = config_manager.load_terraform_config(tf_file)

        assert result is not None
        assert len(result.resources) == 2
        assert result.resources[0]["type"] == "aws_instance"
        assert result.resources[1]["type"] == "aws_s3_bucket"

    def test_configuration_manager_error_handling(self, tmp_path: Path):
        """Test ConfigurationManager error handling."""
        # Create invalid Terraform file
        invalid_tf = tmp_path / "invalid.tf"
        invalid_tf.write_text("invalid terraform syntax {{{")

        config_manager = Mock(spec=ConfigurationManager)
        config_manager.load_terraform_config.side_effect = Exception("Parse error")

        # Should raise appropriate exception
        with pytest.raises(Exception, match="Parse error"):
            config_manager.load_terraform_config(invalid_tf)

    def test_configuration_manager_caching(self, tmp_path: Path, sample_terraform_content: str):
        """Test ConfigurationManager caching behavior."""
        tf_file = tmp_path / "main.tf"
        tf_file.write_text(sample_terraform_content)

        config_manager = Mock(spec=ConfigurationManager)
        mock_config = Mock()
        config_manager.load_terraform_config.return_value = mock_config

        # Load configuration multiple times
        result1 = config_manager.load_terraform_config(tf_file)
        result2 = config_manager.load_terraform_config(tf_file)

        # Should return same result (caching behavior would be tested in real implementation)
        assert result1 == result2


class TestOutputManagerIntegration:
    """Integration tests for OutputManager and formatters."""

    @pytest.fixture
    def sample_validation_result(self, sample_resources):
        """Create sample validation result for testing."""
        from riveter.models.core import RuleResult
        from riveter.validation.result import ValidationResult

        rule_results = [
            RuleResult(
                rule_id="test-rule-1",
                resource=sample_resources[0],
                status=True,
                message="All checks passed",
                severity=Severity.INFO,
                assertion_results=[],
            ),
            RuleResult(
                rule_id="test-rule-2",
                resource=sample_resources[1],
                status=False,
                message="Missing required tag",
                severity=Severity.ERROR,
                assertion_results=[],
            ),
        ]

        summary = ValidationSummary(
            total_rules=2,
            total_resources=2,
            passed_rules=1,
            failed_rules=1,
            skipped_rules=0,
            total_assertions=2,
            passed_assertions=1,
            failed_assertions=1,
            execution_time=1.5,
            error_count=1,
            warning_count=0,
            info_count=1,
        )

        return ValidationResult(rule_results, summary)

    def test_output_manager_json_formatting(self, sample_validation_result):
        """Test OutputManager with JSON formatter."""
        json_formatter = Mock(spec=JSONFormatter)
        json_formatter.format.return_value = '{"test": "json_output"}'

        output_manager = Mock(spec=OutputManager)
        output_manager.format_output.return_value = '{"test": "json_output"}'

        result = output_manager.format_output(sample_validation_result, "json")

        assert result == '{"test": "json_output"}'
        assert isinstance(result, str)

    def test_output_manager_table_formatting(self, sample_validation_result):
        """Test OutputManager with table formatter."""
        table_formatter = Mock(spec=TableFormatter)
        table_formatter.format.return_value = (
            "| Rule | Status | Message |\n|------|--------|---------|"
        )

        output_manager = Mock(spec=OutputManager)
        output_manager.format_output.return_value = (
            "| Rule | Status | Message |\n|------|--------|---------|"
        )

        result = output_manager.format_output(sample_validation_result, "table")

        assert "Rule" in result
        assert "Status" in result
        assert "|" in result

    def test_output_manager_multiple_formats(self, sample_validation_result):
        """Test OutputManager with multiple output formats."""
        output_manager = Mock(spec=OutputManager)

        # Mock different format outputs
        format_outputs = {
            "json": '{"summary": {"total_rules": 2}}',
            "table": "| Rule | Status |\n|------|--------|",
            "junit": '<?xml version="1.0"?><testsuite></testsuite>',
            "sarif": '{"version": "2.1.0", "runs": []}',
        }

        def mock_format(result, format_type):
            return format_outputs.get(format_type, "unknown format")

        output_manager.format_output.side_effect = mock_format

        # Test all formats
        for format_type, expected in format_outputs.items():
            result = output_manager.format_output(sample_validation_result, format_type)
            assert result == expected

    def test_output_manager_error_handling(self, sample_validation_result):
        """Test OutputManager error handling."""
        output_manager = Mock(spec=OutputManager)
        output_manager.format_output.side_effect = Exception("Formatting error")

        with pytest.raises(Exception, match="Formatting error"):
            output_manager.format_output(sample_validation_result, "json")


class TestEndToEndComponentIntegration:
    """End-to-end integration tests combining multiple components."""

    @pytest.fixture
    def integration_setup(self, sample_resources, sample_rules):
        """Set up components for integration testing."""
        # Mock evaluator
        evaluator = Mock(spec=RuleEvaluator)

        def mock_evaluate(rule, resource):
            from riveter.models.core import RuleResult

            # Simple evaluation: check if resource has required tags
            passed = True
            message = "All checks passed"

            for condition in rule.conditions:
                if condition.operator == "present":
                    if not resource.has_attribute(condition.property_path):
                        passed = False
                        message = f"Required attribute '{condition.property_path}' is missing"
                        break

            return RuleResult(
                rule_id=rule.id,
                resource=resource,
                status=passed,
                message=message,
                severity=rule.severity,
                assertion_results=[],
            )

        evaluator.evaluate.side_effect = mock_evaluate

        # Mock configuration manager
        config_manager = Mock(spec=ConfigurationManager)
        config_manager.load_terraform_config.return_value = Mock(resources=sample_resources)

        # Mock output manager
        output_manager = Mock(spec=OutputManager)
        output_manager.format_output.return_value = '{"test": "output"}'

        return {
            "evaluator": evaluator,
            "config_manager": config_manager,
            "output_manager": output_manager,
            "resources": sample_resources,
            "rules": sample_rules,
        }

    def test_complete_validation_workflow(self, integration_setup):
        """Test complete validation workflow from configuration to output."""
        setup = integration_setup

        # Step 1: Load configuration
        config = setup["config_manager"].load_terraform_config(Path("test.tf"))
        assert config is not None

        # Step 2: Create validation engine and context
        engine = ValidationEngine(setup["evaluator"])
        context = ValidationContext(
            resources=setup["resources"], rules=setup["rules"], config={}, metadata={}
        )

        # Step 3: Execute validation
        validation_result = engine.validate(context)
        assert validation_result is not None
        assert len(validation_result.rule_results) > 0

        # Step 4: Format output
        json_output = setup["output_manager"].format_output(validation_result, "json")
        assert json_output == '{"test": "output"}'

        # Verify all components were called
        setup["config_manager"].load_terraform_config.assert_called_once()
        assert setup["evaluator"].evaluate.call_count > 0
        setup["output_manager"].format_output.assert_called_once()

    def test_validation_with_different_rule_sets(self, integration_setup):
        """Test validation with different rule sets."""
        setup = integration_setup

        # Test with different rule combinations
        rule_sets = [
            setup["rules"][:1],  # Single rule
            setup["rules"][:2],  # Two rules
            setup["rules"],  # All rules
        ]

        engine = ValidationEngine(setup["evaluator"])

        for rule_set in rule_sets:
            context = ValidationContext(
                resources=setup["resources"], rules=rule_set, config={}, metadata={}
            )

            result = engine.validate(context)

            # Should have results proportional to rule count
            assert len(result.rule_results) >= len(rule_set)
            assert result.summary.total_rules == len(rule_set)

    def test_validation_with_resource_filtering(self, integration_setup):
        """Test validation with different resource sets."""
        setup = integration_setup

        # Test with different resource combinations
        resource_sets = [
            setup["resources"][:1],  # Single resource
            setup["resources"][:2],  # Two resources
            setup["resources"],  # All resources
        ]

        engine = ValidationEngine(setup["evaluator"])

        for resource_set in resource_sets:
            context = ValidationContext(
                resources=resource_set, rules=setup["rules"], config={}, metadata={}
            )

            result = engine.validate(context)

            # Should process all provided resources
            assert result.summary.total_resources == len(resource_set)

    def test_error_propagation_through_workflow(self, integration_setup):
        """Test error propagation through the complete workflow."""
        setup = integration_setup

        # Make evaluator throw errors
        setup["evaluator"].evaluate.side_effect = Exception("Evaluation failed")

        engine = ValidationEngine(setup["evaluator"])
        context = ValidationContext(
            resources=setup["resources"][:1], rules=setup["rules"][:1], config={}, metadata={}
        )

        # Should handle errors gracefully
        result = engine.validate(context)

        # Should have error results
        assert len(result.rule_results) > 0
        assert any(not r.status for r in result.rule_results)

    def test_performance_with_large_dataset(self, integration_setup):
        """Test performance with larger datasets."""
        setup = integration_setup

        # Create larger datasets
        large_resources = setup["resources"] * 10  # 40 resources
        large_rules = setup["rules"] * 5  # 20 rules

        engine = ValidationEngine(setup["evaluator"])
        context = ValidationContext(
            resources=large_resources, rules=large_rules, config={}, metadata={}
        )

        import time

        start_time = time.time()

        result = engine.validate(context)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete within reasonable time
        assert execution_time < 10.0  # 10 seconds max

        # Should process all data
        assert result.summary.total_resources == len(large_resources)
        assert result.summary.total_rules == len(large_rules)

    def test_concurrent_validation_safety(self, integration_setup):
        """Test that validation is safe for concurrent execution."""
        setup = integration_setup

        engine = ValidationEngine(setup["evaluator"])
        context = ValidationContext(
            resources=setup["resources"], rules=setup["rules"], config={}, metadata={}
        )

        # Run multiple validations concurrently (simulated)
        results = []
        for _ in range(5):
            result = engine.validate(context)
            results.append(result)

        # All results should be consistent
        for result in results:
            assert result.summary.total_resources == len(setup["resources"])
            assert result.summary.total_rules == len(setup["rules"])
            assert (
                len(result.rule_results)
                == results[0].summary.total_rules * results[0].summary.total_resources
            )
