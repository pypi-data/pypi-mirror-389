"""Pytest configuration and fixtures for Riveter tests.

This module provides comprehensive test fixtures and utilities for testing
the Riveter CLI tool, including backward compatibility validation and
performance regression testing.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from riveter.scanner import ValidationResult


# Test configuration and markers
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance benchmarks")
    config.addinivalue_line(
        "markers", "compatibility: marks tests as backward compatibility validation"
    )
    config.addinivalue_line("markers", "cli: marks tests as CLI interface tests")
    config.addinivalue_line("markers", "regression: marks tests as regression tests")
    config.addinivalue_line("markers", "security: marks tests as security-related tests")


# Performance tracking fixtures
@pytest.fixture(scope="session")
def performance_tracker():
    """Track performance metrics across test sessions."""

    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
            self.baselines = {}

        def record_metric(self, test_name: str, metric_name: str, value: float):
            """Record a performance metric."""
            if test_name not in self.metrics:
                self.metrics[test_name] = {}
            self.metrics[test_name][metric_name] = value

        def set_baseline(self, test_name: str, metric_name: str, baseline: float):
            """Set a performance baseline."""
            if test_name not in self.baselines:
                self.baselines[test_name] = {}
            self.baselines[test_name][metric_name] = baseline

        def check_regression(self, test_name: str, metric_name: str, threshold: float = 1.2):
            """Check if performance has regressed beyond threshold."""
            if (
                test_name in self.metrics
                and metric_name in self.metrics[test_name]
                and test_name in self.baselines
                and metric_name in self.baselines[test_name]
            ):
                current = self.metrics[test_name][metric_name]
                baseline = self.baselines[test_name][metric_name]
                return current <= baseline * threshold
            return True

    return PerformanceTracker()


@pytest.fixture
def benchmark_timer():
    """Utility for timing operations in tests."""

    class BenchmarkTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            """Start timing."""
            self.start_time = time.perf_counter()

        def stop(self):
            """Stop timing and return elapsed time."""
            self.end_time = time.perf_counter()
            return self.elapsed

        @property
        def elapsed(self):
            """Get elapsed time in seconds."""
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return BenchmarkTimer()


# Backward compatibility fixtures
@pytest.fixture(scope="session")
def compatibility_baseline():
    """Load baseline data for backward compatibility testing."""
    baseline_file = Path(__file__).parent / "fixtures" / "compatibility_baseline.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            return json.load(f)
    return {}


@pytest.fixture
def cli_output_validator():
    """Validate CLI output for backward compatibility."""

    class CLIOutputValidator:
        def __init__(self, baseline_data: dict[str, Any]):
            self.baseline_data = baseline_data

        def validate_output_format(self, command: str, output: str, format_type: str = "table"):
            """Validate that output format matches baseline."""
            baseline_key = f"{command}_{format_type}"
            if baseline_key in self.baseline_data:
                baseline_output = self.baseline_data[baseline_key]
                # Implement specific validation logic based on format
                return self._compare_outputs(output, baseline_output, format_type)
            return True

        def _compare_outputs(self, current: str, baseline: str, format_type: str) -> bool:
            """Compare outputs based on format type."""
            if format_type == "json":
                try:
                    current_data = json.loads(current)
                    baseline_data = json.loads(baseline)
                    return self._compare_json_structure(current_data, baseline_data)
                except json.JSONDecodeError:
                    return False
            elif format_type == "table":
                return self._compare_table_structure(current, baseline)
            else:
                return current.strip() == baseline.strip()

        def _compare_json_structure(self, current: Any, baseline: Any) -> bool:
            """Compare JSON structure while allowing for data differences."""
            if type(current) != type(baseline):
                return False
            if isinstance(current, dict):
                return set(current.keys()) == set(baseline.keys()) and all(
                    self._compare_json_structure(current[k], baseline[k]) for k in current.keys()
                )
            if isinstance(current, list):
                return len(current) == len(baseline)
            return True

        def _compare_table_structure(self, current: str, baseline: str) -> bool:
            """Compare table structure (headers and column count)."""
            current_lines = current.strip().split("\n")
            baseline_lines = baseline.strip().split("\n")

            if len(current_lines) == 0 or len(baseline_lines) == 0:
                return len(current_lines) == len(baseline_lines)

            # Compare header structure
            current_header = current_lines[0]
            baseline_header = baseline_lines[0]

            # Count columns (assuming pipe-separated or space-separated)
            current_cols = len([col for col in current_header.split("|") if col.strip()])
            baseline_cols = len([col for col in baseline_header.split("|") if col.strip()])

            return current_cols == baseline_cols

    return CLIOutputValidator


# Enhanced test data fixtures
@pytest.fixture
def sample_terraform_config():
    """Sample Terraform configuration for testing."""
    return {
        "resources": [
            {
                "id": "web_server",
                "resource_type": "aws_instance",
                "instance_type": "t3.micro",
                "ami": "ami-12345678",
                "tags": {"Environment": "production", "Name": "web-server", "CostCenter": "12345"},
                "security_groups": ["sg-12345678"],
                "root_block_device": {"volume_size": 20, "volume_type": "gp3"},
            },
            {
                "id": "database",
                "resource_type": "aws_rds_instance",
                "engine": "mysql",
                "engine_version": "8.0",
                "instance_class": "db.t3.micro",
                "allocated_storage": 20,
                "tags": {"Environment": "production", "Name": "database"},
            },
            {
                "id": "storage_bucket",
                "resource_type": "aws_s3_bucket",
                "bucket": "my-test-bucket",
                "tags": {"Environment": "production", "Purpose": "data-storage"},
            },
        ]
    }


@pytest.fixture
def sample_rule_dict():
    """Sample rule dictionary for testing."""
    return {
        "id": "test-rule-001",
        "resource_type": "aws_instance",
        "description": "Test rule for EC2 instances",
        "filter": {"tags": {"Environment": "production"}},
        "assert": {"tags": {"CostCenter": "present"}},
    }


@pytest.fixture
def sample_rule(sample_rule_dict):
    """Sample Rule object for testing."""
    from riveter.rules import create_rule_from_dict

    return create_rule_from_dict(sample_rule_dict)


@pytest.fixture
def sample_rules_list(sample_rule_dict):
    """List of sample rules for testing."""
    from riveter.rules import create_rule_from_dict

    rules_data = [
        sample_rule_dict,
        {
            "id": "test-rule-002",
            "resource_type": "aws_s3_bucket",
            "description": "Test rule for S3 buckets",
            "assert": {"tags": {"Purpose": "present"}},
        },
        {
            "id": "test-rule-003",
            "resource_type": "*",
            "description": "Universal rule for all resources",
            "assert": {"tags": {"Environment": "production"}},
        },
    ]
    return [create_rule_from_dict(rule_dict) for rule_dict in rules_data]


@pytest.fixture
def temp_terraform_file():
    """Create a temporary Terraform file for testing."""
    terraform_content = """
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

