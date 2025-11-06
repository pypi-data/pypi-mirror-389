"""Unit tests for core data models."""

from pathlib import Path
from typing import Any

import pytest

from riveter.models.core import (
    RuleResult,
    Severity,
    SourceLocation,
    TerraformResource,
    ValidationResult,
    ValidationSummary,
)


class TestSeverity:
    """Test cases for the Severity enum."""

    def test_severity_values(self):
        """Test that severity enum has correct values."""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_severity_ordering(self):
        """Test that severity levels have correct ordering."""
        assert Severity.ERROR > Severity.WARNING
        assert Severity.WARNING > Severity.INFO
        assert Severity.INFO < Severity.WARNING

    def test_severity_from_string(self):
        """Test creating severity from string values."""
        assert Severity("error") == Severity.ERROR
        assert Severity("warning") == Severity.WARNING
        assert Severity("info") == Severity.INFO

    def test_severity_invalid_value(self):
        """Test that invalid severity values raise ValueError."""
        with pytest.raises(ValueError):
            Severity("invalid")


class TestSourceLocation:
    """Test cases for the SourceLocation data class."""

    def test_source_location_creation(self):
        """Test creating a SourceLocation instance."""
        location = SourceLocation(file=Path("main.tf"), line=10, column=5)

        assert location.file == Path("main.tf")
        assert location.line == 10
        assert location.column == 5

    def test_source_location_immutable(self):
        """Test that SourceLocation is immutable."""
        location = SourceLocation(file=Path("main.tf"), line=10, column=5)

        with pytest.raises(AttributeError):
            location.line = 20  # type: ignore

    def test_source_location_equality(self):
        """Test SourceLocation equality comparison."""
        location1 = SourceLocation(Path("main.tf"), 10, 5)
        location2 = SourceLocation(Path("main.tf"), 10, 5)
        location3 = SourceLocation(Path("main.tf"), 10, 6)

        assert location1 == location2
        assert location1 != location3

    def test_source_location_str_representation(self):
        """Test string representation of SourceLocation."""
        location = SourceLocation(Path("main.tf"), 10, 5)
        str_repr = str(location)

        assert "main.tf" in str_repr
        assert "10" in str_repr
        assert "5" in str_repr


class TestTerraformResource:
    """Test cases for the TerraformResource data class."""

    def test_terraform_resource_creation(self):
        """Test creating a TerraformResource instance."""
        resource = TerraformResource(
            type="aws_instance",
            name="web_server",
            attributes={"instance_type": "t3.micro", "ami": "ami-12345"},
            source_location=SourceLocation(Path("main.tf"), 5, 1),
        )

        assert resource.type == "aws_instance"
        assert resource.name == "web_server"
        assert resource.attributes["instance_type"] == "t3.micro"
        assert resource.source_location.line == 5

    def test_terraform_resource_without_location(self):
        """Test creating TerraformResource without source location."""
        resource = TerraformResource(
            type="aws_s3_bucket", name="data_bucket", attributes={"bucket": "my-bucket"}
        )

        assert resource.type == "aws_s3_bucket"
        assert resource.name == "data_bucket"
        assert resource.source_location is None

    def test_terraform_resource_immutable(self):
        """Test that TerraformResource is immutable."""
        resource = TerraformResource(
            type="aws_instance", name="web_server", attributes={"instance_type": "t3.micro"}
        )

        with pytest.raises(AttributeError):
            resource.type = "aws_s3_bucket"  # type: ignore

    def test_terraform_resource_equality(self):
        """Test TerraformResource equality comparison."""
        resource1 = TerraformResource("aws_instance", "web1", {"type": "t3.micro"})
        resource2 = TerraformResource("aws_instance", "web1", {"type": "t3.micro"})
        resource3 = TerraformResource("aws_instance", "web2", {"type": "t3.micro"})

        assert resource1 == resource2
        assert resource1 != resource3

    def test_terraform_resource_get_attribute(self):
        """Test getting attributes from TerraformResource."""
        resource = TerraformResource(
            type="aws_instance",
            name="web_server",
            attributes={
                "instance_type": "t3.micro",
                "tags": {"Environment": "production"},
                "root_block_device": {"volume_size": 20},
            },
        )

        # Test direct attribute access
        assert resource.get_attribute("instance_type") == "t3.micro"

        # Test missing attribute
        assert resource.get_attribute("missing_attr") is None
        assert resource.get_attribute("missing_attr", "default") == "default"

    def test_terraform_resource_has_attribute(self):
        """Test checking if TerraformResource has attributes."""
        resource = TerraformResource(
            type="aws_instance",
            name="web_server",
            attributes={"instance_type": "t3.micro", "tags": {"Environment": "production"}},
        )

        assert resource.has_attribute("instance_type") is True
        assert resource.has_attribute("missing_attr") is False

    def test_terraform_resource_tags(self):
        """Test tag-related methods."""
        resource = TerraformResource(
            type="aws_instance",
            name="web_server",
            attributes={
                "instance_type": "t3.micro",
                "tags": {"Environment": "production", "Name": "web-server"},
            },
        )

        assert resource.has_tag("Environment") is True
        assert resource.has_tag("Missing") is False
        assert resource.get_tag("Environment") == "production"
        assert resource.get_tag("Missing", "default") == "default"


