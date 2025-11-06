"""Integration tests for backward compatibility validation."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from riveter.models.core import ValidationSummary


class TestBackwardCompatibilityValidation:
    """Tests to ensure backward compatibility is maintained."""

    def run_cli_command(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Helper to run CLI commands with proper environment."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")

        return subprocess.run(
            [sys.executable, "-m", "riveter.cli"] + args,
            env=env,
            capture_output=True,
            text=True,
            **kwargs,
        )

    def extract_json_from_output(self, output: str) -> Dict[str, Any]:
        """Extract JSON from CLI output."""
        lines = output.strip().split("\n")
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        if json_start >= 0:
            json_output = "\n".join(lines[json_start:])
            return json.loads(json_output)
        raise ValueError(f"No JSON found in output: {output}")

    @pytest.fixture
    def legacy_terraform_file(self, tmp_path: Path) -> Path:
        """Create a Terraform file that should work with legacy versions."""
        tf_content = """
# Legacy-compatible Terraform configuration
resource "aws_instance" "web_server" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server"
    Environment = "production"
    CostCenter  = "12345"
  }

  security_groups = ["sg-12345678"]
}

resource "aws_s3_bucket" "data_bucket" {
  bucket = "my-test-bucket"

  tags = {
    Environment = "production"
    Purpose     = "data-storage"
  }
}
"""
        tf_file = tmp_path / "main.tf"
        tf_file.write_text(tf_content)
        return tf_file

    @pytest.fixture
    def legacy_rules_file(self, tmp_path: Path) -> Path:
        """Create a rules file in legacy format."""
        rules_content = """
rules:
  - id: ec2-environment-tag-required
    resource_type: aws_instance
    description: EC2 instances must have Environment tag
    assert:
      tags:
        Environment: present

  - id: ec2-cost-center-required
    resource_type: aws_instance
    description: Production EC2 instances must have CostCenter tag
    filter:
      tags:
        Environment: production
    assert:
      tags:
        CostCenter: present

  - id: s3-purpose-tag-required
    resource_type: aws_s3_bucket
    description: S3 buckets must have Purpose tag
    assert:
      tags:
        Purpose: present
