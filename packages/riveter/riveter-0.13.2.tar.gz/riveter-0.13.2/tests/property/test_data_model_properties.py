"""Property-based tests for data model invariants using Hypothesis."""

from pathlib import Path
from typing import Any, Dict, List, Union

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from riveter.models.core import (
    AssertionResult,
    RuleResult,
    Severity,
    SourceLocation,
    TerraformResource,
    ValidationSummary,
)
from riveter.models.rules import Rule, RuleCondition, RuleFilter, RuleMetadata, RulePack


# Strategies for generating valid data model instances
@st.composite
def source_location_strategy(draw):
    """Generate valid SourceLocation instances."""
    file_path = draw(st.text(min_size=1, max_size=100).map(lambda x: Path(x)))
    line = draw(st.integers(min_value=1, max_value=10000))
    column = draw(st.integers(min_value=1, max_value=1000))

    return SourceLocation(file=file_path, line=line, column=column)


@st.composite
def assertion_result_strategy(draw):
    """Generate valid AssertionResult instances."""
    property_path = draw(st.text(min_size=1, max_size=100))
    operator = draw(st.sampled_from(["equals", "present", "regex", "gte", "lte", "contains"]))
    expected = draw(st.one_of(st.text(), st.integers(), st.booleans(), st.none()))
    actual = draw(st.one_of(st.text(), st.integers(), st.booleans(), st.none()))
    passed = draw(st.booleans())
    message = draw(st.text(max_size=200))

    return AssertionResult(
        property_path=property_path,
        operator=operator,
        expected=expected,
        actual=actual,
        passed=passed,
        message=message,
    )


@st.composite
def rule_result_strategy(draw):
    """Generate valid RuleResult instances."""
    rule_id = draw(st.text(min_size=1, max_size=100))
    resource = draw(terraform_resource_strategy())
    status = draw(st.booleans())
    message = draw(st.text(max_size=500))
    severity = draw(st.sampled_from([Severity.ERROR, Severity.WARNING, Severity.INFO]))
    assertion_results = draw(st.lists(assertion_result_strategy(), max_size=10))
    execution_time = draw(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )

    return RuleResult(
        rule_id=rule_id,
        resource=resource,
        status=status,
        message=message,
        severity=severity,
        assertion_results=assertion_results,
        execution_time=execution_time,
    )


@st.composite
def terraform_resource_strategy(draw):
    """Generate valid TerraformResource instances."""
    resource_type = draw(st.text(min_size=1, max_size=50))
    name = draw(st.text(min_size=1, max_size=50))

    # Generate nested attributes
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
                st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=10),
                st.lists(children, max_size=10),
            ),
            max_leaves=30,
        )
    )

    source_location = draw(st.one_of(st.none(), source_location_strategy()))

    return TerraformResource(
        type=resource_type, name=name, attributes=attributes, source_location=source_location
    )


@st.composite
def validation_summary_strategy(draw):
    """Generate valid ValidationSummary instances."""
    total_rules = draw(st.integers(min_value=0, max_value=1000))
    total_resources = draw(st.integers(min_value=0, max_value=1000))

    # Ensure counts are consistent
    max_evaluations = total_rules * total_resources
    passed_rules = draw(st.integers(min_value=0, max_value=max_evaluations))
    failed_rules = draw(st.integers(min_value=0, max_value=max_evaluations - passed_rules))
    skipped_rules = max(0, max_evaluations - passed_rules - failed_rules)

    total_assertions = passed_rules + failed_rules
    passed_assertions = draw(st.integers(min_value=0, max_value=total_assertions))
    failed_assertions = total_assertions - passed_assertions

    execution_time = draw(
        st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )

    error_count = draw(st.integers(min_value=0, max_value=failed_rules))
    warning_count = draw(st.integers(min_value=0, max_value=failed_rules - error_count))
    info_count = draw(st.integers(min_value=0, max_value=total_assertions))

    return ValidationSummary(
        total_rules=total_rules,
        total_resources=total_resources,
        passed_rules=passed_rules,
        failed_rules=failed_rules,
        skipped_rules=skipped_rules,
        total_assertions=total_assertions,
        passed_assertions=passed_assertions,
        failed_assertions=failed_assertions,
        execution_time=execution_time,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
    )