resource "aws_s3_bucket" "storage" {
  bucket = "my-test-bucket"

  tags = {
    Environment = "production"
    Purpose     = "data-storage"
  }
}
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tf", delete=False) as f:
        f.write(terraform_content)
        temp_file_path = f.name

    yield temp_file_path

    # Cleanup
    os.unlink(temp_file_path)


@pytest.fixture
def temp_rules_file():
    """Create a temporary rules YAML file for testing."""
    rules_content = """
rules:
  - id: test-rule-001
    resource_type: aws_instance
    description: Test rule for EC2 instances
    filter:
      tags:
        Environment: production
    assert:
      tags:
        CostCenter: present

  - id: test-rule-002
    resource_type: aws_s3_bucket
    description: Test rule for S3 buckets
    assert:
      tags:
        Purpose: present

  - id: test-rule-003
    resource_type: "*"
    description: Universal rule for all resources
    assert:
      tags:
        Environment: production
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(rules_content)
        temp_file_path = f.name

    yield temp_file_path

    # Cleanup
    os.unlink(temp_file_path)


@pytest.fixture
def mock_validation_results(sample_rules_list, sample_terraform_config):
    """Create mock validation results for testing."""
    results = []

    # Create some passing and failing results
    rule1 = sample_rules_list[0]  # aws_instance rule
    resource1 = sample_terraform_config["resources"][0]  # web_server

    results.append(
        ValidationResult(rule=rule1, resource=resource1, passed=True, message="All checks passed")
    )

    rule2 = sample_rules_list[1]  # aws_s3_bucket rule
    resource2 = sample_terraform_config["resources"][2]  # storage_bucket

    results.append(
        ValidationResult(rule=rule2, resource=resource2, passed=True, message="All checks passed")
    )

    # Add a failing result
    results.append(
        ValidationResult(
            rule=rule1,
            resource={"id": "failing_instance", "resource_type": "aws_instance"},
            passed=False,
            message="Required tag 'CostCenter' is missing",
        )
    )

    return results


# Test data management fixtures
@pytest.fixture(scope="session")
def test_data_manager():
    """Manage test data and fixtures."""

    class TestDataManager:
        def __init__(self):
            self.fixtures_dir = Path(__file__).parent / "fixtures"
            self.terraform_dir = self.fixtures_dir / "terraform"
            self.rules_dir = self.fixtures_dir / "rules"
            self.rule_packs_dir = self.fixtures_dir / "rule_packs"

        def get_terraform_file(self, name: str) -> Path:
            """Get path to a Terraform test file."""
            return self.terraform_dir / f"{name}.tf"

        def get_rules_file(self, name: str) -> Path:
            """Get path to a rules test file."""
            return self.rules_dir / f"{name}.yml"

        def get_rule_pack_file(self, name: str) -> Path:
            """Get path to a rule pack test file."""
            return self.rule_packs_dir / f"{name}.yml"

        def list_terraform_files(self) -> list[str]:
            """List available Terraform test files."""
            return [f.stem for f in self.terraform_dir.glob("*.tf")]

        def list_rules_files(self) -> list[str]:
            """List available rules test files."""
            return [f.stem for f in self.rules_dir.glob("*.yml")]

        def list_rule_pack_files(self) -> list[str]:
            """List available rule pack test files."""
            return [f.stem for f in self.rule_packs_dir.glob("*.yml")]

    return TestDataManager()


# Mock utilities
class MockResource:
    """Utility class for creating mock resources in tests."""

    @staticmethod
    def create_aws_instance(
        instance_id: str = "test-instance",
        instance_type: str = "t3.micro",
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a mock AWS instance resource."""
        if tags is None:
            tags = {"Environment": "test"}

        return {
            "id": instance_id,
            "resource_type": "aws_instance",
            "instance_type": instance_type,
            "ami": "ami-12345678",
            "tags": tags,
            "security_groups": ["sg-12345678"],
        }

    @staticmethod
    def create_s3_bucket(
        bucket_id: str = "test-bucket",
        bucket_name: str = "my-test-bucket",
        tags: dict[str, str] = None,
    ) -> dict[str, Any]:
        """Create a mock S3 bucket resource."""
        if tags is None:
            tags = {"Environment": "test"}

        return {
            "id": bucket_id,
            "resource_type": "aws_s3_bucket",
            "bucket": bucket_name,
            "tags": tags,
        }

    @staticmethod
    def create_rds_instance(
        instance_id: str = "test-db", engine: str = "mysql", tags: dict[str, str] = None
    ) -> dict[str, Any]:
        """Create a mock RDS instance resource."""
        if tags is None:
            tags = {"Environment": "test"}

        return {
            "id": instance_id,
            "resource_type": "aws_rds_instance",
            "engine": engine,
            "engine_version": "8.0",
            "instance_class": "db.t3.micro",
            "allocated_storage": 20,
            "tags": tags,
        }