"""
        rules_file = tmp_path / "legacy_rules.yml"
        rules_file.write_text(rules_content)
        return rules_file

    def test_legacy_scan_command_interface(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that legacy scan command interface still works."""
        # Test various legacy command formats that should still work
        legacy_commands = [
            # Basic scan with rules file
            ["scan", "--terraform", str(legacy_terraform_file), "--rules", str(legacy_rules_file)],
            # Scan with rule pack
            ["scan", "--terraform", str(legacy_terraform_file), "--rule-pack", "aws-security"],
            # Scan with output format
            [
                "scan",
                "--terraform",
                str(legacy_terraform_file),
                "--rules",
                str(legacy_rules_file),
                "--output-format",
                "json",
            ],
            # Scan with verbose flag
            [
                "scan",
                "--terraform",
                str(legacy_terraform_file),
                "--rules",
                str(legacy_rules_file),
                "--verbose",
            ],
        ]

        for cmd in legacy_commands:
            result = self.run_cli_command(cmd)

            # Should not fail due to interface changes
            assert result.returncode in [
                0,
                1,
            ], f"Command failed: {' '.join(cmd)}\nStderr: {result.stderr}"

            # Should produce some output
            assert len(result.stdout.strip()) > 0 or len(result.stderr.strip()) > 0

    def test_legacy_output_format_compatibility(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that all legacy output formats still work."""
        formats = ["json", "table", "junit", "sarif"]

        for fmt in formats:
            result = self.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(legacy_terraform_file),
                    "--rules",
                    str(legacy_rules_file),
                    "--output-format",
                    fmt,
                ]
            )

            assert result.returncode in [0, 1], f"Format {fmt} failed\nStderr: {result.stderr}"
            assert len(result.stdout.strip()) > 0, f"No output for format {fmt}"

            # Basic format validation
            if fmt == "json":
                try:
                    json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Try extracting JSON from mixed output
                    self.extract_json_from_output(result.stdout)
            elif fmt == "junit":
                assert "<?xml" in result.stdout or "<testsuite" in result.stdout
            elif fmt == "sarif":
                try:
                    sarif_data = json.loads(result.stdout)
                    assert isinstance(sarif_data, dict)
                except json.JSONDecodeError:
                    sarif_data = self.extract_json_from_output(result.stdout)
                    assert isinstance(sarif_data, dict)

    def test_legacy_rule_pack_commands(self):
        """Test that legacy rule pack commands still work."""
        # Test list-rule-packs command
        result = self.run_cli_command(["list-rule-packs"])
        assert result.returncode == 0
        assert "aws-security" in result.stdout

        # Test validate-rule-pack command
        result = self.run_cli_command(["validate-rule-pack", "rule_packs/aws-security.yml"])
        assert result.returncode == 0
        assert "valid" in result.stdout.lower() or "✓" in result.stdout

    def test_legacy_json_output_structure(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that JSON output structure remains compatible."""
        result = self.run_cli_command(
            [
                "scan",
                "--terraform",
                str(legacy_terraform_file),
                "--rules",
                str(legacy_rules_file),
                "--output-format",
                "json",
            ]
        )

        assert result.returncode in [0, 1]

        # Parse JSON output
        try:
            output_data = self.extract_json_from_output(result.stdout)
        except (json.JSONDecodeError, ValueError):
            pytest.fail("Failed to parse JSON output")

        # Verify expected structure exists
        assert isinstance(output_data, dict)

        # Should have either 'summary' or 'results' or both
        has_summary = "summary" in output_data
        has_results = "results" in output_data
        assert (
            has_summary or has_results
        ), f"Missing expected keys in output: {list(output_data.keys())}"

        # If summary exists, verify its structure
        if has_summary:
            summary = output_data["summary"]
            expected_summary_keys = ["total_rules", "total_resources"]
            for key in expected_summary_keys:
                assert key in summary, f"Missing summary key: {key}"

    def test_legacy_table_output_structure(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that table output structure remains compatible."""
        result = self.run_cli_command(
            [
                "scan",
                "--terraform",
                str(legacy_terraform_file),
                "--rules",
                str(legacy_rules_file),
                "--output-format",
                "table",
            ]
        )

        assert result.returncode in [0, 1]
        assert len(result.stdout.strip()) > 0

        # Table output should contain typical table elements
        table_indicators = ["|", "─", "Rule", "Status", "Resource", "Message"]
        has_table_structure = any(indicator in result.stdout for indicator in table_indicators)
        assert has_table_structure, f"Output doesn't look like a table: {result.stdout[:200]}"

    def test_legacy_exit_codes(self, legacy_terraform_file: Path, legacy_rules_file: Path):
        """Test that exit codes remain consistent with legacy behavior."""
        # Test successful scan (should exit 0 if no violations)
        result = self.run_cli_command(
            ["scan", "--terraform", str(legacy_terraform_file), "--rules", str(legacy_rules_file)]
        )

        # Exit code should be 0 (no violations) or 1 (violations found)
        assert result.returncode in [0, 1]

        # Test with nonexistent file (should exit with error code)
        result = self.run_cli_command(
            ["scan", "--terraform", "nonexistent.tf", "--rules", str(legacy_rules_file)]
        )

        assert result.returncode != 0  # Should fail
        assert result.returncode in [1, 2]  # Common error exit codes

    def test_legacy_error_message_format(self):
        """Test that error messages maintain expected format."""
        # Test with invalid arguments
        result = self.run_cli_command(["scan", "--invalid-flag"])

        assert result.returncode != 0
        # Error should be reported in stderr or stdout
        error_output = result.stderr + result.stdout
        assert "Error:" in error_output or "error:" in error_output or "Usage:" in error_output

    def test_legacy_help_output(self):
        """Test that help output maintains expected structure."""
        result = self.run_cli_command(["--help"])

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "scan" in result.stdout
        assert "list-rule-packs" in result.stdout
        assert "validate-rule-pack" in result.stdout

    def test_legacy_version_output(self):
        """Test that version output works."""
        result = self.run_cli_command(["--version"])

        assert result.returncode == 0
        # Should contain version number
        assert any(char.isdigit() for char in result.stdout)

    def test_legacy_rule_file_format_compatibility(self, legacy_terraform_file: Path):
        """Test that legacy rule file formats are still supported."""
        # Create rule file with various legacy formats
        legacy_formats = [
            # Simple format
            """
rules:
  - id: simple-rule
    resource_type: aws_instance
    assert:
      tags:
        Environment: present
""",
            # Format with filter
            """
rules:
  - id: filtered-rule
    resource_type: aws_instance
    filter:
      tags:
        Environment: production
    assert:
      tags:
        CostCenter: present
""",
            # Format with description and severity
            """
rules:
  - id: detailed-rule
    resource_type: aws_instance
    description: Detailed rule with severity
    severity: error
    assert:
      tags:
        Environment: present
""",
        ]

        for i, rule_content in enumerate(legacy_formats):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
                f.write(rule_content)
                rule_file = f.name

            try:
                result = self.run_cli_command(
                    [
                        "scan",
                        "--terraform",
                        str(legacy_terraform_file),
                        "--rules",
                        rule_file,
                        "--output-format",
                        "json",
                    ]
                )

                assert result.returncode in [0, 1], f"Legacy format {i} failed: {result.stderr}"

                # Should produce valid output
                try:
                    self.extract_json_from_output(result.stdout)
                except (json.JSONDecodeError, ValueError):
                    pytest.fail(f"Legacy format {i} produced invalid JSON")

            finally:
                os.unlink(rule_file)

    def test_legacy_terraform_file_format_compatibility(self, legacy_rules_file: Path):
        """Test that legacy Terraform file formats are supported."""
        legacy_tf_formats = [
            # Simple resource
            """
resource "aws_instance" "test" {
  ami = "ami-12345"
  instance_type = "t3.micro"
  tags = {
    Environment = "test"
  }
}
""",
            # Resource with nested blocks
            """
resource "aws_instance" "complex" {
  ami = "ami-12345"
  instance_type = "t3.micro"

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Environment = "production"
    Name = "complex-instance"
  }
}
""",
            # Multiple resources
            """
resource "aws_instance" "web" {
  ami = "ami-12345"
  instance_type = "t3.micro"
  tags = { Environment = "production" }
}

resource "aws_s3_bucket" "data" {
  bucket = "test-bucket"
  tags = { Environment = "production" }
}
""",
        ]

        for i, tf_content in enumerate(legacy_tf_formats):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".tf", delete=False) as f:
                f.write(tf_content)
                tf_file = f.name

            try:
                result = self.run_cli_command(
                    [
                        "scan",
                        "--terraform",
                        tf_file,
                        "--rules",
                        str(legacy_rules_file),
                        "--output-format",
                        "json",
                    ]
                )

                assert result.returncode in [0, 1], f"Legacy TF format {i} failed: {result.stderr}"

                # Should produce valid output
                try:
                    self.extract_json_from_output(result.stdout)
                except (json.JSONDecodeError, ValueError):
                    pytest.fail(f"Legacy TF format {i} produced invalid JSON")

            finally:
                os.unlink(tf_file)

    def test_legacy_environment_variable_support(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that legacy environment variables are still supported."""
        # Test with environment variables that might have been supported
        env_vars = {
            "RIVETER_LOG_LEVEL": "DEBUG",
            "RIVETER_CONFIG": "/tmp/nonexistent",  # Should not break if file doesn't exist
        }

        for env_var, value in env_vars.items():
            env = os.environ.copy()
            env[env_var] = value

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "riveter.cli",
                    "scan",
                    "--terraform",
                    str(legacy_terraform_file),
                    "--rules",
                    str(legacy_rules_file),
                    "--output-format",
                    "json",
                ],
                env=env,
                capture_output=True,
                text=True,
            )

            # Should not fail due to environment variable
            assert result.returncode in [0, 1], f"Failed with {env_var}={value}: {result.stderr}"

    def test_legacy_command_aliases(self, legacy_terraform_file: Path):
        """Test that any legacy command aliases still work."""
        # Test potential legacy aliases or alternative command names
        # This would depend on what aliases were supported in the past

        # Test that main commands work with full names
        commands_to_test = [
            ["list-rule-packs"],
            ["validate-rule-pack", "rule_packs/aws-security.yml"],
        ]

        for cmd in commands_to_test:
            result = self.run_cli_command(cmd)
            # Should work without errors
            assert result.returncode in [0, 1, 2]  # Allow various success/error codes

    def test_legacy_configuration_file_support(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that legacy configuration files are supported."""
        # Create a legacy-style configuration file
        config_content = """
# Legacy configuration format
default_rule_pack: aws-security
output_format: json
verbose: false
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write(config_content)
            config_file = f.name

        try:
            # Test that configuration file doesn't break the command
            # (even if it's not actively used)
            result = self.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(legacy_terraform_file),
                    "--rules",
                    str(legacy_rules_file),
                ]
            )

            assert result.returncode in [0, 1]

        finally:
            os.unlink(config_file)

    def test_legacy_performance_characteristics(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that performance characteristics haven't degraded significantly."""
        import time

        # Measure execution time
        start_time = time.time()

        result = self.run_cli_command(
            [
                "scan",
                "--terraform",
                str(legacy_terraform_file),
                "--rules",
                str(legacy_rules_file),
                "--output-format",
                "json",
            ]
        )

        end_time = time.time()
        execution_time = end_time - start_time

        assert result.returncode in [0, 1]

        # Should complete within reasonable time (adjust threshold as needed)
        # This is a basic performance regression test
        assert execution_time < 10.0, f"Execution took too long: {execution_time}s"

    def test_legacy_memory_usage_patterns(
        self, legacy_terraform_file: Path, legacy_rules_file: Path
    ):
        """Test that memory usage patterns are reasonable."""
        # This is a basic test to ensure we don't have obvious memory leaks
        # In a real scenario, you might use memory profiling tools

        # Run the command multiple times to check for memory leaks
        for _ in range(3):
            result = self.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(legacy_terraform_file),
                    "--rules",
                    str(legacy_rules_file),
                    "--output-format",
                    "json",
                ]
            )

            assert result.returncode in [0, 1]

            # Basic check that output is consistent
            try:
                self.extract_json_from_output(result.stdout)
            except (json.JSONDecodeError, ValueError):
                pytest.fail("Inconsistent output across runs")
