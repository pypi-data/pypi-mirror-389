"""Property-based tests for rule validation using Hypothesis."""

from pathlib import Path
from typing import Any, Dict, List

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from riveter.models.core import Severity, TerraformResource
from riveter.models.rules import Rule, RuleCondition, RuleFilter
from riveter.validation.evaluator import RuleEvaluator


# Hypothesis strategies for generating test data
@st.composite
def terraform_resource_strategy(draw):
    """Generate valid TerraformResource instances."""
    resource_types = st.sampled_from(
        [
            "aws_instance",
            "aws_s3_bucket",
            "aws_rds_instance",
            "google_compute_instance",
            "azurerm_virtual_machine",
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

    # Generate realistic attributes based on resource type
    if resource_type == "aws_instance":
        attributes = {
            "instance_type": draw(
                st.sampled_from(["t3.micro", "t3.small", "t3.medium", "m5.large"])
            ),
            "ami": draw(st.text(min_size=12, max_size=12, alphabet="ami-0123456789abcdef")),
            "tags": draw(
                st.dictionaries(
                    st.text(min_size=1, max_size=20),
                    st.text(min_size=1, max_size=50),
                    min_size=0,
                    max_size=5,
                )
            ),
        }
    elif resource_type == "aws_s3_bucket":
        attributes = {
            "bucket": draw(
                st.text(
                    min_size=3,
                    max_size=63,
                    alphabet=st.characters(whitelist_categories=("Ll", "Nd", "-")),
                )
            ),
            "tags": draw(
                st.dictionaries(
                    st.text(min_size=1, max_size=20),
                    st.text(min_size=1, max_size=50),
                    min_size=0,
                    max_size=5,
                )
            ),
        }
    else:
        attributes = draw(
            st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.one_of(st.text(), st.integers(), st.booleans()),
                min_size=0,
                max_size=10,
            )
        )

    return TerraformResource(type=resource_type, name=name, attributes=attributes)


@st.composite
def rule_condition_strategy(draw):
    """Generate valid RuleCondition instances."""
    property_paths = st.sampled_from(
        [
            "tags.Environment",
            "tags.CostCenter",
            "instance_type",
            "ami",
            "bucket",
            "security_groups",
            "root_block_device.volume_size",
        ]
    )

    operators = st.sampled_from(
        ["equals", "present", "regex", "gte", "lte", "gt", "lt", "contains", "length"]
    )

    property_path = draw(property_paths)
    operator = draw(operators)

    # Generate appropriate expected values based on operator
    if operator == "present":
        expected_value = None
    elif operator in ["equals", "contains"]:
        expected_value = draw(st.text(min_size=1, max_size=50))
    elif operator in ["gte", "lte", "gt", "lt"]:
        expected_value = draw(st.integers(min_value=1, max_value=1000))
    elif operator == "regex":
        # Generate simple regex patterns
        patterns = [r"^t3\.", r"^ami-[0-9a-f]+$", r"production|staging|development", r"\d+"]
        expected_value = draw(st.sampled_from(patterns))
    elif operator == "length":
        expected_value = {"gte": draw(st.integers(min_value=0, max_value=10))}
    else:
        expected_value = draw(st.text())

    return RuleCondition(
        property_path=property_path, operator=operator, expected_value=expected_value
    )


@st.composite
def rule_strategy(draw):
    """Generate valid Rule instances."""
    rule_id = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "-", "_")),
        )
    )
    resource_type = draw(st.sampled_from(["aws_instance", "aws_s3_bucket", "*"]))
    description = draw(st.text(min_size=1, max_size=200))
    severity = draw(st.sampled_from([Severity.ERROR, Severity.WARNING, Severity.INFO]))

    conditions = draw(st.lists(rule_condition_strategy(), min_size=1, max_size=5))

    return Rule(
        id=rule_id,
        resource_type=resource_type,
        description=description,
        conditions=conditions,
        severity=severity,
    )


