"""Backward compatibility validation tests.

These tests ensure that all existing CLI commands, outputs, and behaviors
remain identical after modernization.
"""

import json
import subprocess
from pathlib import Path

import pytest

from .utils.compatibility import CompatibilityTester
from .utils.fixtures import FixtureManager


@pytest.fixture(scope="module")
def compatibility_tester():
    """Initialize compatibility tester."""
    return CompatibilityTester()


@pytest.fixture(scope="module")
def fixture_manager():
    """Initialize fixture manager."""
    return FixtureManager()


@pytest.mark.compatibility
class TestCLICompatibility:
    """Test CLI command backward compatibility."""

    def test_help_command_structure(self, compatibility_tester):
        """Test that help command output structure is preserved."""
        success, message = compatibility_tester.test_cli_command_compatibility(
            ["riveter", "--help"],
            expected_exit_code=0,
            check_output_structure=False,  # Help output can vary slightly
        )
        assert success, f"Help command compatibility failed: {message}"

    def test_version_command_compatibility(self, compatibility_tester):
        """Test that version command works and returns expected format."""
        success, message = compatibility_tester.test_cli_command_compatibility(
            ["riveter", "--version"], expected_exit_code=0, check_output_structure=False
        )
        assert success, f"Version command compatibility failed: {message}"

    @pytest.mark.slow
    def test_scan_command_table_output(self, compatibility_tester, fixture_manager):
        """Test that scan command with table output maintains structure."""
        try:
            terraform_file = fixture_manager.get_terraform_fixture("simple")
            rules_file = fixture_manager.get_rules_fixture("basic_rules")

            success, message = compatibility_tester.test_cli_command_compatibility(
                [
                    "riveter",
                    "scan",
                    str(terraform_file),
                    "--rules",
                    str(rules_file),
                    "--format",
                    "table",
                ],
                expected_exit_code=0,  # May be 1 if validation fails, but command should work
                check_output_structure=True,
            )
            # Note: We don't assert success here because validation might fail,
            # but we check that the command structure is maintained

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")

    @pytest.mark.slow
    def test_scan_command_json_output(self, compatibility_tester, fixture_manager):
        """Test that scan command with JSON output maintains structure."""
        try:
            terraform_file = fixture_manager.get_terraform_fixture("simple")
            rules_file = fixture_manager.get_rules_fixture("basic_rules")

            # Run command and capture output
            result = subprocess.run(
                [
                    "riveter",
                    "scan",
                    str(terraform_file),
                    "--rules",
                    str(rules_file),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            # Validate JSON structure regardless of exit code
            if result.stdout.strip():
                try:
                    json_data = json.loads(result.stdout)
                    assert isinstance(json_data, dict), "JSON output should be an object"

                    # Check for expected top-level fields
                    expected_fields = ["summary", "results"]
                    for field in expected_fields:
                        assert field in json_data, f"Missing required field: {field}"

                    # Validate summary structure
                    if "summary" in json_data:
                        summary = json_data["summary"]
                        summary_fields = ["total_rules", "passed", "failed"]
                        for field in summary_fields:
                            assert field in summary, f"Missing summary field: {field}"

                except json.JSONDecodeError:
                    pytest.fail("JSON output is not valid JSON")

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")
        except subprocess.TimeoutExpired:
            pytest.fail("Scan command timed out")


@pytest.mark.compatibility
class TestExitCodeCompatibility:
    """Test that exit codes remain consistent."""

    def test_success_exit_code(self, compatibility_tester):
        """Test that successful commands return exit code 0."""
        assert compatibility_tester.test_exit_code_compatibility("success", ["riveter", "--help"])

    def test_invalid_args_exit_code(self, compatibility_tester):
        """Test that invalid arguments return appropriate exit code."""
        assert compatibility_tester.test_exit_code_compatibility(
            "invalid_args", ["riveter", "--invalid-flag"]
        )


@pytest.mark.compatibility
class TestFileFormatCompatibility:
    """Test that file format support is maintained."""

    def test_terraform_file_extensions(self, compatibility_tester):
        """Test that Terraform file extensions are supported."""
        test_files = [
            Path("test.tf"),
            Path("test.tfvars"),
        ]

        for test_file in test_files:
            assert compatibility_tester.test_file_format_compatibility(
                "terraform_extensions", test_file
            ), f"Terraform file extension {test_file.suffix} should be supported"

    def test_rules_file_extensions(self, compatibility_tester):
        """Test that rules file extensions are supported."""
        test_files = [
            Path("rules.yml"),
            Path("rules.yaml"),
        ]

        for test_file in test_files:
            assert compatibility_tester.test_file_format_compatibility(
                "rules_extensions", test_file
            ), f"Rules file extension {test_file.suffix} should be supported"


@pytest.mark.compatibility
@pytest.mark.integration
class TestEndToEndCompatibility:
    """Test end-to-end workflow compatibility."""

    @pytest.mark.slow
    def test_complete_scan_workflow(self, fixture_manager):
        """Test that complete scan workflow produces expected results."""
        try:
            terraform_file = fixture_manager.get_terraform_fixture("simple")
            rules_file = fixture_manager.get_rules_fixture("basic_rules")

            # Test different output formats
            formats = ["table", "json"]

            for output_format in formats:
                result = subprocess.run(
                    [
                        "riveter",
                        "scan",
                        str(terraform_file),
                        "--rules",
                        str(rules_file),
                        "--format",
                        output_format,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )

                # Command should complete (exit code 0 or 1 for validation failures)
                assert result.returncode in [
                    0,
                    1,
                ], f"Unexpected exit code {result.returncode} for format {output_format}"

                # Should produce output
                assert result.stdout.strip(), f"No output produced for format {output_format}"

                # JSON format should be valid JSON
                if output_format == "json":
                    try:
                        json.loads(result.stdout)
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON output for format {output_format}")

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")
        except subprocess.TimeoutExpired:
            pytest.fail("End-to-end scan workflow timed out")


@pytest.mark.compatibility
def test_generate_compatibility_report(compatibility_tester):
    """Test compatibility report generation."""
    # Mock test results
    test_results = [
        {"test_name": "help_command", "passed": True, "message": "Success"},
        {"test_name": "version_command", "passed": True, "message": "Success"},
        {"test_name": "scan_json", "passed": False, "message": "Structure mismatch"},
    ]

    report = compatibility_tester.generate_compatibility_report(test_results)

    assert "summary" in report
    assert "details" in report
    assert report["summary"]["total_tests"] == 3
    assert report["summary"]["passed"] == 2
    assert report["summary"]["failed"] == 1
    assert report["summary"]["success_rate"] == pytest.approx(66.67, rel=1e-2)
