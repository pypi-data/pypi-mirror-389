"""Backward compatibility validation for output formats.

This module provides comprehensive tests to ensure that the modernized
output system produces identical results to the legacy system.
"""

import json
import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest

from riveter.formatters import JSONFormatter as LegacyJSONFormatter
from riveter.formatters import JUnitXMLFormatter as LegacyJUnitXMLFormatter
from riveter.formatters import SARIFFormatter as LegacySARIFFormatter
from riveter.output.formatters import JSONFormatter, JUnitXMLFormatter, SARIFFormatter
from riveter.output.manager import _convert_legacy_results
from riveter.reporter import report_results
from riveter.rules import Rule
from riveter.scanner import ValidationResult


class TestBackwardCompatibilityOutput:
    """Test backward compatibility of output formats."""

    def test_json_formatter_compatibility(self, sample_rules_list):
        """Test that new JSON formatter produces compatible output with legacy."""
        rule = sample_rules_list[0]

        # Create test data
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

        # Test legacy formatter
        legacy_formatter = LegacyJSONFormatter()
        legacy_output = legacy_formatter.format(legacy_results)
        legacy_data = json.loads(legacy_output)

        # Test modern formatter through conversion
        modern_result = _convert_legacy_results(legacy_results)
        modern_formatter = JSONFormatter()
        modern_output = modern_formatter.format(modern_result)
        modern_data = json.loads(modern_output)

        # Compare structure and key fields
        assert "timestamp" in legacy_data
        assert "timestamp" in modern_data
        assert "summary" in legacy_data
        assert "summary" in modern_data
        assert "results" in legacy_data
        assert "results" in modern_data

        # Compare summary structure
        legacy_summary = legacy_data["summary"]
        modern_summary = modern_data["summary"]

        # Key fields should match
        assert legacy_summary["total"] == modern_summary["total"]
        assert legacy_summary["passed"] == modern_summary["passed"]
        assert legacy_summary["failed"] == modern_summary["failed"]
        assert legacy_summary["active_checks"] == modern_summary["active_checks"]

        # Results should have same count
        assert len(legacy_data["results"]) == len(modern_data["results"])

    def test_junit_formatter_compatibility(self, sample_rules_list):
        """Test that new JUnit formatter produces compatible output with legacy."""
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

        # Test legacy formatter
        legacy_formatter = LegacyJUnitXMLFormatter()
        legacy_output = legacy_formatter.format(legacy_results)
        legacy_root = ET.fromstring(legacy_output)

        # Test modern formatter
        modern_result = _convert_legacy_results(legacy_results)
        modern_formatter = JUnitXMLFormatter()
        modern_output = modern_formatter.format(modern_result)
        modern_root = ET.fromstring(modern_output)

        # Compare XML structure
        assert legacy_root.tag == modern_root.tag == "testsuite"

        # Compare key attributes
        assert legacy_root.get("name") == modern_root.get("name")
        assert legacy_root.get("tests") == modern_root.get("tests")
        assert legacy_root.get("failures") == modern_root.get("failures")

        # Compare testcase count
        legacy_testcases = legacy_root.findall("testcase")
        modern_testcases = modern_root.findall("testcase")
        assert len(legacy_testcases) == len(modern_testcases)

    def test_sarif_formatter_compatibility(self, sample_rules_list):
        """Test that new SARIF formatter produces compatible output with legacy."""
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

        # Test legacy formatter
        legacy_formatter = LegacySARIFFormatter()
        legacy_output = legacy_formatter.format(legacy_results)
        legacy_data = json.loads(legacy_output)

        # Test modern formatter
        modern_result = _convert_legacy_results(legacy_results)
        modern_formatter = SARIFFormatter()
        modern_output = modern_formatter.format(modern_result)
        modern_data = json.loads(modern_output)

        # Compare SARIF structure
        assert legacy_data["version"] == modern_data["version"]
        assert legacy_data["$schema"] == modern_data["$schema"]

        # Compare runs structure
        assert len(legacy_data["runs"]) == len(modern_data["runs"])

        legacy_run = legacy_data["runs"][0]
        modern_run = modern_data["runs"][0]

        # Compare tool information
        assert legacy_run["tool"]["driver"]["name"] == modern_run["tool"]["driver"]["name"]

        # Compare results count (should both have failed results)
        assert len(legacy_run["results"]) == len(modern_run["results"])

    def test_end_to_end_output_compatibility(self, sample_rules_list):
        """Test end-to-end output compatibility through report_results function."""
        rule = sample_rules_list[0]

        test_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
            ),
        ]

        # Test all formats through the main interface
        formats_to_test = ["json", "junit", "sarif"]

        for fmt in formats_to_test:
            with patch("builtins.print") as mock_print:
                exit_code = report_results(test_results, fmt)

                # Should succeed
                assert exit_code == 0
                mock_print.assert_called_once()

                # Output should be valid for the format
                output = mock_print.call_args[0][0]

                if fmt == "json":
                    # Should be valid JSON
                    data = json.loads(output)
                    assert "summary" in data
                    assert "results" in data
                elif fmt == "junit":
                    # Should be valid XML
                    root = ET.fromstring(output)
                    assert root.tag == "testsuite"
                elif fmt == "sarif":
                    # Should be valid SARIF JSON
                    data = json.loads(output)
                    assert data["version"] == "2.1.0"
                    assert "runs" in data

    def test_empty_results_compatibility(self):
        """Test that empty results are handled consistently."""
        empty_results = []

        # Test table format (should use console.print)
        with patch("riveter.reporter.console") as mock_console:
            exit_code = report_results(empty_results, "table")
            assert exit_code == 0
            mock_console.print.assert_called_once_with("[green]All rules passed![/green]")

        # Test other formats
        for fmt in ["json", "junit", "sarif"]:
            with patch("builtins.print") as mock_print:
                exit_code = report_results(empty_results, fmt)
                assert exit_code == 0
                mock_print.assert_called_once()

                output = mock_print.call_args[0][0]

                if fmt == "json":
                    data = json.loads(output)
                    assert data["summary"]["total"] == 0
                elif fmt == "junit":
                    root = ET.fromstring(output)
                    assert root.get("tests") == "0"
                elif fmt == "sarif":
                    data = json.loads(output)
                    assert len(data["runs"][0]["results"]) == 0

    def test_mixed_results_compatibility(self, sample_rules_list):
        """Test compatibility with mixed passing, failing, and skipped results."""
        rule = sample_rules_list[0]

        mixed_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "good-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
            ),
            ValidationResult(
                rule=rule,
                resource={"id": "bad-instance", "resource_type": "aws_instance"},
                passed=False,
                message="Required tag missing",
            ),
            ValidationResult(
                rule=rule,
                resource={"resource_type": rule.resource_type, "id": "N/A"},
                passed=False,
                message="SKIPPED: No matching resources found for this rule",
            ),
        ]

        # Test JSON format
        with patch("builtins.print") as mock_print:
            exit_code = report_results(mixed_results, "json")

            # Should fail due to failed result
            assert exit_code == 1

            output = mock_print.call_args[0][0]
            data = json.loads(output)

            # Validate summary counts
            summary = data["summary"]
            assert summary["total"] == 3
            assert summary["passed"] == 1
            assert summary["failed"] == 1
            assert summary["skipped"] == 1
            assert summary["active_checks"] == 2  # Total minus skipped

    def test_output_format_error_handling(self):
        """Test that invalid output formats are handled properly."""
        test_results = []

        # Test invalid format through report_results
        # The modern system handles errors gracefully and returns exit code 1
        with patch("builtins.print"):
            exit_code = report_results(test_results, "invalid_format")
            # Should return error exit code
            assert exit_code == 1


