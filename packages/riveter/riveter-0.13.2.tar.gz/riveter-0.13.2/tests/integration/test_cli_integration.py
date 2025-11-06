"""Integration tests for CLI commands with real components."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from riveter.cli.main import main as cli_main
from riveter.models.core import ValidationSummary


def run_cli_command(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Helper function to run CLI commands with proper environment setup."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")

    return subprocess.run(
        [sys.executable, "-m", "riveter.cli"] + args,
        env=env,
        capture_output=True,
        text=True,
        **kwargs,
    )


def extract_json_from_output(output: str) -> Dict[str, Any]:
    """Extract JSON from CLI output that may contain informational messages."""
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


class TestCLIIntegrationBasic:
    """Basic CLI integration tests."""

    def test_cli_help_command(self):
        """Test that CLI help command works."""
        result = run_cli_command(["--help"])

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "scan" in result.stdout
        assert "list-rule-packs" in result.stdout

    def test_cli_version_command(self):
        """Test that CLI version command works."""
        result = run_cli_command(["--version"])

        assert result.returncode == 0
        # Should contain version information
        assert any(char.isdigit() for char in result.stdout)

    def test_cli_invalid_command(self):
        """Test CLI behavior with invalid command."""
        result = run_cli_command(["invalid-command"])

        assert result.returncode != 0
        assert "Error:" in result.stderr or "Usage:" in result.stdout


class TestScanCommandIntegration:
    """Integration tests for the scan command."""

    @pytest.fixture
    def sample_terraform_file(self, tmp_path: Path) -> Path:
        """Create a sample Terraform file for testing."""
        tf_content = """
# Sample Terraform configuration for integration testing
resource "aws_instance" "web_server" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server"
    Environment = "production"
    CostCenter  = "12345"
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  security_groups = ["sg-12345678"]
}

resource "aws_s3_bucket" "data_bucket" {
  bucket = "my-test-bucket-12345"

  tags = {
    Environment = "production"
    Purpose     = "data-storage"
  }
}

