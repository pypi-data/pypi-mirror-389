"""Performance benchmarks for CLI commands."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

import psutil
import pytest


class CLIBenchmarkRunner:
    """Utility class for running CLI benchmarks."""

    def __init__(self):
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")

    def run_cli_command(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """Run CLI command and measure performance metrics."""
        # Start monitoring
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.perf_counter()
        start_cpu_time = time.process_time()

        # Run command
        result = subprocess.run(
            [sys.executable, "-m", "riveter.cli"] + args,
            env=self.env,
            capture_output=True,
            text=True,
            **kwargs,
        )

        end_time = time.perf_counter()
        end_cpu_time = time.process_time()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "wall_time": end_time - start_time,
            "cpu_time": end_cpu_time - start_cpu_time,
            "memory_usage": final_memory - initial_memory,
            "peak_memory": final_memory,
        }

    def extract_json_from_output(self, output: str) -> Dict[str, Any]:
        """Extract JSON from CLI output."""
        lines = output.strip().split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_output = "\n".join(lines[i:])
                return json.loads(json_output)
        raise ValueError("No JSON found in output")


class TestCLIStartupPerformance:
    """Benchmark CLI startup performance."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = CLIBenchmarkRunner()

    @pytest.mark.performance
    def test_help_command_startup_time(self):
        """Benchmark help command startup time."""
        results = []

        # Run multiple times to get average
        for _ in range(5):
            result = self.runner.run_cli_command(["--help"])
            assert result["returncode"] == 0
            results.append(result["wall_time"])

        avg_time = sum(results) / len(results)
        max_time = max(results)
        min_time = min(results)

        # Performance assertions
        assert avg_time < 2.0, f"Help command too slow: {avg_time:.3f}s average"
        assert max_time < 3.0, f"Help command max time too slow: {max_time:.3f}s"

        print(
            f"Help command startup: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s"
        )

    @pytest.mark.performance
    def test_version_command_startup_time(self):
        """Benchmark version command startup time."""
        results = []

        for _ in range(5):
            result = self.runner.run_cli_command(["--version"])
            assert result["returncode"] == 0
            results.append(result["wall_time"])

        avg_time = sum(results) / len(results)

        # Version should be very fast
        assert avg_time < 1.5, f"Version command too slow: {avg_time:.3f}s"

        print(f"Version command startup: {avg_time:.3f}s average")

    @pytest.mark.performance
    def test_list_rule_packs_startup_time(self):
        """Benchmark list-rule-packs command startup time."""
        results = []

        for _ in range(3):
            result = self.runner.run_cli_command(["list-rule-packs"])
            assert result["returncode"] == 0
            results.append(result["wall_time"])

        avg_time = sum(results) / len(results)

        # Should be reasonably fast
        assert avg_time < 3.0, f"List rule packs too slow: {avg_time:.3f}s"

        print(f"List rule packs startup: {avg_time:.3f}s average")

    @pytest.mark.performance
    def test_cli_memory_usage_startup(self):
        """Benchmark CLI memory usage during startup."""
        commands = [["--help"], ["--version"], ["list-rule-packs"]]

        for cmd in commands:
            result = self.runner.run_cli_command(cmd)
            assert result["returncode"] == 0

            # Memory usage should be reasonable
            assert (
                result["peak_memory"] < 200
            ), f"Command {cmd} uses too much memory: {result['peak_memory']:.1f}MB"

            print(f"Command {' '.join(cmd)} memory: {result['peak_memory']:.1f}MB")


class TestScanCommandPerformance:
    """Benchmark scan command performance."""

    def setup_method(self):
        """Set up benchmark runner and test files."""
        self.runner = CLIBenchmarkRunner()

    @pytest.fixture
    def small_terraform_file(self, tmp_path: Path) -> Path:
        """Create small Terraform file for benchmarking."""
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