class TestDataModelImmutability:
    """Property-based tests for data model immutability."""

    @given(terraform_resource_strategy())
    @settings(max_examples=100)
    def test_terraform_resource_immutability(self, resource):
        """Property: TerraformResource instances should be immutable."""
        original_type = resource.type
        original_name = resource.name
        original_attributes = resource.attributes
        original_location = resource.source_location

        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            resource.type = "modified"  # type: ignore

        with pytest.raises(AttributeError):
            resource.name = "modified"  # type: ignore

        with pytest.raises(AttributeError):
            resource.attributes = {}  # type: ignore

        # Values should remain unchanged
        assert resource.type == original_type
        assert resource.name == original_name
        assert resource.attributes == original_attributes
        assert resource.source_location == original_location

    @given(source_location_strategy())
    @settings(max_examples=100)
    def test_source_location_immutability(self, location):
        """Property: SourceLocation instances should be immutable."""
        original_file = location.file
        original_line = location.line
        original_column = location.column

        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            location.file = Path("modified")  # type: ignore

        with pytest.raises(AttributeError):
            location.line = 999  # type: ignore

        with pytest.raises(AttributeError):
            location.column = 999  # type: ignore

        # Values should remain unchanged
        assert location.file == original_file
        assert location.line == original_line
        assert location.column == original_column

    @given(assertion_result_strategy())
    @settings(max_examples=100)
    def test_assertion_result_immutability(self, assertion_result):
        """Property: AssertionResult instances should be immutable."""
        original_path = assertion_result.property_path
        original_operator = assertion_result.operator
        original_expected = assertion_result.expected
        original_actual = assertion_result.actual
        original_passed = assertion_result.passed
        original_message = assertion_result.message

        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            assertion_result.property_path = "modified"  # type: ignore

        with pytest.raises(AttributeError):
            assertion_result.passed = not assertion_result.passed  # type: ignore

        # Values should remain unchanged
        assert assertion_result.property_path == original_path
        assert assertion_result.operator == original_operator
        assert assertion_result.expected == original_expected
        assert assertion_result.actual == original_actual
        assert assertion_result.passed == original_passed
        assert assertion_result.message == original_message

    @given(rule_result_strategy())
    @settings(max_examples=50)
    def test_rule_result_immutability(self, rule_result):
        """Property: RuleResult instances should be immutable."""
        original_rule_id = rule_result.rule_id
        original_resource = rule_result.resource
        original_status = rule_result.status
        original_message = rule_result.message
        original_severity = rule_result.severity

        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            rule_result.rule_id = "modified"  # type: ignore

        with pytest.raises(AttributeError):
            rule_result.status = not rule_result.status  # type: ignore

        # Values should remain unchanged
        assert rule_result.rule_id == original_rule_id
        assert rule_result.resource == original_resource
        assert rule_result.status == original_status
        assert rule_result.message == original_message
        assert rule_result.severity == original_severity

    @given(validation_summary_strategy())
    @settings(max_examples=100)
    def test_validation_summary_immutability(self, summary):
        """Property: ValidationSummary instances should be immutable."""
        original_total_rules = summary.total_rules
        original_total_resources = summary.total_resources
        original_passed_rules = summary.passed_rules
        original_execution_time = summary.execution_time

        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            summary.total_rules = 999  # type: ignore

        with pytest.raises(AttributeError):
            summary.passed_rules = 999  # type: ignore

        # Values should remain unchanged
        assert summary.total_rules == original_total_rules
        assert summary.total_resources == original_total_resources
        assert summary.passed_rules == original_passed_rules
        assert summary.execution_time == original_execution_time