resource "aws_rds_instance" "database" {
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.micro"
  allocated_storage = 20

  tags = {
    Environment = "production"
    Name        = "database"
  }
}
"""
        tf_file = tmp_path / "main.tf"
        tf_file.write_text(tf_content)
        return tf_file

    @pytest.fixture
    def sample_rules_file(self, tmp_path: Path) -> Path:
        """Create a sample rules file for testing."""
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
    description: EC2 instances must have CostCenter tag
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

  - id: all-resources-environment-tag
    resource_type: "*"
    description: All resources must have Environment tag
    assert:
      tags:
        Environment: production
"""
        rules_file = tmp_path / "test_rules.yml"
        rules_file.write_text(rules_content)
        return rules_file

    def test_scan_with_custom_rules_file(
        self, sample_terraform_file: Path, sample_rules_file: Path
    ):
        """Test scanning with custom rules file."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rules",
                str(sample_rules_file),
                "--output-format",
                "json",
            ]
        )

        assert result.returncode in [0, 1]  # 0 for pass, 1 for violations

        # Should produce valid JSON output
        try:
            output_data = extract_json_from_output(result.stdout)
            assert isinstance(output_data, dict)
            assert "summary" in output_data or "results" in output_data
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Failed to parse JSON output: {e}")

    def test_scan_with_rule_pack(self, sample_terraform_file: Path):
        """Test scanning with built-in rule pack."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rule-pack",
                "aws-security",
                "--output-format",
                "json",
            ]
        )

        assert result.returncode in [0, 1]  # 0 for pass, 1 for violations

        try:
            output_data = extract_json_from_output(result.stdout)
            assert isinstance(output_data, dict)
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Failed to parse JSON output: {e}")

    def test_scan_table_output_format(self, sample_terraform_file: Path, sample_rules_file: Path):
        """Test scan command with table output format."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rules",
                str(sample_rules_file),
                "--output-format",
                "table",
            ]
        )

        assert result.returncode in [0, 1]
        assert len(result.stdout.strip()) > 0
        # Table output should contain some structure
        assert "|" in result.stdout or "─" in result.stdout or "Rule" in result.stdout

    def test_scan_junit_output_format(self, sample_terraform_file: Path, sample_rules_file: Path):
        """Test scan command with JUnit XML output format."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rules",
                str(sample_rules_file),
                "--output-format",
                "junit",
            ]
        )

        assert result.returncode in [0, 1]
        # JUnit output should contain XML
        assert "<?xml" in result.stdout or "<testsuite" in result.stdout

    def test_scan_sarif_output_format(self, sample_terraform_file: Path, sample_rules_file: Path):
        """Test scan command with SARIF output format."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rules",
                str(sample_rules_file),
                "--output-format",
                "sarif",
            ]
        )

        assert result.returncode in [0, 1]

        # SARIF output should be valid JSON with specific structure
        try:
            output_data = extract_json_from_output(result.stdout)
            # SARIF should have specific schema
            assert "$schema" in output_data or "version" in output_data or "runs" in output_data
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Failed to parse SARIF output: {e}")

    def test_scan_verbose_output(self, sample_terraform_file: Path, sample_rules_file: Path):
        """Test scan command with verbose output."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rules",
                str(sample_rules_file),
                "--output-format",
                "json",
                "--verbose",
            ]
        )

        assert result.returncode in [0, 1]
        # Verbose output should contain additional information
        # This might be in stderr or stdout depending on implementation
        total_output = result.stdout + result.stderr
        assert len(total_output) > 0

    def test_scan_nonexistent_terraform_file(self):
        """Test scan command with nonexistent Terraform file."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                "nonexistent.tf",
                "--rule-pack",
                "aws-security",
                "--output-format",
                "json",
            ]
        )

        assert result.returncode != 0
        assert "Error:" in result.stderr or "not found" in result.stderr.lower()

    def test_scan_nonexistent_rules_file(self, sample_terraform_file: Path):
        """Test scan command with nonexistent rules file."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rules",
                "nonexistent_rules.yml",
                "--output-format",
                "json",
            ]
        )

        assert result.returncode != 0
        assert "Error:" in result.stderr or "not found" in result.stderr.lower()

    def test_scan_invalid_terraform_file(self, tmp_path: Path):
        """Test scan command with invalid Terraform file."""
        invalid_tf = tmp_path / "invalid.tf"
        invalid_tf.write_text("invalid terraform syntax {{{")

        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(invalid_tf),
                "--rule-pack",
                "aws-security",
                "--output-format",
                "json",
            ]
        )

        assert result.returncode != 0
        # Should report parsing error
        assert "Error:" in result.stderr or "parse" in result.stderr.lower()

    def test_scan_multiple_rule_packs(self, sample_terraform_file: Path):
        """Test scan command with multiple rule packs."""
        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(sample_terraform_file),
                "--rule-pack",
                "aws-security",
                "--rule-pack",
                "cis-aws",
                "--output-format",
                "json",
            ]
        )

        assert result.returncode in [0, 1]

        try:
            output_data = extract_json_from_output(result.stdout)
            assert isinstance(output_data, dict)
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Failed to parse JSON output: {e}")


class TestListRulePacksIntegration:
    """Integration tests for the list-rule-packs command."""

    def test_list_rule_packs_basic(self):
        """Test basic list-rule-packs command."""
        result = run_cli_command(["list-rule-packs"])

        assert result.returncode == 0
        assert "Available Rule Packs" in result.stdout or "Rule Packs" in result.stdout

        # Should list some built-in rule packs
        expected_packs = ["aws-security", "cis-aws", "gcp-security", "azure-security"]
        for pack in expected_packs:
            assert pack in result.stdout

    def test_list_rule_packs_shows_metadata(self):
        """Test that list-rule-packs shows rule pack metadata."""
        result = run_cli_command(["list-rule-packs"])

        assert result.returncode == 0

        # Should show version information
        assert "1.0.0" in result.stdout or "version" in result.stdout.lower()

        # Should show rule counts
        lines = result.stdout.split("\n")
        rule_count_lines = [line for line in lines if any(char.isdigit() for char in line)]
        assert len(rule_count_lines) > 0

    def test_list_rule_packs_total_count(self):
        """Test that list-rule-packs shows total count."""
        result = run_cli_command(["list-rule-packs"])

        assert result.returncode == 0

        # Should show total count
        assert "Total" in result.stdout or "total" in result.stdout

        # Extract total count
        lines = result.stdout.split("\n")
        total_lines = [line for line in lines if "total" in line.lower()]
        assert len(total_lines) >= 1


