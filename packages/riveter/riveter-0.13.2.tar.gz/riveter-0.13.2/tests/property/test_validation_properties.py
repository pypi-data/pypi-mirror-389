"""Property-based tests for validation logic using Hypothesis."""

from typing import Any, Dict, List, Union

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from riveter.models.core import RuleResult, Severity, TerraformResource, ValidationSummary
from riveter.models.rules import Rule, RuleCondition, RuleFilter
from riveter.validation.engine import ValidationContext, ValidationEngine


# Extended strategies for more comprehensive testing
@st.composite
def complex_terraform_resource_strategy(draw):
    """Generate complex TerraformResource instances with nested data."""
    resource_types = st.sampled_from(
        [
            "aws_instance",
            "aws_s3_bucket",
            "aws_rds_instance",
            "aws_lambda_function",
            "google_compute_instance",
            "google_storage_bucket",
            "google_sql_database_instance",
            "azurerm_virtual_machine",
            "azurerm_storage_account",
            "azurerm_sql_database",
            "kubernetes_deployment",
            "kubernetes_service",
            "kubernetes_ingress",
        ]
    )

    resource_type = draw(resource_types)
    name = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "-", "_")),
        )
    )

    # Generate complex nested attributes
    attributes = draw(
        st.recursive(
            st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000, max_value=1000),
                st.floats(
                    min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
                ),
                st.booleans(),
                st.none(),
            ),
            lambda children: st.one_of(
                st.dictionaries(
                    st.text(
                        min_size=1,
                        max_size=20,
                        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "_")),
                    ),
                    children,
                    min_size=0,
                    max_size=10,
                ),
                st.lists(children, min_size=0, max_size=10),
            ),
            max_leaves=50,
        )
    )

    return TerraformResource(type=resource_type, name=name, attributes=attributes)


@st.composite
def complex_rule_condition_strategy(draw):
    """Generate complex RuleCondition instances."""
    # More diverse property paths
    property_paths = st.one_of(
        st.just("tags.Environment"),
        st.just("tags.CostCenter"),
        st.just("instance_type"),
        st.just("ami"),
        st.just("security_groups"),
        st.just("root_block_device.volume_size"),
        st.just("root_block_device.encrypted"),
        st.just("metadata.labels.app"),
        st.just("spec.replicas"),
        st.just("spec.containers[0].image"),
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", ".", "[", "]", "_")),
        ),
    )

    operators = st.sampled_from(
        [
            "equals",
            "present",
            "regex",
            "gte",
            "lte",
            "gt",
            "lt",
            "contains",
            "length",
            "starts_with",
            "ends_with",
            "in",
            "not_in",
        ]
    )

    property_path = draw(property_paths)
    operator = draw(operators)

    # Generate appropriate expected values based on operator
    if operator == "present":
        expected_value = None
    elif operator in ["equals", "contains", "starts_with", "ends_with"]:
        expected_value = draw(st.text(max_size=100))
    elif operator in ["gte", "lte", "gt", "lt"]:
        expected_value = draw(
            st.one_of(
                st.integers(min_value=-1000, max_value=1000),
                st.floats(
                    min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
                ),
            )
        )
    elif operator == "regex":
        # Generate simple regex patterns
        patterns = [
            r"^[a-zA-Z]+$",
            r"\d+",
            r"^(prod|staging|dev)$",
            r"^ami-[0-9a-f]+$",
            r"^t3\.",
            r".*test.*",
        ]
        expected_value = draw(st.sampled_from(patterns))
    elif operator == "length":
        expected_value = draw(
            st.dictionaries(
                st.sampled_from(["gte", "lte", "gt", "lt", "equals"]),
                st.integers(min_value=0, max_value=100),
                min_size=1,
                max_size=2,
            )
        )
    elif operator in ["in", "not_in"]:
        expected_value = draw(st.lists(st.text(max_size=50), min_size=1, max_size=10))
    else:
        expected_value = draw(
            st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000, max_value=1000),
                st.booleans(),
                st.lists(st.text(max_size=20), max_size=5),
            )
        )

    return RuleCondition(
        property_path=property_path, operator=operator, expected_value=expected_value
    )