class TestRuleResult:
    """Test cases for the RuleResult data class."""

    def test_rule_result_creation(self):
        """Test creating a RuleResult instance."""
        resource = TerraformResource("aws_instance", "web", {"instance_type": "t3.micro"})

        result = RuleResult(
            rule_id="test-rule-001",
            resource=resource,
            passed=True,
            message="All checks passed",
            severity=Severity.INFO,
        )

        assert result.rule_id == "test-rule-001"
        assert result.resource == resource
        assert result.passed is True
        assert result.severity == Severity.INFO
        assert result.status == "PASS"

    def test_rule_result_failed(self):
        """Test RuleResult for failed validation."""
        resource = TerraformResource("aws_instance", "web", {"instance_type": "t3.large"})

        result = RuleResult(
            rule_id="test-rule-001",
            resource=resource,
            passed=False,
            message="Validation failed",
            severity=Severity.ERROR,
        )

        assert result.passed is False
        assert result.severity == Severity.ERROR
        assert result.status == "FAIL"

    def test_rule_result_immutable(self):
        """Test that RuleResult is immutable."""
        resource = TerraformResource("aws_instance", "web", {"instance_type": "t3.micro"})
        result = RuleResult("rule-1", resource, True, "OK", Severity.INFO)

        with pytest.raises(AttributeError):
            result.passed = False  # type: ignore

    def test_rule_result_to_dict(self):
        """Test converting RuleResult to dictionary."""
        resource = TerraformResource("aws_instance", "web", {"instance_type": "t3.micro"})

        result = RuleResult(
            rule_id="test-rule-001",
            resource=resource,
            passed=True,
            message="All checks passed",
            severity=Severity.INFO,
        )

        result_dict = result.to_dict()

        assert result_dict["rule_id"] == "test-rule-001"
        assert result_dict["resource_type"] == "aws_instance"
        assert result_dict["resource_name"] == "web"
        assert result_dict["passed"] is True
        assert result_dict["severity"] == "info"
        assert result_dict["status"] == "PASS"


class TestValidationSummary:
    """Test cases for the ValidationSummary data class."""

    def test_validation_summary_creation(self):
        """Test creating a ValidationSummary instance."""
        summary = ValidationSummary(
            total_rules=10, total_resources=5, passed=8, failed=2, errors=2, warnings=3, info=5
        )

        assert summary.total_rules == 10
        assert summary.total_resources == 5
        assert summary.passed == 8
        assert summary.failed == 2
        assert summary.errors == 2

    def test_validation_summary_success_rate(self):
        """Test calculating success rate from ValidationSummary."""
        summary = ValidationSummary(
            total_rules=10, total_resources=5, passed=8, failed=2, errors=2, warnings=0, info=8
        )

        assert summary.success_rate == 80.0  # (8/10) * 100
        assert summary.total_results == 10

    def test_validation_summary_zero_division(self):
        """Test ValidationSummary handles zero division gracefully."""
        summary = ValidationSummary(
            total_rules=0, total_resources=0, passed=0, failed=0, errors=0, warnings=0, info=0
        )

        assert summary.success_rate == 100.0  # No failures = 100% success
        assert summary.total_results == 0

    def test_validation_summary_immutable(self):
        """Test that ValidationSummary is immutable."""
        summary = ValidationSummary(
            total_rules=10, total_resources=5, passed=8, failed=2, errors=2, warnings=0, info=8
        )

        with pytest.raises(AttributeError):
            summary.total_rules = 15  # type: ignore

    def test_validation_summary_to_dict(self):
        """Test converting ValidationSummary to dictionary."""
        summary = ValidationSummary(
            total_rules=10, total_resources=5, passed=8, failed=2, errors=2, warnings=0, info=8
        )

        summary_dict = summary.to_dict()

        assert summary_dict["total_rules"] == 10
        assert summary_dict["success_rate"] == 80.0
        assert "errors" in summary_dict
        assert "warnings" in summary_dict
        assert "info" in summary_dict