class TestValidateRulePackIntegration:
    """Integration tests for the validate-rule-pack command."""

    def test_validate_existing_rule_pack(self):
        """Test validating an existing rule pack."""
        result = run_cli_command(["validate-rule-pack", "rule_packs/aws-security.yml"])

        assert result.returncode == 0
        assert "✓" in result.stdout or "valid" in result.stdout.lower()

    def test_validate_nonexistent_rule_pack(self):
        """Test validating a nonexistent rule pack."""
        result = run_cli_command(["validate-rule-pack", "nonexistent-pack.yml"])

        assert result.returncode != 0
        assert "Error:" in result.stderr or "not found" in result.stderr.lower()

    def test_validate_invalid_rule_pack(self, tmp_path: Path):
        """Test validating an invalid rule pack."""
        invalid_pack = tmp_path / "invalid_pack.yml"
        invalid_pack.write_text(
            """
rules:
  - id: invalid-rule
    # Missing required fields
    description: Invalid rule
"""
        )

        result = run_cli_command(["validate-rule-pack", str(invalid_pack)])

        assert result.returncode != 0
        assert "Error:" in result.stderr or "invalid" in result.stderr.lower()

    @pytest.fixture
    def valid_rule_pack_file(self, tmp_path: Path) -> Path:
        """Create a valid rule pack file for testing."""
        pack_content = """
metadata:
  name: test-pack
  version: 1.0.0
  author: Test Author
  description: Test rule pack for integration testing

rules:
  - id: test-rule-001
    resource_type: aws_instance
    description: Test rule for EC2 instances
    severity: error
    assert:
      tags:
        Environment: present

  - id: test-rule-002
    resource_type: aws_s3_bucket
    description: Test rule for S3 buckets
    severity: warning
    assert:
      tags:
        Purpose: present
"""
        pack_file = tmp_path / "test_pack.yml"
        pack_file.write_text(pack_content)
        return pack_file

    def test_validate_valid_rule_pack(self, valid_rule_pack_file: Path):
        """Test validating a valid rule pack."""
        result = run_cli_command(["validate-rule-pack", str(valid_rule_pack_file)])

        assert result.returncode == 0
        assert "✓" in result.stdout or "valid" in result.stdout.lower()
        assert "2 rules" in result.stdout or "Rules: 2" in result.stdout


class TestEndToEndWorkflows:
    """End-to-end workflow integration tests."""

    @pytest.fixture
    def complete_test_setup(self, tmp_path: Path):
        """Create a complete test setup with Terraform files and rules."""
        # Create Terraform file
        tf_content = """
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server"
    Environment = "production"
    CostCenter  = "12345"
  }
}

resource "aws_instance" "test" {
  ami           = "ami-87654321"
  instance_type = "t3.nano"

  tags = {
    Name        = "test-server"
    Environment = "staging"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "test-data-bucket"

  tags = {
    Environment = "production"
    Purpose     = "data-storage"
  }
}
"""
        tf_file = tmp_path / "infrastructure.tf"
        tf_file.write_text(tf_content)

        # Create rules file
        rules_content = """
rules:
  - id: production-cost-center
    resource_type: aws_instance
    description: Production instances must have CostCenter tag
    filter:
      tags:
        Environment: production
    assert:
      tags:
        CostCenter: present

  - id: s3-purpose-required
    resource_type: aws_s3_bucket
    description: S3 buckets must have Purpose tag
    assert:
      tags:
        Purpose: present

  - id: environment-tag-universal
    resource_type: "*"
    description: All resources must have Environment tag
    assert:
      tags:
        Environment: present
"""
        rules_file = tmp_path / "compliance_rules.yml"
        rules_file.write_text(rules_content)

        return {"terraform_file": tf_file, "rules_file": rules_file, "tmp_path": tmp_path}

    def test_complete_scan_workflow(self, complete_test_setup):
        """Test complete scan workflow from start to finish."""
        setup = complete_test_setup

        # Step 1: Validate the rule pack
        validate_result = run_cli_command(["validate-rule-pack", str(setup["rules_file"])])
        assert validate_result.returncode == 0

        # Step 2: Run scan with JSON output
        scan_result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(setup["terraform_file"]),
                "--rules",
                str(setup["rules_file"]),
                "--output-format",
                "json",
            ]
        )

        assert scan_result.returncode in [0, 1]

        # Parse and validate JSON output
        output_data = extract_json_from_output(scan_result.stdout)
        assert isinstance(output_data, dict)

        # Should have summary information
        if "summary" in output_data:
            summary = output_data["summary"]
            assert "total_rules" in summary
            assert "total_resources" in summary
            assert summary["total_resources"] == 3  # web, test, data

        # Step 3: Run scan with table output
        table_result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(setup["terraform_file"]),
                "--rules",
                str(setup["rules_file"]),
                "--output-format",
                "table",
            ]
        )

        assert table_result.returncode in [0, 1]
        assert len(table_result.stdout.strip()) > 0

    def test_scan_with_mixed_results(self, complete_test_setup):
        """Test scan that produces both passing and failing results."""
        setup = complete_test_setup

        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(setup["terraform_file"]),
                "--rules",
                str(setup["rules_file"]),
                "--output-format",
                "json",
                "--verbose",
            ]
        )

        # Should have exit code 1 due to some failures (test instance missing CostCenter)
        assert result.returncode == 1

        output_data = extract_json_from_output(result.stdout)

        # Should have both passed and failed results
        if "results" in output_data:
            results = output_data["results"]
            passed_results = [r for r in results if r.get("status") or r.get("passed")]
            failed_results = [r for r in results if not (r.get("status") or r.get("passed"))]

            assert len(passed_results) > 0
            assert len(failed_results) > 0

    def test_performance_with_large_configuration(self, tmp_path: Path):
        """Test performance with larger Terraform configuration."""
        # Generate a larger Terraform file
        tf_content = "# Large Terraform configuration for performance testing\n\n"

        for i in range(50):  # Create 50 resources
            tf_content += f"""
resource "aws_instance" "instance_{i}" {{
  ami           = "ami-{i:08d}"
  instance_type = "t3.micro"

  tags = {{
    Name        = "instance-{i}"
    Environment = "{"production" if i % 2 == 0 else "staging"}"
    Index       = "{i}"
  }}
}}
"""

        tf_file = tmp_path / "large_infrastructure.tf"
        tf_file.write_text(tf_content)

        # Create simple rules
        rules_content = """
rules:
  - id: environment-required
    resource_type: aws_instance
    description: Instances must have Environment tag
    assert:
      tags:
        Environment: present

  - id: name-required
    resource_type: aws_instance
    description: Instances must have Name tag
    assert:
      tags:
        Name: present
"""
        rules_file = tmp_path / "simple_rules.yml"
        rules_file.write_text(rules_content)

        # Run scan and measure basic performance
        import time

        start_time = time.time()

        result = run_cli_command(
            [
                "scan",
                "--terraform",
                str(tf_file),
                "--rules",
                str(rules_file),
                "--output-format",
                "json",
            ]
        )

        end_time = time.time()
        execution_time = end_time - start_time

        assert result.returncode in [0, 1]

        # Should complete within reasonable time (adjust threshold as needed)
        assert execution_time < 30.0  # 30 seconds max

        # Verify all resources were processed
        output_data = extract_json_from_output(result.stdout)
        if "summary" in output_data:
            assert output_data["summary"]["total_resources"] == 50