class TestDataModelSerialization:
    """Property-based tests for data model serialization."""

    @given(terraform_resource_strategy())
    @settings(max_examples=100)
    def test_terraform_resource_serialization_roundtrip(self, resource):
        """Property: TerraformResource serialization should preserve data."""
        try:
            resource_dict = resource.to_dict()

            # Should be a dictionary
            assert isinstance(resource_dict, dict)

            # Should contain all essential fields
            assert resource_dict["type"] == resource.type
            assert resource_dict["name"] == resource.name
            assert resource_dict["attributes"] == resource.attributes

            # Source location handling
            if resource.source_location:
                assert "source_location" in resource_dict
                location_dict = resource_dict["source_location"]
                assert location_dict["file"] == str(resource.source_location.file)
                assert location_dict["line"] == resource.source_location.line
                assert location_dict["column"] == resource.source_location.column
            else:
                assert resource_dict.get("source_location") is None

        except Exception as e:
            pytest.fail(f"TerraformResource serialization failed: {e}")

    @given(assertion_result_strategy())
    @settings(max_examples=100)
    def test_assertion_result_serialization_roundtrip(self, assertion_result):
        """Property: AssertionResult serialization should preserve data."""
        try:
            result_dict = assertion_result.to_dict()

            # Should be a dictionary
            assert isinstance(result_dict, dict)

            # Should contain all fields
            assert result_dict["property_path"] == assertion_result.property_path
            assert result_dict["operator"] == assertion_result.operator
            assert result_dict["expected"] == assertion_result.expected
            assert result_dict["actual"] == assertion_result.actual
            assert result_dict["passed"] == assertion_result.passed
            assert result_dict["message"] == assertion_result.message

        except Exception as e:
            pytest.fail(f"AssertionResult serialization failed: {e}")

    @given(rule_result_strategy())
    @settings(max_examples=50)
    def test_rule_result_serialization_roundtrip(self, rule_result):
        """Property: RuleResult serialization should preserve data."""
        try:
            result_dict = rule_result.to_dict()

            # Should be a dictionary
            assert isinstance(result_dict, dict)

            # Should contain all essential fields
            assert result_dict["rule_id"] == rule_result.rule_id
            assert result_dict["resource_type"] == rule_result.resource.type
            assert result_dict["resource_name"] == rule_result.resource.name
            assert result_dict["status"] == rule_result.status
            assert result_dict["message"] == rule_result.message
            assert result_dict["severity"] == rule_result.severity.value

            # Should contain assertion results
            assert "assertion_results" in result_dict
            assert len(result_dict["assertion_results"]) == len(rule_result.assertion_results)

            # Execution time should be included if present
            if rule_result.execution_time is not None:
                assert result_dict["execution_time"] == rule_result.execution_time

        except Exception as e:
            pytest.fail(f"RuleResult serialization failed: {e}")

    @given(validation_summary_strategy())
    @settings(max_examples=100)
    def test_validation_summary_serialization_roundtrip(self, summary):
        """Property: ValidationSummary serialization should preserve data."""
        try:
            summary_dict = summary.to_dict()

            # Should be a dictionary
            assert isinstance(summary_dict, dict)

            # Should contain all fields
            assert summary_dict["total_rules"] == summary.total_rules
            assert summary_dict["total_resources"] == summary.total_resources
            assert summary_dict["passed_rules"] == summary.passed_rules
            assert summary_dict["failed_rules"] == summary.failed_rules
            assert summary_dict["execution_time"] == summary.execution_time

            # Should contain calculated fields
            assert "success_rate" in summary_dict
            assert "assertion_success_rate" in summary_dict

            # Success rates should be between 0 and 1
            assert 0.0 <= summary_dict["success_rate"] <= 1.0
            assert 0.0 <= summary_dict["assertion_success_rate"] <= 1.0

        except Exception as e:
            pytest.fail(f"ValidationSummary serialization failed: {e}")