class TestPropertyBasedModels:
    """Property-based tests for data models using hypothesis."""

    @pytest.mark.parametrize("severity", [Severity.ERROR, Severity.WARNING, Severity.INFO])
    def test_severity_roundtrip(self, severity):
        """Test that severity values can be converted to string and back."""
        severity_str = severity.value
        reconstructed = Severity(severity_str)
        assert reconstructed == severity

    def test_terraform_resource_attribute_access_edge_cases(self):
        """Test edge cases in TerraformResource attribute access."""
        resource = TerraformResource(
            type="aws_instance",
            name="test",
            attributes={
                "nested": {"deep": {"value": "found"}},
                "list": [{"item": "first"}, {"item": "second"}],
                "empty_dict": {},
                "empty_list": [],
                "null_value": None,
            },
        )

        # Test deep nesting
        assert resource.get_attribute("nested.deep.value") == "found"

        # Test list access
        assert resource.get_attribute("list[0].item") == "first"
        assert resource.get_attribute("list[1].item") == "second"

        # Test empty containers
        assert resource.get_attribute("empty_dict") == {}
        assert resource.get_attribute("empty_list") == []

        # Test null values
        assert resource.get_attribute("null_value") is None

        # Test invalid paths
        assert resource.get_attribute("nested.missing.value") is None
        assert resource.get_attribute("list[10].item") is None
        assert resource.get_attribute("") is None

    def test_assertion_result_edge_cases(self):
        """Test AssertionResult with edge case values."""
        # Test with None values
        result = AssertionResult(
            property_path="test",
            operator="present",
            expected=None,
            actual=None,
            passed=True,
            message="",
        )

        assert result.expected is None
        assert result.actual is None

        # Test with complex objects
        complex_expected = {"nested": {"list": [1, 2, 3]}}
        complex_actual = {"nested": {"list": [1, 2, 4]}}

        result = AssertionResult(
            property_path="complex.nested.list",
            operator="equals",
            expected=complex_expected,
            actual=complex_actual,
            passed=False,
            message="Complex object mismatch",
        )

        assert result.expected == complex_expected
        assert result.actual == complex_actual

    def test_rule_result_with_no_assertions(self):
        """Test RuleResult with empty assertion results."""
        resource = TerraformResource("aws_instance", "test", {})

        result = RuleResult(
            rule_id="empty-rule",
            resource=resource,
            status=True,
            message="No assertions to check",
            severity=Severity.INFO,
            assertion_results=[],
        )

        assert len(result.assertion_results) == 0
        assert result.status is True

        result_dict = result.to_dict()
        assert result_dict["assertion_results"] == []

    def test_validation_summary_edge_cases(self):
        """Test ValidationSummary with edge case values."""
        # Test with all zeros
        summary = ValidationSummary(
            total_rules=0,
            total_resources=0,
            passed_rules=0,
            failed_rules=0,
            skipped_rules=0,
            total_assertions=0,
            passed_assertions=0,
            failed_assertions=0,
            execution_time=0.0,
            error_count=0,
            warning_count=0,
            info_count=0,
        )

        assert summary.success_rate == 0.0
        assert summary.assertion_success_rate == 0.0

        # Test with only skipped rules
        summary = ValidationSummary(
            total_rules=5,
            total_resources=0,
            passed_rules=0,
            failed_rules=0,
            skipped_rules=5,
            total_assertions=0,
            passed_assertions=0,
            failed_assertions=0,
            execution_time=0.1,
            error_count=0,
            warning_count=0,
            info_count=0,
        )

        assert summary.success_rate == 0.0  # No passed rules
        assert summary.total_rules == 5
        assert summary.skipped_rules == 5
