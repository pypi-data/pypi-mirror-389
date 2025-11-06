"""Comprehensive output validation tests.

This module provides regression tests for all output formats to ensure
backward compatibility and validate that the modernized formatters
produce identical output to the legacy versions.
"""

import json
import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest

from riveter.models.core import Severity
from riveter.output.formatters import JSONFormatter, JUnitXMLFormatter, SARIFFormatter
from riveter.output.manager import ReportManager, _convert_legacy_results
from riveter.reporter import report_results
from riveter.rules import Rule
from riveter.scanner import ValidationResult


class TestOutputValidation:
    """Test output validation and backward compatibility."""

    def test_legacy_to_modern_conversion_empty(self):
        """Test conversion of empty legacy results to modern format."""
        legacy_results = []
        modern_result = _convert_legacy_results(legacy_results)

        assert modern_result.summary.total_rules == 0
        assert modern_result.summary.total_resources == 0
        assert modern_result.summary.passed == 0
        assert modern_result.summary.failed == 0
        assert len(modern_result.results) == 0
        assert modern_result.metadata["legacy_conversion"] is True

    def test_legacy_to_modern_conversion_with_results(self, sample_rules_list):
        """Test conversion of legacy results with actual data."""
        rule = sample_rules_list[0]

        # Create legacy results
        legacy_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
                execution_time=0.1,
            ),
            ValidationResult(
                rule=rule,
                resource={"id": "bad-instance", "resource_type": "aws_instance"},
                passed=False,
                message="Required tag missing",
                execution_time=0.2,
            ),
        ]

        # Convert to modern format
        modern_result = _convert_legacy_results(legacy_results)

        # Validate conversion
        assert modern_result.summary.total_results == 2
        assert modern_result.summary.passed == 1
        assert modern_result.summary.failed == 1
        assert len(modern_result.results) == 2

        # Check individual results
        passed_result = next(r for r in modern_result.results if r.passed)
        failed_result = next(r for r in modern_result.results if not r.passed)

        assert passed_result.rule_id == rule.id
        assert passed_result.resource.name == "test-instance"
        assert passed_result.message == "All checks passed"

        assert failed_result.rule_id == rule.id
        assert failed_result.resource.name == "bad-instance"
        assert failed_result.message == "Required tag missing"

    def test_legacy_to_modern_conversion_with_skipped(self, sample_rules_list):
        """Test conversion of legacy results with skipped entries."""
        rule = sample_rules_list[0]

        legacy_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
            ),
            ValidationResult(
                rule=rule,
                resource={"resource_type": rule.resource_type, "id": "N/A"},
                passed=False,
                message="SKIPPED: No matching resources found for this rule",
            ),
        ]

        modern_result = _convert_legacy_results(legacy_results)

        # Should have 2 results but only 1 counts toward pass/fail
        assert len(modern_result.results) == 2
        assert modern_result.summary.passed == 1
        assert modern_result.summary.failed == 0

        # Check skipped result details
        skipped_result = next(r for r in modern_result.results if r.message.startswith("SKIPPED:"))
        assert skipped_result.details["is_skipped"] is True

    def test_report_manager_format_registration(self):
        """Test that ReportManager properly registers and manages formatters."""
        manager = ReportManager()

        # Check default formatters are registered
        available_formats = manager.get_available_formats()
        expected_formats = ["table", "json", "junit", "sarif"]

        for fmt in expected_formats:
            assert fmt in available_formats

        # Test getting formatters
        json_formatter = manager.get_formatter("json")
        assert isinstance(json_formatter, JSONFormatter)

        junit_formatter = manager.get_formatter("junit")
        assert isinstance(junit_formatter, JUnitXMLFormatter)

        sarif_formatter = manager.get_formatter("sarif")
        assert isinstance(sarif_formatter, SARIFFormatter)

    def test_report_manager_invalid_format(self):
        """Test that ReportManager raises error for invalid formats."""
        manager = ReportManager()

        with pytest.raises(ValueError, match="Unsupported output format: invalid"):
            manager.get_formatter("invalid")

    def test_report_manager_custom_formatter_registration(self):
        """Test registering custom formatters."""
        manager = ReportManager()

        # Create a mock formatter
        class CustomFormatter:
            @property
            def format_name(self):
                return "custom"

            @property
            def file_extension(self):
                return ".custom"

            def format(self, result):
                return "custom output"

            def format_summary(self, result):
                return "custom summary"

        custom_formatter = CustomFormatter()
        manager.register_formatter("custom", custom_formatter)

        # Check it's registered
        assert "custom" in manager.get_available_formats()
        retrieved_formatter = manager.get_formatter("custom")
        assert retrieved_formatter is custom_formatter