class MockRule:
    """Utility class for creating mock rules in tests."""

    @staticmethod
    def create_tag_rule(
        rule_id: str = "test-rule",
        resource_type: str = "aws_instance",
        required_tags: dict[str, str] = None,
        filter_tags: dict[str, str] = None,
    ) -> dict[str, Any]:
        """Create a mock rule that checks for required tags."""
        if required_tags is None:
            required_tags = {"Environment": "present"}

        rule_dict = {
            "id": rule_id,
            "resource_type": resource_type,
            "description": f"Test rule for {resource_type}",
            "assert": {"tags": required_tags},
        }

        if filter_tags:
            rule_dict["filter"] = {"tags": filter_tags}

        return rule_dict

    @staticmethod
    def create_property_rule(
        rule_id: str = "test-property-rule",
        resource_type: str = "aws_instance",
        property_name: str = "instance_type",
        expected_value: str = "t3.micro",
    ) -> dict[str, Any]:
        """Create a mock rule that checks a specific property value."""
        return {
            "id": rule_id,
            "resource_type": resource_type,
            "description": f"Test rule checking {property_name}",
            "assert": {property_name: expected_value},
        }


@pytest.fixture
def mock_resource():
    """Provide MockResource utility class."""
    return MockResource


@pytest.fixture
def mock_rule():
    """Provide MockRule utility class."""
    return MockRule


# CLI testing fixtures
@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing CLI commands."""
    from click.testing import CliRunner

    return CliRunner()


@pytest.fixture
def isolated_filesystem():
    """Provide an isolated filesystem for CLI tests."""
    from click.testing import CliRunner

    runner = CliRunner()
    with runner.isolated_filesystem():
        yield Path.cwd()


# Environment and configuration fixtures
@pytest.fixture
def clean_environment(monkeypatch):
    """Provide a clean environment for testing."""
    # Clear relevant environment variables
    env_vars_to_clear = [
        "RIVETER_CONFIG",
        "RIVETER_RULES_PATH",
        "RIVETER_CACHE_DIR",
        "RIVETER_LOG_LEVEL",
    ]

    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        yield config_dir


# Performance regression testing fixtures
@pytest.fixture
def performance_baseline():
    """Load performance baselines for regression testing."""
    baseline_file = Path(__file__).parent / "fixtures" / "performance_baseline.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            return json.load(f)
    return {
        "cli_startup_time": 2.0,  # seconds
        "config_parse_time": 0.5,  # seconds
        "rule_evaluation_time": 1.0,  # seconds per 100 rules
        "memory_usage": 100,  # MB
    }


@pytest.fixture
def memory_profiler():
    """Provide memory profiling utilities."""
    try:
        import psutil

        class MemoryProfiler:
            def __init__(self):
                self.process = psutil.Process()
                self.initial_memory = None

            def start(self):
                """Start memory profiling."""
                self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

            def current_usage(self):
                """Get current memory usage in MB."""
                return self.process.memory_info().rss / 1024 / 1024

            def peak_usage(self):
                """Get peak memory usage since start."""
                if self.initial_memory is None:
                    return self.current_usage()
                return max(0, self.current_usage() - self.initial_memory)

        return MemoryProfiler()
    except ImportError:
        # Fallback mock if psutil is not available
        class MockMemoryProfiler:
            def start(self):
                pass

            def current_usage(self):
                return 0

            def peak_usage(self):
                return 0

        return MockMemoryProfiler()