class TestOutputValidationFrameworkIntegration:
    """Test integration of the output validation framework."""

    def test_validation_framework_catches_format_changes(self, sample_rules_list):
        """Test that the validation framework would catch format changes."""
        rule = sample_rules_list[0]

        test_results = [
            ValidationResult(
                rule=rule,
                resource={"id": "test-instance", "resource_type": "aws_instance"},
                passed=True,
                message="All checks passed",
                execution_time=0.1,
            ),
        ]

        # Test that we can validate the structure of each format
        formats_to_validate = ["json", "junit", "sarif"]

        for fmt in formats_to_validate:
            with patch("builtins.print") as mock_print:
                exit_code = report_results(test_results, fmt)
                assert exit_code == 0

                output = mock_print.call_args[0][0]

                # Validate that output has expected structure
                if fmt == "json":
                    data = json.loads(output)
                    # These fields must exist for compatibility
                    required_fields = ["timestamp", "summary", "results"]
                    for field in required_fields:
                        assert field in data, f"Missing required field '{field}' in JSON output"

                    # Summary must have these fields
                    summary_fields = ["total", "passed", "failed", "skipped", "active_checks"]
                    for field in summary_fields:
                        assert field in data["summary"], f"Missing summary field '{field}'"

                elif fmt == "junit":
                    root = ET.fromstring(output)
                    # Required attributes for JUnit compatibility
                    required_attrs = ["name", "tests", "failures", "skipped", "time", "timestamp"]
                    for attr in required_attrs:
                        assert (
                            attr in root.attrib
                        ), f"Missing required attribute '{attr}' in JUnit XML"

                elif fmt == "sarif":
                    data = json.loads(output)
                    # Required SARIF structure
                    assert data["version"] == "2.1.0", "SARIF version must be 2.1.0"
                    assert "$schema" in data, "SARIF must have $schema field"
                    assert "runs" in data, "SARIF must have runs field"
                    assert len(data["runs"]) > 0, "SARIF must have at least one run"

    def test_performance_regression_detection(self, sample_rules_list):
        """Test that performance characteristics are maintained."""
        import time

        rule = sample_rules_list[0]

        # Create a larger set of results to test performance
        large_results = []
        for i in range(100):
            large_results.append(
                ValidationResult(
                    rule=rule,
                    resource={"id": f"instance-{i}", "resource_type": "aws_instance"},
                    passed=i % 2 == 0,  # Alternate pass/fail
                    message=f"Test result {i}",
                    execution_time=0.001,
                )
            )

        # Test that formatting doesn't take too long
        for fmt in ["json", "junit", "sarif"]:
            start_time = time.time()

            with patch("builtins.print"):
                exit_code = report_results(large_results, fmt)

            end_time = time.time()
            duration = end_time - start_time

            # Should complete within reasonable time (adjust threshold as needed)
            assert duration < 1.0, f"Format '{fmt}' took too long: {duration:.3f}s"
            assert exit_code == 1  # Should fail due to failed results
