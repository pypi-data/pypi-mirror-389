"""Performance testing and regression detection utilities."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest


class PerformanceTester:
    """Test performance and detect regressions."""

    def __init__(self, baseline_file: Path | None = None):
        """Initialize with performance baseline data."""
        if baseline_file is None:
            baseline_file = Path(__file__).parent.parent / "fixtures" / "performance_baseline.json"

        self.baseline_file = baseline_file
        self.baseline_data = self._load_baseline()
        self.current_metrics = {}

    def _load_baseline(self) -> dict[str, Any]:
        """Load performance baseline data."""
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                return json.load(f)
        return {"metrics": {}}

    def measure_cli_startup_time(self, command: list[str] = None) -> float:
        """Measure CLI startup time."""
        if command is None:
            command = ["riveter", "--help"]

        start_time = time.perf_counter()
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=10, check=False
            )
            end_time = time.perf_counter()

            if result.returncode == 0:
                return end_time - start_time
            raise RuntimeError(f"Command failed with exit code {result.returncode}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Command timed out")

    def measure_config_parse_time(self, terraform_file: Path) -> float:
        """Measure Terraform configuration parsing time."""
        command = ["riveter", "scan", str(terraform_file), "--dry-run"]

        start_time = time.perf_counter()
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=30, check=False
            )
            end_time = time.perf_counter()

            # Even if validation fails, parsing should succeed
            return end_time - start_time

        except subprocess.TimeoutExpired:
            raise RuntimeError("Config parsing timed out")

    def measure_scan_time(self, terraform_file: Path, rules_file: Path | None = None) -> float:
        """Measure end-to-end scan time."""
        command = ["riveter", "scan", str(terraform_file)]
        if rules_file:
            command.extend(["--rules", str(rules_file)])

        start_time = time.perf_counter()
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=60, check=False
            )
            end_time = time.perf_counter()

            return end_time - start_time

        except subprocess.TimeoutExpired:
            raise RuntimeError("Scan timed out")

    def measure_memory_usage(self, command: list[str]) -> float:
        """Measure peak memory usage during command execution."""
        try:
            import psutil

            # Start the process
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Monitor memory usage
            ps_process = psutil.Process(process.pid)
            peak_memory = 0

            while process.poll() is None:
                try:
                    memory_info = ps_process.memory_info()
                    current_memory = memory_info.rss / 1024 / 1024  # Convert to MB
                    peak_memory = max(peak_memory, current_memory)
                    time.sleep(0.1)  # Sample every 100ms
                except psutil.NoSuchProcess:
                    break

            # Wait for process to complete
            process.wait()

            return peak_memory

        except ImportError:
            # psutil not available, return 0
            return 0.0

    def record_metric(self, metric_name: str, value: float, unit: str = "seconds"):
        """Record a performance metric."""
        self.current_metrics[metric_name] = {"value": value, "unit": unit, "timestamp": time.time()}

    def check_regression(self, metric_name: str, current_value: float) -> tuple[bool, str]:
        """Check if a metric shows performance regression."""
        baseline_metrics = self.baseline_data.get("metrics", {})

        if metric_name not in baseline_metrics:
            return True, f"No baseline for metric '{metric_name}'"

        baseline_metric = baseline_metrics[metric_name]
        baseline_value = baseline_metric["value"]
        tolerance = baseline_metric.get("tolerance", 1.2)  # 20% tolerance by default

        threshold = baseline_value * tolerance

        if current_value <= threshold:
            improvement = ((baseline_value - current_value) / baseline_value) * 100
            return (
                True,
                f"Performance maintained (baseline: {baseline_value}, current: {current_value}, improvement: {improvement:.1f}%)",
            )
        regression = ((current_value - baseline_value) / baseline_value) * 100
        return (
            False,
            f"Performance regression detected (baseline: {baseline_value}, current: {current_value}, regression: {regression:.1f}%)",
        )

    def run_performance_suite(self, test_data_dir: Path) -> dict[str, Any]:
        """Run comprehensive performance test suite."""
        results = {"timestamp": time.time(), "metrics": {}, "regressions": [], "improvements": []}

        # Test CLI startup time
        try:
            startup_time = self.measure_cli_startup_time()
            results["metrics"]["cli_startup_time"] = startup_time

            is_ok, message = self.check_regression("cli_startup_time", startup_time)
            if not is_ok:
                results["regressions"].append({"metric": "cli_startup_time", "message": message})
            elif "improvement" in message:
                results["improvements"].append({"metric": "cli_startup_time", "message": message})
        except Exception as e:
            results["metrics"]["cli_startup_time"] = f"Error: {e!s}"

        # Test configuration parsing
        simple_tf = test_data_dir / "terraform" / "simple.tf"
        if simple_tf.exists():
            try:
                parse_time = self.measure_config_parse_time(simple_tf)
                results["metrics"]["config_parse_time"] = parse_time

                is_ok, message = self.check_regression("config_parse_time", parse_time)
                if not is_ok:
                    results["regressions"].append(
                        {"metric": "config_parse_time", "message": message}
                    )
                elif "improvement" in message:
                    results["improvements"].append(
                        {"metric": "config_parse_time", "message": message}
                    )
            except Exception as e:
                results["metrics"]["config_parse_time"] = f"Error: {e!s}"

        # Test scan performance
        test_configs = self.baseline_data.get("test_configurations", {})
        for config_name, config_info in test_configs.items():
            tf_file = test_data_dir / "terraform" / config_info["terraform_file"]
            rules_file = test_data_dir / "rules" / config_info["rules_file"]

            if tf_file.exists() and rules_file.exists():
                try:
                    scan_time = self.measure_scan_time(tf_file, rules_file)
                    metric_name = f"scan_{config_name}_config"
                    results["metrics"][metric_name] = scan_time

                    is_ok, message = self.check_regression(metric_name, scan_time)
                    if not is_ok:
                        results["regressions"].append({"metric": metric_name, "message": message})
                    elif "improvement" in message:
                        results["improvements"].append({"metric": metric_name, "message": message})
                except Exception as e:
                    results["metrics"][f"scan_{config_name}_config"] = f"Error: {e!s}"

        return results

    def generate_performance_report(self, results: dict[str, Any]) -> str:
        """Generate a human-readable performance report."""
        report_lines = [
            "Performance Test Report",
            "=" * 50,
            f"Test run at: {time.ctime(results['timestamp'])}",
            "",
        ]

        # Metrics summary
        report_lines.append("Metrics:")
        for metric_name, value in results["metrics"].items():
            if isinstance(value, (int, float)):
                report_lines.append(f"  {metric_name}: {value:.3f}s")
            else:
                report_lines.append(f"  {metric_name}: {value}")

        report_lines.append("")

        # Regressions
        if results["regressions"]:
            report_lines.append("Performance Regressions:")
            for regression in results["regressions"]:
                report_lines.append(f"  ❌ {regression['metric']}: {regression['message']}")
        else:
            report_lines.append("✅ No performance regressions detected")

        report_lines.append("")

        # Improvements
        if results["improvements"]:
            report_lines.append("Performance Improvements:")
            for improvement in results["improvements"]:
                report_lines.append(f"  ✅ {improvement['metric']}: {improvement['message']}")

        return "\n".join(report_lines)

    def save_results_as_baseline(self, results: dict[str, Any], output_file: Path | None = None):
        """Save current results as new baseline."""
        if output_file is None:
            output_file = self.baseline_file

        baseline_data = {
            "version": "current",
            "baseline_date": time.strftime("%Y-%m-%d"),
            "metrics": {},
        }

        for metric_name, value in results["metrics"].items():
            if isinstance(value, (int, float)):
                baseline_data["metrics"][metric_name] = {
                    "value": value,
                    "unit": "seconds",
                    "tolerance": 1.2,
                }

        with open(output_file, "w") as f:
            json.dump(baseline_data, f, indent=2)

    @pytest.fixture
    def performance_regression_check(self):
        """Pytest fixture for performance regression checking."""

        def check_performance(metric_name: str, measured_value: float) -> None:
            is_ok, message = self.check_regression(metric_name, measured_value)
            if not is_ok:
                pytest.fail(f"Performance regression in {metric_name}: {message}")

        return check_performance