@st.composite
def complex_rule_strategy(draw):
    """Generate complex Rule instances."""
    rule_id = draw(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "-", "_", ".")),
        )
    )
    resource_type = draw(
        st.sampled_from(
            [
                "aws_instance",
                "aws_s3_bucket",
                "aws_rds_instance",
                "*",
                "google_compute_instance",
                "azurerm_virtual_machine",
                "kubernetes_deployment",
            ]
        )
    )
    description = draw(st.text(max_size=500))
    severity = draw(st.sampled_from([Severity.ERROR, Severity.WARNING, Severity.INFO]))

    conditions = draw(st.lists(complex_rule_condition_strategy(), min_size=1, max_size=10))

    # Sometimes add a filter
    rule_filter = None
    if draw(st.booleans()):
        filter_conditions = draw(
            st.lists(complex_rule_condition_strategy(), min_size=1, max_size=3)
        )
        rule_filter = RuleFilter(filter_conditions)

    return Rule(
        id=rule_id,
        resource_type=resource_type,
        description=description,
        conditions=conditions,
        severity=severity,
        rule_filter=rule_filter,
    )


class TestValidationEngineProperties:
    """Property-based tests for ValidationEngine behavior."""

    @given(
        st.lists(complex_terraform_resource_strategy(), min_size=0, max_size=20),
        st.lists(complex_rule_strategy(), min_size=0, max_size=10),
    )
    @settings(max_examples=50, deadline=5000)
    def test_validation_engine_never_crashes(self, resources, rules):
        """Property: ValidationEngine should never crash regardless of input."""
        from unittest.mock import Mock

        # Create a mock evaluator that always succeeds
        evaluator = Mock()
        evaluator.evaluate.return_value = RuleResult(
            rule_id="mock-rule",
            resource=Mock(),
            status=True,
            message="Mock evaluation",
            severity=Severity.INFO,
            assertion_results=[],
        )

        engine = ValidationEngine(evaluator)
        context = ValidationContext(resources, rules, {}, {})

        try:
            result = engine.validate(context)

            # Basic invariants
            assert isinstance(result.summary, ValidationSummary)
            assert result.summary.total_resources == len(resources)
            assert result.summary.total_rules == len(rules)
            assert len(result.rule_results) >= 0

        except Exception as e:
            pytest.fail(
                f"ValidationEngine crashed with input: resources={len(resources)}, rules={len(rules)}, error={e}"
            )

    @given(
        st.lists(complex_terraform_resource_strategy(), min_size=1, max_size=10),
        st.lists(complex_rule_strategy(), min_size=1, max_size=5),
    )
    @settings(max_examples=30)
    def test_validation_result_count_property(self, resources, rules):
        """Property: Number of results should match applicable rule-resource pairs."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = RuleResult(
            rule_id="test",
            resource=Mock(),
            status=True,
            message="Test",
            severity=Severity.INFO,
            assertion_results=[],
        )

        engine = ValidationEngine(evaluator)
        context = ValidationContext(resources, rules, {}, {})

        result = engine.validate(context)

        # Count expected rule-resource pairs
        expected_pairs = 0
        for rule in rules:
            for resource in resources:
                if rule.matches_resource_type(resource):
                    expected_pairs += 1

        # Should have one result per applicable pair
        assert len(result.rule_results) == expected_pairs

    @given(complex_terraform_resource_strategy())
    @settings(max_examples=100)
    def test_resource_attribute_access_properties(self, resource):
        """Property: Resource attribute access should be consistent and safe."""
        # Property 1: get_attribute should never raise exceptions
        test_paths = [
            "tags.Environment",
            "instance_type",
            "nonexistent",
            "",
            ".",
            "..",
            "tags.",
            ".Environment",
            "tags..Environment",
            "very.deep.nested.path.that.does.not.exist",
            "list[0].item",
            "list[999].item",
            "dict.missing.key",
        ]

        for path in test_paths:
            try:
                result = resource.get_attribute(path)
                assert result is None or isinstance(result, (str, int, float, bool, dict, list))
            except Exception as e:
                pytest.fail(f"get_attribute raised exception for path '{path}': {e}")

        # Property 2: has_attribute should be consistent with get_attribute
        for path in test_paths:
            has_attr = resource.has_attribute(path)
            get_attr = resource.get_attribute(path)

            if has_attr:
                assert (
                    get_attr is not None
                ), f"has_attribute returned True but get_attribute returned None for '{path}'"
            else:
                assert (
                    get_attr is None
                ), f"has_attribute returned False but get_attribute returned {get_attr} for '{path}'"

    @given(complex_rule_strategy())
    @settings(max_examples=100)
    def test_rule_immutability_property(self, rule):
        """Property: Rules should be immutable after creation."""
        original_id = rule.id
        original_type = rule.resource_type
        original_conditions = rule.conditions
        original_severity = rule.severity

        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            rule.id = "modified"  # type: ignore

        with pytest.raises(AttributeError):
            rule.resource_type = "modified"  # type: ignore

        with pytest.raises(AttributeError):
            rule.conditions = []  # type: ignore

        # Values should remain unchanged
        assert rule.id == original_id
        assert rule.resource_type == original_type
        assert rule.conditions == original_conditions
        assert rule.severity == original_severity

    @given(
        complex_rule_strategy(),
        st.lists(complex_terraform_resource_strategy(), min_size=1, max_size=10),
    )
    @settings(max_examples=50)
    def test_rule_resource_matching_consistency(self, rule, resources):
        """Property: Rule-resource matching should be deterministic."""
        # Multiple calls should return same result
        for resource in resources:
            result1 = rule.matches_resource_type(resource)
            result2 = rule.matches_resource_type(resource)
            result3 = rule.matches_resource_type(resource)

            assert (
                result1 == result2 == result3
            ), f"Inconsistent matching for rule {rule.id} and resource {resource.name}"

            # Universal rules should always match
            if rule.resource_type == "*":
                assert result1 is True, f"Universal rule {rule.id} should match all resources"

            # Specific rules should only match exact types
            elif rule.resource_type == resource.type:
                assert result1 is True, f"Rule {rule.id} should match resource type {resource.type}"

    @given(
        st.lists(complex_rule_condition_strategy(), min_size=1, max_size=5),
        complex_terraform_resource_strategy(),
    )
    @settings(max_examples=50)
    def test_rule_filter_properties(self, conditions, resource):
        """Property: Rule filters should behave consistently."""
        rule_filter = RuleFilter(conditions)

        # Property 1: Filter should be immutable
        original_conditions = rule_filter.conditions
        with pytest.raises(AttributeError):
            rule_filter.conditions = []  # type: ignore

        assert rule_filter.conditions == original_conditions

        # Property 2: Filter matching should be deterministic
        result1 = rule_filter.matches(resource)
        result2 = rule_filter.matches(resource)

        assert result1 == result2, "Filter matching should be deterministic"
        assert isinstance(result1, bool), "Filter matching should return boolean"

    @given(st.data())
    @settings(max_examples=30)
    def test_validation_summary_calculation_properties(self, data):
        """Property: Validation summary calculations should be mathematically correct."""
        # Generate rule results with known properties
        num_results = data.draw(st.integers(min_value=0, max_value=100))

        rule_results = []
        expected_passed = 0
        expected_failed = 0
        expected_errors = 0
        expected_warnings = 0
        expected_infos = 0

        for i in range(num_results):
            status = data.draw(st.booleans())
            severity = data.draw(st.sampled_from([Severity.ERROR, Severity.WARNING, Severity.INFO]))

            if status:
                expected_passed += 1
            else:
                expected_failed += 1

            if severity == Severity.ERROR:
                expected_errors += 1
            elif severity == Severity.WARNING:
                expected_warnings += 1
            else:
                expected_infos += 1

            rule_results.append(
                RuleResult(
                    rule_id=f"rule_{i}",
                    resource=TerraformResource("test_type", f"resource_{i}", {}),
                    status=status,
                    message="Test message",
                    severity=severity,
                    assertion_results=[],
                )
            )

        # Calculate summary
        summary = ValidationSummary(
            total_rules=data.draw(st.integers(min_value=1, max_value=50)),
            total_resources=data.draw(st.integers(min_value=1, max_value=50)),
            passed_rules=expected_passed,
            failed_rules=expected_failed,
            skipped_rules=0,
            total_assertions=num_results,
            passed_assertions=expected_passed,
            failed_assertions=expected_failed,
            execution_time=data.draw(
                st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
            ),
            error_count=expected_errors,
            warning_count=expected_warnings,
            info_count=expected_infos,
        )

        # Property: Counts should add up correctly
        assert (
            summary.passed_rules + summary.failed_rules + summary.skipped_rules
            <= summary.total_assertions
        )
        assert summary.error_count + summary.warning_count + summary.info_count == num_results

        # Property: Success rate should be mathematically correct
        if summary.total_assertions > 0:
            expected_success_rate = expected_passed / num_results
            assert abs(summary.assertion_success_rate - expected_success_rate) < 0.001
        else:
            assert summary.assertion_success_rate == 0.0

    @given(
        st.lists(complex_terraform_resource_strategy(), min_size=0, max_size=10),
        st.lists(complex_rule_strategy(), min_size=0, max_size=5),
        st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans()), max_size=5),
    )
    @settings(max_examples=30)
    def test_validation_context_properties(self, resources, rules, config):
        """Property: ValidationContext should preserve input data."""
        metadata = {"test": True, "timestamp": 12345}
        context = ValidationContext(resources, rules, config, metadata)

        # Property: All input data should be preserved
        assert context.resources == resources
        assert context.rules == rules
        assert context.config == config
        assert context.metadata == metadata

        # Property: Context should be immutable
        with pytest.raises(AttributeError):
            context.resources = []  # type: ignore

        # Property: Helper methods should work correctly
        if resources:
            resource_types = set(r.type for r in resources)
            for resource_type in resource_types:
                filtered_resources = context.get_resources_by_type(resource_type)
                assert all(r.type == resource_type for r in filtered_resources)

        if rules:
            rule_types = set(r.resource_type for r in rules if r.resource_type != "*")
            for rule_type in rule_types:
                applicable_rules = context.get_rules_for_resource_type(rule_type)
                # Should include specific rules for this type plus universal rules
                specific_rules = [r for r in rules if r.resource_type == rule_type]
                universal_rules = [r for r in rules if r.resource_type == "*"]
                expected_count = len(specific_rules) + len(universal_rules)
                assert len(applicable_rules) == expected_count


class TestValidationEdgeCases:
    """Property-based tests for edge cases and boundary conditions."""

    @given(st.text(max_size=1000))
    @settings(max_examples=100)
    def test_attribute_path_edge_cases(self, path):
        """Property: Attribute path handling should be robust for any string input."""
        resource = TerraformResource(
            "test_type",
            "test_name",
            {
                "simple": "value",
                "nested": {"deep": {"value": "found"}},
                "list": [{"item": "first"}, {"item": "second"}],
                "empty": {},
                "null": None,
                "number": 42,
                "boolean": True,
            },
        )

        # Should never raise exception
        try:
            result = resource.get_attribute(path)
            has_result = resource.has_attribute(path)

            # Results should be consistent
            if has_result:
                assert result is not None
            else:
                assert result is None

        except Exception as e:
            pytest.fail(f"Attribute access failed for path '{path}': {e}")

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.recursive(
                st.one_of(st.text(), st.integers(), st.booleans(), st.none()),
                lambda children: st.one_of(
                    st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=5),
                    st.lists(children, max_size=5),
                ),
                max_leaves=20,
            ),
            max_size=20,
        )
    )
    @settings(max_examples=50)
    def test_resource_with_arbitrary_attributes(self, attributes):
        """Property: Resources should handle arbitrary attribute structures."""
        resource = TerraformResource("test_type", "test_name", attributes)

        # Should be able to create resource
        assert resource.type == "test_type"
        assert resource.name == "test_name"
        assert resource.attributes == attributes

        # Should be able to serialize
        try:
            resource_dict = resource.to_dict()
            assert isinstance(resource_dict, dict)
            assert resource_dict["type"] == "test_type"
            assert resource_dict["name"] == "test_name"
            assert resource_dict["attributes"] == attributes
        except Exception as e:
            pytest.fail(f"Resource serialization failed: {e}")

    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=50),  # property_path
                st.sampled_from(["equals", "present", "regex", "gte"]),  # operator
                st.one_of(st.text(), st.integers(), st.none()),  # expected_value
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=30)
    def test_rule_with_arbitrary_conditions(self, condition_tuples):
        """Property: Rules should handle arbitrary condition combinations."""
        conditions = []
        for path, operator, expected in condition_tuples:
            # Adjust expected value based on operator
            if operator == "present":
                expected = None
            elif operator == "gte" and not isinstance(expected, (int, float)):
                expected = 0

            conditions.append(RuleCondition(path, operator, expected))

        try:
            rule = Rule(
                id="test-rule",
                resource_type="test_type",
                description="Test rule with arbitrary conditions",
                conditions=conditions,
            )

            # Should be able to create rule
            assert rule.id == "test-rule"
            assert len(rule.conditions) == len(conditions)

            # Should be able to serialize
            rule_dict = rule.to_dict()
            assert isinstance(rule_dict, dict)
            assert rule_dict["id"] == "test-rule"

        except Exception as e:
            pytest.fail(f"Rule creation failed with conditions {condition_tuples}: {e}")

    @given(
        st.integers(min_value=0, max_value=1000),
        st.integers(min_value=0, max_value=1000),
        st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_validation_summary_edge_cases(self, total_rules, total_resources, execution_time):
        """Property: ValidationSummary should handle edge cases gracefully."""
        # Generate valid counts
        passed_rules = min(total_rules, total_resources * total_rules)
        failed_rules = max(0, (total_resources * total_rules) - passed_rules)

        try:
            summary = ValidationSummary(
                total_rules=total_rules,
                total_resources=total_resources,
                passed_rules=passed_rules,
                failed_rules=failed_rules,
                skipped_rules=0,
                total_assertions=passed_rules + failed_rules,
                passed_assertions=passed_rules,
                failed_assertions=failed_rules,
                execution_time=execution_time,
                error_count=failed_rules,
                warning_count=0,
                info_count=passed_rules,
            )

            # Basic invariants
            assert summary.total_rules >= 0
            assert summary.total_resources >= 0
            assert summary.execution_time >= 0

            # Success rate should be between 0 and 1
            assert 0.0 <= summary.success_rate <= 1.0
            assert 0.0 <= summary.assertion_success_rate <= 1.0

            # Counts should be non-negative
            assert summary.passed_rules >= 0
            assert summary.failed_rules >= 0
            assert summary.error_count >= 0
            assert summary.warning_count >= 0
            assert summary.info_count >= 0

        except Exception as e:
            pytest.fail(f"ValidationSummary creation failed: {e}")

    @given(
        st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=50),
        st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=50),
    )
    @settings(max_examples=50)
    def test_rule_id_uniqueness_properties(self, rule_ids, resource_names):
        """Property: Rule and resource ID handling should be robust."""
        # Create rules with potentially duplicate IDs
        rules = []
        for i, rule_id in enumerate(rule_ids):
            try:
                rule = Rule(
                    id=rule_id,
                    resource_type="test_type",
                    description=f"Rule {i}",
                    conditions=[RuleCondition("test", "present", None)],
                )
                rules.append(rule)
            except Exception:
                # Skip invalid rule IDs
                continue

        # Create resources with potentially duplicate names
        resources = []
        for i, name in enumerate(resource_names):
            try:
                resource = TerraformResource("test_type", name, {"index": i})
                resources.append(resource)
            except Exception:
                # Skip invalid resource names
                continue

        # Should be able to work with the collections
        assert len(rules) <= len(rule_ids)
        assert len(resources) <= len(resource_names)

        # All rules should have valid IDs
        for rule in rules:
            assert isinstance(rule.id, str)
            assert len(rule.id) > 0

        # All resources should have valid names
        for resource in resources:
            assert isinstance(resource.name, str)
            assert len(resource.name) > 0