class TestRuleValidationProperties:
    """Property-based tests for rule validation logic."""

    @given(terraform_resource_strategy())
    def test_resource_attribute_access_is_consistent(self, resource):
        """Test that resource attribute access is consistent and safe."""
        # Property: Getting an attribute should always return the same value
        for _ in range(3):  # Test multiple times
            value1 = resource.get_attribute("tags.Environment")
            value2 = resource.get_attribute("tags.Environment")
            assert value1 == value2

        # Property: has_attribute should be consistent with get_attribute
        for attr_path in ["tags.Environment", "instance_type", "nonexistent.path"]:
            has_attr = resource.has_attribute(attr_path)
            get_attr = resource.get_attribute(attr_path)

            if has_attr:
                assert get_attr is not None
            else:
                assert get_attr is None

    @given(terraform_resource_strategy(), st.text())
    def test_resource_get_attribute_never_raises(self, resource, attribute_path):
        """Test that get_attribute never raises exceptions for any input."""
        # Property: get_attribute should never raise exceptions
        try:
            result = resource.get_attribute(attribute_path)
            # Result should be None or a valid value
            assert result is None or isinstance(result, (str, int, float, bool, dict, list))
        except Exception as e:
            pytest.fail(f"get_attribute raised exception for path '{attribute_path}': {e}")

    @given(rule_condition_strategy())
    def test_rule_condition_immutability(self, condition):
        """Test that RuleCondition instances are immutable."""
        original_path = condition.property_path
        original_operator = condition.operator
        original_expected = condition.expected_value

        # Property: Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            condition.property_path = "modified"  # type: ignore

        # Property: Values should remain unchanged
        assert condition.property_path == original_path
        assert condition.operator == original_operator
        assert condition.expected_value == original_expected

    @given(rule_strategy())
    def test_rule_immutability(self, rule):
        """Test that Rule instances are immutable."""
        original_id = rule.id
        original_type = rule.resource_type
        original_conditions = rule.conditions

        # Property: Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            rule.id = "modified"  # type: ignore

        # Property: Values should remain unchanged
        assert rule.id == original_id
        assert rule.resource_type == original_type
        assert rule.conditions == original_conditions

    @given(rule_strategy(), terraform_resource_strategy())
    def test_rule_resource_type_matching(self, rule, resource):
        """Test rule resource type matching logic."""
        matches = rule.matches_resource_type(resource)

        # Property: Universal rules (*) should match all resources
        if rule.resource_type == "*":
            assert matches is True

        # Property: Specific rules should only match exact resource types
        elif rule.resource_type == resource.type:
            assert matches is True
        else:
            assert matches is False

    @given(st.lists(rule_strategy(), min_size=1, max_size=10), terraform_resource_strategy())
    def test_rule_application_consistency(self, rules, resource):
        """Test that rule application is consistent across multiple evaluations."""
        # Property: Rule application should be deterministic
        for rule in rules:
            result1 = rule.applies_to_resource(resource)
            result2 = rule.applies_to_resource(resource)
            result3 = rule.applies_to_resource(resource)

            assert result1 == result2 == result3

    @given(terraform_resource_strategy())
    def test_resource_serialization_roundtrip(self, resource):
        """Test that resource serialization preserves data."""
        # Property: Serialization should be reversible
        resource_dict = resource.to_dict()

        # Check that all essential data is preserved
        assert resource_dict["type"] == resource.type
        assert resource_dict["name"] == resource.name
        assert resource_dict["attributes"] == resource.attributes

    @given(rule_condition_strategy())
    def test_rule_condition_serialization_roundtrip(self, condition):
        """Test that rule condition serialization preserves data."""
        # Property: Serialization should preserve all data
        condition_dict = condition.to_dict()

        assert condition_dict["property_path"] == condition.property_path
        assert condition_dict["operator"] == condition.operator
        assert condition_dict["expected_value"] == condition.expected_value

    @given(st.lists(terraform_resource_strategy(), min_size=0, max_size=20))
    def test_resource_list_operations(self, resources):
        """Test operations on lists of resources."""
        # Property: Grouping by type should preserve all resources
        type_groups = {}
        for resource in resources:
            if resource.type not in type_groups:
                type_groups[resource.type] = []
            type_groups[resource.type].append(resource)

        total_grouped = sum(len(group) for group in type_groups.values())
        assert total_grouped == len(resources)

        # Property: All resources should have valid types
        for resource in resources:
            assert isinstance(resource.type, str)
            assert len(resource.type) > 0

    @given(st.lists(rule_strategy(), min_size=0, max_size=20))
    def test_rule_list_operations(self, rules):
        """Test operations on lists of rules."""
        # Property: Filtering by resource type should not lose rules
        for resource_type in ["aws_instance", "aws_s3_bucket", "*"]:
            filtered_rules = [
                r for r in rules if r.resource_type == resource_type or r.resource_type == "*"
            ]

            # All filtered rules should match the criteria
            for rule in filtered_rules:
                assert rule.resource_type == resource_type or rule.resource_type == "*"

        # Property: All rules should have unique IDs within the list
        rule_ids = [rule.id for rule in rules]
        # Note: We don't enforce uniqueness in generation, but we can test the property
        if len(set(rule_ids)) == len(rule_ids):
            # If IDs are unique, grouping by ID should preserve count
            id_groups = {}
            for rule in rules:
                if rule.id not in id_groups:
                    id_groups[rule.id] = []
                id_groups[rule.id].append(rule)

            total_grouped = sum(len(group) for group in id_groups.values())
            assert total_grouped == len(rules)

    @settings(max_examples=50)  # Reduce examples for complex tests
    @given(
        st.lists(rule_strategy(), min_size=1, max_size=5),
        st.lists(terraform_resource_strategy(), min_size=1, max_size=5),
    )
    def test_validation_result_properties(self, rules, resources):
        """Test properties of validation results."""
        # This would test actual validation logic if we had a complete evaluator
        # For now, we test the structure and consistency

        # Property: Each rule should be evaluated against applicable resources
        applicable_pairs = []
        for rule in rules:
            for resource in resources:
                if rule.matches_resource_type(resource):
                    applicable_pairs.append((rule, resource))

        # Property: Number of applicable pairs should be deterministic
        count1 = len(applicable_pairs)

        # Recalculate to ensure consistency
        applicable_pairs2 = []
        for rule in rules:
            for resource in resources:
                if rule.matches_resource_type(resource):
                    applicable_pairs2.append((rule, resource))

        count2 = len(applicable_pairs2)
        assert count1 == count2

    @given(terraform_resource_strategy())
    def test_resource_attribute_path_parsing(self, resource):
        """Test that attribute path parsing handles various formats."""
        # Property: Simple paths should work
        simple_paths = ["tags", "instance_type", "ami"]
        for path in simple_paths:
            result = resource.get_attribute(path)
            # Should not raise exception
            assert result is None or isinstance(result, (str, int, float, bool, dict, list))

        # Property: Nested paths should work
        nested_paths = ["tags.Environment", "root_block_device.volume_size", "metadata.labels.app"]
        for path in nested_paths:
            result = resource.get_attribute(path)
            # Should not raise exception
            assert result is None or isinstance(result, (str, int, float, bool, dict, list))

        # Property: Invalid paths should return None
        invalid_paths = ["", ".", "..", "tags.", ".Environment", "tags..Environment"]
        for path in invalid_paths:
            result = resource.get_attribute(path)
            assert result is None

    @given(rule_condition_strategy(), terraform_resource_strategy())
    def test_condition_evaluation_consistency(self, condition, resource):
        """Test that condition evaluation is consistent."""
        # This would test actual condition evaluation logic
        # For now, we test that the condition structure is valid

        # Property: Condition should have valid operator
        valid_operators = [
            "equals",
            "present",
            "regex",
            "gte",
            "lte",
            "gt",
            "lt",
            "contains",
            "length",
        ]
        assert condition.operator in valid_operators

        # Property: Property path should be non-empty string
        assert isinstance(condition.property_path, str)
        assert len(condition.property_path) > 0

        # Property: Expected value should be appropriate for operator
        if condition.operator == "present":
            assert condition.expected_value is None
        elif condition.operator in ["gte", "lte", "gt", "lt"]:
            assert isinstance(condition.expected_value, (int, float, dict))
        elif condition.operator == "regex":
            assert isinstance(condition.expected_value, str)

    @given(st.lists(rule_condition_strategy(), min_size=1, max_size=10))
    def test_rule_filter_logic(self, conditions):
        """Test rule filter logic properties."""
        rule_filter = RuleFilter(conditions)

        # Property: Filter should contain all conditions
        assert len(rule_filter.conditions) == len(conditions)

        # Property: Filter should be immutable
        with pytest.raises(AttributeError):
            rule_filter.conditions = []  # type: ignore

        # Property: All conditions should be preserved
        for i, condition in enumerate(conditions):
            assert rule_filter.conditions[i] == condition