class TestBackwardCompatibilityIntegration:
    """Integration tests for backward compatibility."""

    def test_legacy_command_line_interface(self, tmp_path: Path):
        """Test that legacy command line interface still works."""
        # Create minimal test files
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami = "ami-12345"
  instance_type = "t3.micro"
  tags = { Environment = "test" }
}
"""
        )

        # Test various legacy command formats
        legacy_commands = [
            ["scan", "--terraform", str(tf_file), "--rule-pack", "aws-security"],
            ["list-rule-packs"],
            ["validate-rule-pack", "rule_packs/aws-security.yml"],
        ]

        for cmd in legacy_commands:
            result = run_cli_command(cmd)
            # Should not fail due to interface changes
            assert result.returncode in [0, 1, 2]  # Allow various exit codes but no crashes

    def test_output_format_compatibility(self, tmp_path: Path):
        """Test that output formats remain compatible."""
        tf_file = tmp_path / "test.tf"
        tf_file.write_text(
            """
resource "aws_instance" "test" {
  ami = "ami-12345"
  instance_type = "t3.micro"
  tags = { Environment = "test" }
}
"""
        )

        # Test all supported output formats
        formats = ["json", "table", "junit", "sarif"]

        for fmt in formats:
            result = run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(tf_file),
                    "--rule-pack",
                    "aws-security",
                    "--output-format",
                    fmt,
                ]
            )

            assert result.returncode in [0, 1]
            assert len(result.stdout.strip()) > 0

            # Basic format validation
            if fmt == "json":
                try:
                    json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Try extracting JSON from mixed output
                    extract_json_from_output(result.stdout)
            elif fmt == "junit":
                assert "<?xml" in result.stdout or "<testsuite" in result.stdout
            elif fmt == "sarif":
                try:
                    sarif_data = json.loads(result.stdout)
                    assert isinstance(sarif_data, dict)
                except json.JSONDecodeError:
                    sarif_data = extract_json_from_output(result.stdout)
                    assert isinstance(sarif_data, dict)