resource "aws_s3_bucket" "data" {
  bucket = "test-bucket"
  tags = {
    Environment = "production"
    Purpose     = "storage"
  }
}
"""
        tf_file = tmp_path / "small.tf"
        tf_file.write_text(tf_content)
        return tf_file

    @pytest.fixture
    def medium_terraform_file(self, tmp_path: Path) -> Path:
        """Create medium-sized Terraform file for benchmarking."""
        tf_content = "# Medium Terraform configuration\n\n"

        for i in range(20):
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

        tf_file = tmp_path / "medium.tf"
        tf_file.write_text(tf_content)
        return tf_file

    @pytest.fixture
    def large_terraform_file(self, tmp_path: Path) -> Path:
        """Create large Terraform file for benchmarking."""
        tf_content = "# Large Terraform configuration\n\n"

        for i in range(100):
            tf_content += f"""
resource "aws_instance" "instance_{i}" {{
  ami           = "ami-{i:08d}"
  instance_type = "t3.micro"

  root_block_device {{
    volume_size = {20 + (i % 10)}
    volume_type = "gp3"
    encrypted   = {"true" if i % 2 == 0 else "false"}
  }}

  tags = {{
    Name        = "instance-{i}"
    Environment = "{"production" if i % 3 == 0 else "staging" if i % 3 == 1 else "development"}"
    CostCenter  = "{1000 + (i % 5)}"
    Index       = "{i}"
  }}

  security_groups = ["sg-{i:08d}"]
}}
"""

        tf_file = tmp_path / "large.tf"
        tf_file.write_text(tf_content)
        return tf_file

    @pytest.fixture
    def simple_rules_file(self, tmp_path: Path) -> Path:
        """Create simple rules file for benchmarking."""
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
        return rules_file

    @pytest.fixture
    def complex_rules_file(self, tmp_path: Path) -> Path:
        """Create complex rules file for benchmarking."""
        rules_content = """
rules:
  - id: environment-required
    resource_type: aws_instance
    description: Instances must have Environment tag
    assert:
      tags:
        Environment: present

  - id: production-cost-center
    resource_type: aws_instance
    description: Production instances must have CostCenter
    filter:
      tags:
        Environment: production
    assert:
      tags:
        CostCenter: present

  - id: instance-type-check
    resource_type: aws_instance
    description: Instance type must be appropriate
    assert:
      instance_type:
        regex: "^(t3|m5)\\.(micro|small|medium)$"

  - id: encryption-required
    resource_type: aws_instance
    description: Root block device must be encrypted
    assert:
      root_block_device.encrypted: true

  - id: volume-size-limit
    resource_type: aws_instance
    description: Volume size must be reasonable
    assert:
      root_block_device.volume_size:
        lte: 100

  - id: security-groups-present
    resource_type: aws_instance
    description: Security groups must be specified
    assert:
      security_groups:
        length:
          gte: 1