class TestRuleValidationEdgeCases:
    """Property-based tests for edge cases in rule validation."""

    @given(st.text(max_size=1000))
    def test_attribute_path_edge_cases(self, path):
        """Test attribute path handling with various edge cases."""
        resource = TerraformResource(
            "test_type",
            "test_name",
            {
                "simple": "value",
                "nested": {"deep": {"value": "found"}},
                "list": [{"item": "first"}, {"item": "second"}],
                "empty": {},
                "null": None,
            },
        )

        # Property: Should never raise exception
        try:
            result = resource.get_attribute(path)
            assert result is None or isinstance(result, (str, int, float, bool, dict, list))
        except Exception as e:
            pytest.fail(f"get_attribute raised exception for path '{path}': {e}")

    @given(
        st.dictionaries(
            st.text(), st.one_of(st.text(), st.integers(), st.booleans(), st.none()), max_size=20
        )
    )
    def test_resource_with_various_attribute_types(self, attributes):
        """Test resources with various attribute types."""
        resource = TerraformResource("test_type", "test_name", attributes)

        # Property: Resource should be created successfully
        assert resource.type == "test_type"
        assert resource.name == "test_name"
        assert resource.attributes == attributes

        # Property: All attribute keys should be accessible
        for key in attributes.keys():
            result = resource.get_attribute(key)
            assert result == attributes[key]

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
    def test_rule_with_many_conditions(self, property_paths):
        """Test rules with many conditions."""
        assume(len(set(property_paths)) == len(property_paths))  # Unique paths

        conditions = [RuleCondition(path, "present", None) for path in property_paths]

        rule = Rule(
            id="multi-condition-rule",
            resource_type="test_type",
            description="Rule with many conditions",
            conditions=conditions,
        )

        # Property: All conditions should be preserved
        assert len(rule.conditions) == len(conditions)

        # Property: Rule should be valid
        assert rule.id == "multi-condition-rule"
        assert rule.resource_type == "test_type"

    @given(st.integers(min_value=-1000, max_value=1000))
    def test_numeric_condition_values(self, numeric_value):
        """Test rule conditions with various numeric values."""
        condition = RuleCondition(
            property_path="numeric_field", operator="gte", expected_value=numeric_value
        )

        # Property: Condition should be created successfully
        assert condition.expected_value == numeric_value
        assert condition.operator == "gte"

        # Property: Condition should be serializable
        condition_dict = condition.to_dict()
        assert condition_dict["expected_value"] == numeric_value