class TestOutputFormatRegression:
    """Regression tests to ensure output format compatibility."""

    def test_json_format_structure_compatibility(self, sample_rules_list):
        """Test that JSON output maintains expected structure."""
        rule = sample_rules_list[0]

        legacy_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
                execution_time=0.1,
            ),
        ]

        # Test through the full pipeline
        with patch("builtins.print") as mock_print:
            exit_code = report_results(legacy_results, "json")

            assert exit_code == 0
            mock_print.assert_called_once()

            # Parse and validate JSON structure
            json_output = mock_print.call_args[0][0]
            data = json.loads(json_output)

            # Check required fields
            assert "timestamp" in data
            assert "summary" in data
            assert "results" in data

            # Check summary structure
            summary = data["summary"]
            required_summary_fields = ["total", "passed", "failed", "skipped", "active_checks"]
            for field in required_summary_fields:
                assert field in summary

            # Check results structure
            assert len(data["results"]) == 1
            result = data["results"][0]
            required_result_fields = [
                "rule_id",
                "resource_type",
                "resource_id",
                "passed",
                "severity",
                "message",
                "execution_time",
                "assertion_results",
            ]
            for field in required_result_fields:
                assert field in result

    def test_junit_xml_structure_compatibility(self, sample_rules_list):
        """Test that JUnit XML output maintains expected structure."""
        rule = sample_rules_list[0]

        legacy_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=False,
                message="Test failure",
                execution_time=0.1,
            ),
        ]

        with patch("builtins.print") as mock_print:
            exit_code = report_results(legacy_results, "junit")

            assert exit_code == 1  # Should fail due to failure
            mock_print.assert_called_once()

            # Parse and validate XML structure
            xml_output = mock_print.call_args[0][0]
            root = ET.fromstring(xml_output)

            # Check root element
            assert root.tag == "testsuite"

            # Check required attributes
            required_attrs = ["name", "tests", "failures", "skipped", "time", "timestamp"]
            for attr in required_attrs:
                assert attr in root.attrib

            # Check testcase structure
            testcases = root.findall("testcase")
            assert len(testcases) == 1

            testcase = testcases[0]
            required_testcase_attrs = ["classname", "name", "time"]
            for attr in required_testcase_attrs:
                assert attr in testcase.attrib

            # Check failure element
            failure = testcase.find("failure")
            assert failure is not None
            assert "message" in failure.attrib
            assert "type" in failure.attrib

    def test_sarif_structure_compatibility(self, sample_rules_list):
        """Test that SARIF output maintains expected structure."""
        rule = sample_rules_list[0]

        legacy_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=False,
                message="Security issue",
                execution_time=0.1,
            ),
        ]

        with patch("builtins.print") as mock_print:
            exit_code = report_results(legacy_results, "sarif")

            assert exit_code == 1  # Should fail due to failure
            mock_print.assert_called_once()

            # Parse and validate SARIF structure
            sarif_output = mock_print.call_args[0][0]
            data = json.loads(sarif_output)

            # Check SARIF root structure
            assert data["version"] == "2.1.0"
            assert "$schema" in data
            assert "runs" in data
            assert len(data["runs"]) == 1

            run = data["runs"][0]

            # Check tool structure
            assert "tool" in run
            tool = run["tool"]
            assert "driver" in tool
            driver = tool["driver"]

            required_driver_fields = [
                "name",
                "version",
                "informationUri",
                "shortDescription",
                "fullDescription",
                "rules",
            ]
            for field in required_driver_fields:
                assert field in driver

            # Check results structure (should have failed results)
            assert "results" in run
            assert len(run["results"]) == 1

            result = run["results"][0]
            required_result_fields = ["ruleId", "level", "message", "locations", "properties"]
            for field in required_result_fields:
                assert field in result

    def test_table_format_backward_compatibility(self, sample_rules_list):
        """Test that table format maintains backward compatibility."""
        rule = sample_rules_list[0]

        legacy_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
            ),
        ]

        # Test that table format uses console.print for backward compatibility
        with patch("riveter.reporter.console") as mock_console:
            exit_code = report_results(legacy_results, "table")

            assert exit_code == 0
            # Should have called console.print at least once (for table and summary)
            assert mock_console.print.call_count >= 1

    def test_output_format_case_insensitivity(self, sample_rules_list):
        """Test that output formats are case insensitive."""
        rule = sample_rules_list[0]

        legacy_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
            ),
        ]

        # Test various case combinations
        format_variations = [
            "JSON",
            "Json",
            "json",
            "JUNIT",
            "JUnit",
            "junit",
            "SARIF",
            "Sarif",
            "sarif",
        ]

        for fmt in format_variations:
            with patch("builtins.print"):
                exit_code = report_results(legacy_results, fmt)
                assert exit_code == 0  # Should not fail due to case sensitivity