class TestDataModelInvariants:
    """Property-based tests for data model invariants."""

    @given(validation_summary_strategy())
    @settings(max_examples=100)
    def test_validation_summary_mathematical_invariants(self, summary):
        """Property: ValidationSummary should maintain mathematical invariants."""
        # Non-negative counts
        assert summary.total_rules >= 0
        assert summary.total_resources >= 0
        assert summary.passed_rules >= 0
        assert summary.failed_rules >= 0
        assert summary.skipped_rules >= 0
        assert summary.total_assertions >= 0
        assert summary.passed_assertions >= 0
        assert summary.failed_assertions >= 0
        assert summary.error_count >= 0
        assert summary.warning_count >= 0
        assert summary.info_count >= 0

        # Execution time should be non-negative
        assert summary.execution_time >= 0

        # Assertion counts should add up
        assert summary.passed_assertions + summary.failed_assertions == summary.total_assertions

        # Success rates should be between 0 and 1
        assert 0.0 <= summary.success_rate <= 1.0
        assert 0.0 <= summary.assertion_success_rate <= 1.0

        # Success rate calculations should be correct
        if summary.total_assertions > 0:
            expected_assertion_success_rate = summary.passed_assertions / summary.total_assertions
            assert abs(summary.assertion_success_rate - expected_assertion_success_rate) < 0.001
        else:
            assert summary.assertion_success_rate == 0.0

    @given(terraform_resource_strategy())
    @settings(max_examples=100)
    def test_terraform_resource_attribute_access_invariants(self, resource):
        """Property: TerraformResource attribute access should maintain invariants."""
        # get_attribute should never raise exceptions
        test_paths = [
            "simple_key",
            "nested.key",
            "deep.nested.key",
            "list[0]",
            "list[0].item",
            "",
            ".",
            "..",
            "nonexistent",
            "null.key",
            "empty.key",
        ]

        for path in test_paths:
            try:
                result = resource.get_attribute(path)
                has_result = resource.has_attribute(path)

                # Consistency invariant
                if has_result:
                    assert (
                        result is not None
                    ), f"has_attribute returned True but get_attribute returned None for '{path}'"
                else:
                    assert (
                        result is None
                    ), f"has_attribute returned False but get_attribute returned {result} for '{path}'"

                # Type invariant
                if result is not None:
                    assert isinstance(result, (str, int, float, bool, dict, list, type(None)))

            except Exception as e:
                pytest.fail(f"Attribute access failed for path '{path}': {e}")

    @given(
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100),
        st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans()), max_size=20),
    )
    @settings(max_examples=100)
    def test_terraform_resource_creation_invariants(self, resource_type, name, attributes):
        """Property: TerraformResource creation should maintain invariants."""
        try:
            resource = TerraformResource(resource_type, name, attributes)

            # Identity invariants
            assert resource.type == resource_type
            assert resource.name == name
            assert resource.attributes == attributes

            # String representation should not crash
            str_repr = str(resource)
            assert isinstance(str_repr, str)
            assert len(str_repr) > 0

            # Equality invariants
            same_resource = TerraformResource(resource_type, name, attributes)
            assert resource == same_resource

            different_resource = TerraformResource(resource_type, name + "_different", attributes)
            assert resource != different_resource

        except Exception as e:
            pytest.fail(f"TerraformResource creation failed: {e}")

    @given(
        st.text(min_size=1, max_size=100),
        st.sampled_from(["equals", "present", "regex", "gte", "lte", "contains"]),
        st.one_of(st.text(), st.integers(), st.booleans(), st.none()),
    )
    @settings(max_examples=100)
    def test_assertion_result_logical_invariants(self, property_path, operator, expected_value):
        """Property: AssertionResult should maintain logical invariants."""
        actual_value = expected_value  # Make it pass
        passed = True
        message = "Test assertion"

        try:
            assertion = AssertionResult(
                property_path=property_path,
                operator=operator,
                expected=expected_value,
                actual=actual_value,
                passed=passed,
                message=message,
            )

            # Identity invariants
            assert assertion.property_path == property_path
            assert assertion.operator == operator
            assert assertion.expected == expected_value
            assert assertion.actual == actual_value
            assert assertion.passed == passed
            assert assertion.message == message

            # Logical invariants
            assert isinstance(assertion.passed, bool)
            assert isinstance(assertion.property_path, str)
            assert len(assertion.property_path) > 0
            assert isinstance(assertion.operator, str)
            assert len(assertion.operator) > 0

        except Exception as e:
            pytest.fail(f"AssertionResult creation failed: {e}")

    @given(st.sampled_from([Severity.ERROR, Severity.WARNING, Severity.INFO]))
    @settings(max_examples=10)
    def test_severity_enum_invariants(self, severity):
        """Property: Severity enum should maintain invariants."""
        # Should have string value
        assert isinstance(severity.value, str)
        assert len(severity.value) > 0

        # Should be comparable
        assert severity == severity
        assert severity <= severity
        assert severity >= severity

        # Should be serializable
        assert severity.value in ["error", "warning", "info"]

        # Should be reconstructible from string
        reconstructed = Severity(severity.value)
        assert reconstructed == severity

    @given(
        st.lists(assertion_result_strategy(), max_size=10),
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_rule_result_consistency_invariants(self, assertion_results, execution_time):
        """Property: RuleResult should maintain consistency invariants."""
        rule_id = "test-rule"
        resource = TerraformResource("test_type", "test_resource", {})
        status = all(ar.passed for ar in assertion_results) if assertion_results else True
        message = "Test message"
        severity = Severity.INFO

        try:
            rule_result = RuleResult(
                rule_id=rule_id,
                resource=resource,
                status=status,
                message=message,
                severity=severity,
                assertion_results=assertion_results,
                execution_time=execution_time,
            )

            # Identity invariants
            assert rule_result.rule_id == rule_id
            assert rule_result.resource == resource
            assert rule_result.status == status
            assert rule_result.message == message
            assert rule_result.severity == severity
            assert rule_result.assertion_results == assertion_results
            assert rule_result.execution_time == execution_time

            # Logical consistency invariants
            if assertion_results:
                # If all assertions pass, result should pass (unless overridden)
                all_assertions_pass = all(ar.passed for ar in assertion_results)
                if all_assertions_pass and status is False:
                    # This is allowed - rule can fail for other reasons
                    pass
                elif not all_assertions_pass and status is True:
                    # This should not happen - if any assertion fails, rule should fail
                    pytest.fail("Rule result shows success but has failing assertions")

            # Type invariants
            assert isinstance(rule_result.status, bool)
            assert isinstance(rule_result.rule_id, str)
            assert len(rule_result.rule_id) > 0
            assert isinstance(rule_result.message, str)
            assert isinstance(rule_result.assertion_results, list)
            assert rule_result.execution_time >= 0

        except Exception as e:
            pytest.fail(f"RuleResult creation failed: {e}")


class TestDataModelEdgeCases:
    """Property-based tests for edge cases in data models."""

    @given(
        st.text(max_size=0),  # Empty string
        st.text(max_size=10000),  # Very long string
        st.dictionaries(
            st.text(),
            st.recursive(
                st.one_of(st.text(), st.integers(), st.booleans(), st.none()),
                lambda x: st.dictionaries(st.text(), x, max_size=3),
                max_leaves=100,
            ),
            max_size=50,
        ),  # Very nested dictionary
    )
    @settings(max_examples=30)
    def test_terraform_resource_edge_cases(self, resource_type, name, attributes):
        """Property: TerraformResource should handle edge cases gracefully."""
        # Skip empty resource type (invalid)
        assume(len(resource_type) > 0)
        assume(len(name) > 0)

        try:
            resource = TerraformResource(resource_type, name, attributes)

            # Should handle serialization of complex nested data
            resource_dict = resource.to_dict()
            assert isinstance(resource_dict, dict)

            # Should handle attribute access on complex data
            for key in list(attributes.keys())[:5]:  # Test first 5 keys
                result = resource.get_attribute(key)
                # Should not crash

        except Exception as e:
            pytest.fail(f"TerraformResource edge case failed: {e}")

    @given(
        st.integers(min_value=0, max_value=0),  # Zero values
        st.integers(min_value=1000000, max_value=2000000),  # Very large values
        st.floats(min_value=0.0, max_value=0.0),  # Zero float
        st.floats(
            min_value=1000000.0, max_value=2000000.0, allow_nan=False, allow_infinity=False
        ),  # Large float
    )
    @settings(max_examples=20)
    def test_validation_summary_edge_values(self, zero_int, large_int, zero_float, large_float):
        """Property: ValidationSummary should handle edge values gracefully."""
        try:
            # Test with zero values
            zero_summary = ValidationSummary(
                total_rules=zero_int,
                total_resources=zero_int,
                passed_rules=zero_int,
                failed_rules=zero_int,
                skipped_rules=zero_int,
                total_assertions=zero_int,
                passed_assertions=zero_int,
                failed_assertions=zero_int,
                execution_time=zero_float,
                error_count=zero_int,
                warning_count=zero_int,
                info_count=zero_int,
            )

            assert zero_summary.success_rate == 0.0
            assert zero_summary.assertion_success_rate == 0.0

            # Test with large values
            large_summary = ValidationSummary(
                total_rules=large_int,
                total_resources=large_int,
                passed_rules=large_int,
                failed_rules=0,
                skipped_rules=0,
                total_assertions=large_int,
                passed_assertions=large_int,
                failed_assertions=0,
                execution_time=large_float,
                error_count=0,
                warning_count=0,
                info_count=large_int,
            )

            assert large_summary.success_rate == 1.0
            assert large_summary.assertion_success_rate == 1.0

        except Exception as e:
            pytest.fail(f"ValidationSummary edge case failed: {e}")

    @given(
        st.text(max_size=10000),  # Very long strings
        st.one_of(
            st.text(max_size=10000),
            st.integers(min_value=-1000000, max_value=1000000),
            st.floats(
                min_value=-1000000.0, max_value=1000000.0, allow_nan=False, allow_infinity=False
            ),
            st.none(),
        ),
    )
    @settings(max_examples=30)
    def test_assertion_result_edge_cases(self, long_string, extreme_value):
        """Property: AssertionResult should handle edge cases gracefully."""
        try:
            assertion = AssertionResult(
                property_path=long_string[:100] if long_string else "test",  # Limit path length
                operator="equals",
                expected=extreme_value,
                actual=extreme_value,
                passed=True,
                message=long_string,
            )

            # Should handle serialization
            assertion_dict = assertion.to_dict()
            assert isinstance(assertion_dict, dict)

            # Should handle string representation
            str_repr = str(assertion)
            assert isinstance(str_repr, str)

        except Exception as e:
            pytest.fail(f"AssertionResult edge case failed: {e}")