"""
        rules_file = tmp_path / "complex_rules.yml"
        rules_file.write_text(rules_content)
        return rules_file

    @pytest.mark.performance
    def test_small_scan_performance(self, small_terraform_file: Path, simple_rules_file: Path):
        """Benchmark scan performance with small configuration."""
        results = []

        for _ in range(3):
            result = self.runner.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(small_terraform_file),
                    "--rules",
                    str(simple_rules_file),
                    "--output-format",
                    "json",
                ]
            )

            assert result["returncode"] in [0, 1]
            results.append(
                {
                    "wall_time": result["wall_time"],
                    "cpu_time": result["cpu_time"],
                    "memory": result["peak_memory"],
                }
            )

        avg_wall_time = sum(r["wall_time"] for r in results) / len(results)
        avg_memory = sum(r["memory"] for r in results) / len(results)

        # Performance assertions for small scan
        assert avg_wall_time < 5.0, f"Small scan too slow: {avg_wall_time:.3f}s"
        assert avg_memory < 150, f"Small scan uses too much memory: {avg_memory:.1f}MB"

        print(f"Small scan: {avg_wall_time:.3f}s, {avg_memory:.1f}MB")

    @pytest.mark.performance
    def test_medium_scan_performance(self, medium_terraform_file: Path, simple_rules_file: Path):
        """Benchmark scan performance with medium configuration."""
        result = self.runner.run_cli_command(
            [
                "scan",
                "--terraform",
                str(medium_terraform_file),
                "--rules",
                str(simple_rules_file),
                "--output-format",
                "json",
            ]
        )

        assert result["returncode"] in [0, 1]

        # Performance assertions for medium scan
        assert result["wall_time"] < 10.0, f"Medium scan too slow: {result['wall_time']:.3f}s"
        assert (
            result["peak_memory"] < 200
        ), f"Medium scan uses too much memory: {result['peak_memory']:.1f}MB"

        print(f"Medium scan: {result['wall_time']:.3f}s, {result['peak_memory']:.1f}MB")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_scan_performance(self, large_terraform_file: Path, complex_rules_file: Path):
        """Benchmark scan performance with large configuration."""
        result = self.runner.run_cli_command(
            [
                "scan",
                "--terraform",
                str(large_terraform_file),
                "--rules",
                str(complex_rules_file),
                "--output-format",
                "json",
            ]
        )

        assert result["returncode"] in [0, 1]

        # Performance assertions for large scan
        assert result["wall_time"] < 30.0, f"Large scan too slow: {result['wall_time']:.3f}s"
        assert (
            result["peak_memory"] < 500
        ), f"Large scan uses too much memory: {result['peak_memory']:.1f}MB"

        print(f"Large scan: {result['wall_time']:.3f}s, {result['peak_memory']:.1f}MB")

    @pytest.mark.performance
    def test_scan_output_format_performance(
        self, medium_terraform_file: Path, simple_rules_file: Path
    ):
        """Benchmark scan performance across different output formats."""
        formats = ["json", "table", "junit", "sarif"]
        results = {}

        for fmt in formats:
            result = self.runner.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(medium_terraform_file),
                    "--rules",
                    str(simple_rules_file),
                    "--output-format",
                    fmt,
                ]
            )

            assert result["returncode"] in [0, 1]
            results[fmt] = {"wall_time": result["wall_time"], "memory": result["peak_memory"]}

            # Each format should complete reasonably quickly
            assert result["wall_time"] < 15.0, f"Format {fmt} too slow: {result['wall_time']:.3f}s"

        # Print results for analysis
        for fmt, metrics in results.items():
            print(f"Format {fmt}: {metrics['wall_time']:.3f}s, {metrics['memory']:.1f}MB")

    @pytest.mark.performance
    def test_scan_rule_pack_performance(self, medium_terraform_file: Path):
        """Benchmark scan performance with built-in rule packs."""
        rule_packs = ["aws-security", "cis-aws"]

        for pack in rule_packs:
            result = self.runner.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(medium_terraform_file),
                    "--rule-pack",
                    pack,
                    "--output-format",
                    "json",
                ]
            )

            assert result["returncode"] in [0, 1]

            # Rule pack scans should be reasonably fast
            assert (
                result["wall_time"] < 20.0
            ), f"Rule pack {pack} too slow: {result['wall_time']:.3f}s"

            print(f"Rule pack {pack}: {result['wall_time']:.3f}s, {result['peak_memory']:.1f}MB")

    @pytest.mark.performance
    def test_scan_verbose_performance_impact(
        self, medium_terraform_file: Path, simple_rules_file: Path
    ):
        """Benchmark performance impact of verbose mode."""
        # Normal scan
        normal_result = self.runner.run_cli_command(
            [
                "scan",
                "--terraform",
                str(medium_terraform_file),
                "--rules",
                str(simple_rules_file),
                "--output-format",
                "json",
            ]
        )

        # Verbose scan
        verbose_result = self.runner.run_cli_command(
            [
                "scan",
                "--terraform",
                str(medium_terraform_file),
                "--rules",
                str(simple_rules_file),
                "--output-format",
                "json",
                "--verbose",
            ]
        )

        assert normal_result["returncode"] in [0, 1]
        assert verbose_result["returncode"] in [0, 1]

        # Verbose should not significantly impact performance
        time_overhead = verbose_result["wall_time"] - normal_result["wall_time"]
        memory_overhead = verbose_result["peak_memory"] - normal_result["peak_memory"]

        assert time_overhead < 2.0, f"Verbose mode adds too much time: {time_overhead:.3f}s"
        assert memory_overhead < 50, f"Verbose mode adds too much memory: {memory_overhead:.1f}MB"

        print(f"Verbose overhead: +{time_overhead:.3f}s, +{memory_overhead:.1f}MB")


class TestValidateRulePackPerformance:
    """Benchmark validate-rule-pack command performance."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = CLIBenchmarkRunner()

    @pytest.mark.performance
    def test_validate_rule_pack_performance(self):
        """Benchmark rule pack validation performance."""
        rule_packs = [
            "rule_packs/aws-security.yml",
            "rule_packs/cis-aws.yml",
            "rule_packs/gcp-security.yml",
        ]

        for pack in rule_packs:
            result = self.runner.run_cli_command(["validate-rule-pack", pack])

            # Should succeed or fail quickly
            assert result["returncode"] in [0, 1]
            assert (
                result["wall_time"] < 5.0
            ), f"Validation of {pack} too slow: {result['wall_time']:.3f}s"

            print(f"Validate {pack}: {result['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_validate_large_rule_pack_performance(self, tmp_path: Path):
        """Benchmark validation of large rule pack."""
        # Create large rule pack
        rules_content = "rules:\n"

        for i in range(200):  # 200 rules
            rules_content += f"""
  - id: rule-{i:03d}
    resource_type: aws_instance
    description: Test rule {i}
    assert:
      tags:
        Tag{i}: present
"""

        large_pack = tmp_path / "large_pack.yml"
        large_pack.write_text(rules_content)

        result = self.runner.run_cli_command(["validate-rule-pack", str(large_pack)])

        assert result["returncode"] in [0, 1]
        assert (
            result["wall_time"] < 10.0
        ), f"Large pack validation too slow: {result['wall_time']:.3f}s"

        print(f"Large pack validation: {result['wall_time']:.3f}s, {result['peak_memory']:.1f}MB")


class TestPerformanceRegression:
    """Performance regression tests."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = CLIBenchmarkRunner()

    @pytest.fixture
    def performance_baseline(self) -> Dict[str, float]:
        """Load performance baselines."""
        # These would typically be loaded from a file or database
        # For now, we'll use reasonable baseline values
        return {
            "help_startup_time": 2.0,  # seconds
            "version_startup_time": 1.5,  # seconds
            "list_packs_time": 3.0,  # seconds
            "small_scan_time": 5.0,  # seconds
            "medium_scan_time": 10.0,  # seconds
            "memory_usage_limit": 200,  # MB
        }

    @pytest.mark.performance
    def test_startup_time_regression(self, performance_baseline: Dict[str, float]):
        """Test for startup time regression."""
        commands = [
            (["--help"], "help_startup_time"),
            (["--version"], "version_startup_time"),
            (["list-rule-packs"], "list_packs_time"),
        ]

        for cmd, baseline_key in commands:
            result = self.runner.run_cli_command(cmd)
            assert result["returncode"] == 0

            baseline = performance_baseline[baseline_key]
            actual_time = result["wall_time"]

            # Allow 20% regression tolerance
            max_allowed = baseline * 1.2

            assert actual_time <= max_allowed, (
                f"Performance regression detected for {' '.join(cmd)}: "
                f"{actual_time:.3f}s > {max_allowed:.3f}s (baseline: {baseline:.3f}s)"
            )

            print(f"Command {' '.join(cmd)}: {actual_time:.3f}s (baseline: {baseline:.3f}s)")

    @pytest.mark.performance
    def test_memory_usage_regression(self, performance_baseline: Dict[str, float]):
        """Test for memory usage regression."""
        commands = [["--help"], ["--version"], ["list-rule-packs"]]

        baseline_memory = performance_baseline["memory_usage_limit"]

        for cmd in commands:
            result = self.runner.run_cli_command(cmd)
            assert result["returncode"] == 0

            actual_memory = result["peak_memory"]

            assert actual_memory <= baseline_memory, (
                f"Memory regression detected for {' '.join(cmd)}: "
                f"{actual_memory:.1f}MB > {baseline_memory:.1f}MB"
            )

            print(f"Command {' '.join(cmd)} memory: {actual_memory:.1f}MB")

    @pytest.mark.performance
    def test_scan_performance_regression(
        self, tmp_path: Path, performance_baseline: Dict[str, float]
    ):
        """Test for scan performance regression."""
        # Create test files
        small_tf = tmp_path / "small.tf"
        small_tf.write_text(
            """
resource "aws_instance" "test" {
  ami = "ami-12345"
  instance_type = "t3.micro"
  tags = { Environment = "test" }
}
"""
        )

        simple_rules = tmp_path / "rules.yml"
        simple_rules.write_text(
            """
rules:
  - id: env-required
    resource_type: aws_instance
    assert:
      tags:
        Environment: present
"""
        )

        result = self.runner.run_cli_command(
            [
                "scan",
                "--terraform",
                str(small_tf),
                "--rules",
                str(simple_rules),
                "--output-format",
                "json",
            ]
        )

        assert result["returncode"] in [0, 1]

        baseline_time = performance_baseline["small_scan_time"]
        actual_time = result["wall_time"]
        max_allowed = baseline_time * 1.2

        assert (
            actual_time <= max_allowed
        ), f"Scan performance regression: {actual_time:.3f}s > {max_allowed:.3f}s"

        print(f"Small scan: {actual_time:.3f}s (baseline: {baseline_time:.3f}s)")

    @pytest.mark.performance
    def test_concurrent_execution_performance(self, tmp_path: Path):
        """Test performance under concurrent execution."""
        # Create test file
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

        import concurrent.futures
        import threading

        def run_scan():
            return self.runner.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(tf_file),
                    "--rule-pack",
                    "aws-security",
                    "--output-format",
                    "json",
                ]
            )

        # Run multiple scans concurrently
        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_scan) for _ in range(3)]
            results = [future.result() for future in futures]

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # All should succeed
        for result in results:
            assert result["returncode"] in [0, 1]

        # Concurrent execution should not take much longer than sequential
        # (allowing for some overhead)
        max_expected_time = 15.0  # seconds
        assert total_time < max_expected_time, f"Concurrent execution too slow: {total_time:.3f}s"

        print(f"Concurrent execution (3 threads): {total_time:.3f}s")


class TestPerformanceMonitoring:
    """Tests for performance monitoring and profiling."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = CLIBenchmarkRunner()

    @pytest.mark.performance
    def test_performance_metrics_collection(self, tmp_path: Path):
        """Test that performance metrics can be collected."""
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

        result = self.runner.run_cli_command(
            [
                "scan",
                "--terraform",
                str(tf_file),
                "--rule-pack",
                "aws-security",
                "--output-format",
                "json",
            ]
        )

        assert result["returncode"] in [0, 1]

        # Verify we collected metrics
        assert "wall_time" in result
        assert "cpu_time" in result
        assert "memory_usage" in result
        assert "peak_memory" in result

        # Metrics should be reasonable
        assert result["wall_time"] > 0
        assert result["cpu_time"] >= 0
        assert result["peak_memory"] > 0

        print(
            f"Metrics: wall={result['wall_time']:.3f}s, cpu={result['cpu_time']:.3f}s, mem={result['peak_memory']:.1f}MB"
        )

    @pytest.mark.performance
    def test_performance_data_export(self, tmp_path: Path):
        """Test exporting performance data for analysis."""
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

        # Run multiple tests and collect data
        performance_data = []

        for i in range(3):
            result = self.runner.run_cli_command(
                [
                    "scan",
                    "--terraform",
                    str(tf_file),
                    "--rule-pack",
                    "aws-security",
                    "--output-format",
                    "json",
                ]
            )

            performance_data.append(
                {
                    "run": i + 1,
                    "wall_time": result["wall_time"],
                    "cpu_time": result["cpu_time"],
                    "memory": result["peak_memory"],
                    "returncode": result["returncode"],
                }
            )

        # Export to JSON for analysis
        perf_file = tmp_path / "performance_data.json"
        with open(perf_file, "w") as f:
            json.dump(performance_data, f, indent=2)

        assert perf_file.exists()

        # Verify data consistency
        wall_times = [d["wall_time"] for d in performance_data]
        avg_time = sum(wall_times) / len(wall_times)
        max_deviation = max(abs(t - avg_time) for t in wall_times)

        # Times should be relatively consistent (within 50% of average)
        assert (
            max_deviation < avg_time * 0.5
        ), f"Performance too inconsistent: {max_deviation:.3f}s deviation"

        print(f"Performance consistency: avg={avg_time:.3f}s, max_dev={max_deviation:.3f}s")