class TestOutputValidationFramework:
    """Test the output validation framework itself."""

    def test_validation_result_conversion_preserves_data(self, sample_rules_list):
        """Test that conversion preserves all important data."""
        rule = sample_rules_list[0]

        # Create a comprehensive legacy result
        legacy_result = ValidationResult(
            rule=rule,
            resource={
                "id": "test-instance",
                "resource_type": "aws_instance",
                "tags": {"Environment": "test"},
                "instance_type": "t2.micro",
            },
            passed=False,
            message="Instance type not allowed",
            execution_time=0.15,
        )

        # Add assertion results if available
        if hasattr(legacy_result, "assertion_results"):
            legacy_result.assertion_results = []

        modern_result = _convert_legacy_results([legacy_result])

        # Validate all data is preserved
        assert len(modern_result.results) == 1
        converted = modern_result.results[0]

        assert converted.rule_id == rule.id
        assert converted.resource.name == "test-instance"
        assert converted.resource.type == "aws_instance"
        assert converted.resource.attributes["tags"]["Environment"] == "test"
        assert converted.resource.attributes["instance_type"] == "t2.micro"
        assert converted.passed is False
        assert converted.message == "Instance type not allowed"
        assert converted.details["execution_time"] == 0.15

    def test_error_handling_in_formatters(self):
        """Test that formatters handle edge cases gracefully."""
        import time

        from riveter.models.core import (
            RuleResult,
            TerraformResource,
            ValidationResult,
            ValidationSummary,
        )

        # Create a result with minimal data
        summary = ValidationSummary(
            total_rules=1,
            total_resources=1,
            passed=0,
            failed=1,
            errors=1,
            warnings=0,
            info=0,
            start_time=time.time(),
            end_time=time.time(),
        )

        resource = TerraformResource(type="unknown", name="unknown", attributes={})

        rule_result = RuleResult(
            rule_id="test-rule",
            resource=resource,
            passed=False,
            message="Test error",
            severity=Severity.ERROR,
        )

        modern_result = ValidationResult(summary=summary, results=[rule_result])

        # Test all formatters can handle this minimal data
        json_formatter = JSONFormatter()
        json_output = json_formatter.format(modern_result)
        assert json_output  # Should not be empty

        junit_formatter = JUnitXMLFormatter()
        junit_output = junit_formatter.format(modern_result)
        assert junit_output  # Should not be empty

        sarif_formatter = SARIFFormatter()
        sarif_output = sarif_formatter.format(modern_result)
        assert sarif_output  # Should not be empty

        # Validate outputs are valid
        json.loads(json_output)  # Should not raise
        ET.fromstring(junit_output)  # Should not raise
        json.loads(sarif_output)  # Should not raise
