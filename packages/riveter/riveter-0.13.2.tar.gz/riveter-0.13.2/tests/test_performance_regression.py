"""Performance regression tests.

These tests ensure that performance characteristics are maintained
or improved during modernization.
"""

import time

import pytest

from .utils.fixtures import FixtureManager
from .utils.performance import PerformanceTester


@pytest.fixture(scope="module")
def performance_tester():
    """Initialize performance tester."""
    return PerformanceTester()


@pytest.fixture(scope="module")
def fixture_manager():
    """Initialize fixture manager."""
    return FixtureManager()


@pytest.mark.performance
class TestCLIPerformance:
    """Test CLI performance characteristics."""

    def test_cli_startup_time(self, performance_tester, benchmark_timer):
        """Test that CLI startup time meets performance requirements."""
        # Measure startup time
        startup_time = performance_tester.measure_cli_startup_time()

        # Record metric
        performance_tester.record_metric("cli_startup_time", startup_time)

        # Check for regression
        is_ok, message = performance_tester.check_regression("cli_startup_time", startup_time)

        # Log the result
        # Log the result to stderr for debugging
        import sys

        sys.stderr.write(f"CLI startup time: {startup_time:.3f}s - {message}\n")

        # Assert no regression
        assert is_ok, f"CLI startup time regression: {message}"

    @pytest.mark.slow
    def test_config_parsing_performance(self, performance_tester, fixture_manager):
        """Test Terraform configuration parsing performance."""
        try:
            # Test with simple configuration
            simple_tf = fixture_manager.get_terraform_fixture("simple")
            parse_time = performance_tester.measure_config_parse_time(simple_tf)

            # Record metric
            performance_tester.record_metric("config_parse_time_simple", parse_time)

            # Check for regression
            is_ok, message = performance_tester.check_regression("config_parse_time", parse_time)

            print(f"Config parsing time (simple): {parse_time:.3f}s - {message}")

            # Allow some flexibility for parsing time
            assert parse_time < 5.0, f"Config parsing too slow: {parse_time:.3f}s"

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")

    @pytest.mark.slow
    def test_scan_performance_simple(self, performance_tester, fixture_manager):
        """Test scan performance with simple configuration."""
        try:
            terraform_file = fixture_manager.get_terraform_fixture("simple")
            rules_file = fixture_manager.get_rules_fixture("basic_rules")

            scan_time = performance_tester.measure_scan_time(terraform_file, rules_file)

            # Record metric
            performance_tester.record_metric("scan_simple_config", scan_time)

            # Check for regression
            is_ok, message = performance_tester.check_regression("scan_simple_config", scan_time)

            print(f"Scan time (simple): {scan_time:.3f}s - {message}")

            # Assert reasonable performance
            assert scan_time < 10.0, f"Simple scan too slow: {scan_time:.3f}s"

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")

    @pytest.mark.slow
    def test_scan_performance_complex(self, performance_tester, fixture_manager):
        """Test scan performance with complex configuration."""
        try:
            terraform_file = fixture_manager.get_terraform_fixture("complex")
            rules_file = fixture_manager.get_rules_fixture("advanced_rules")

            scan_time = performance_tester.measure_scan_time(terraform_file, rules_file)

            # Record metric
            performance_tester.record_metric("scan_complex_config", scan_time)

            # Check for regression
            is_ok, message = performance_tester.check_regression("scan_complex_config", scan_time)

            print(f"Scan time (complex): {scan_time:.3f}s - {message}")

            # Assert reasonable performance for complex scenarios
            assert scan_time < 30.0, f"Complex scan too slow: {scan_time:.3f}s"

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage characteristics."""

    @pytest.mark.slow
    def test_memory_usage_simple_scan(self, performance_tester, fixture_manager):
        """Test memory usage during simple scan."""
        try:
            terraform_file = fixture_manager.get_terraform_fixture("simple")
            rules_file = fixture_manager.get_rules_fixture("basic_rules")

            command = ["riveter", "scan", str(terraform_file), "--rules", str(rules_file)]
            memory_usage = performance_tester.measure_memory_usage(command)

            if memory_usage > 0:  # Only test if psutil is available
                # Record metric
                performance_tester.record_metric("memory_usage_simple", memory_usage, "MB")

                print(f"Memory usage (simple scan): {memory_usage:.1f}MB")

                # Assert reasonable memory usage
                assert memory_usage < 500, f"Memory usage too high: {memory_usage:.1f}MB"
            else:
                pytest.skip("Memory profiling not available (psutil not installed)")

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")


@pytest.mark.performance
class TestScalabilityCharacteristics:
    """Test scalability and performance under load."""

    @pytest.mark.slow
    def test_multiple_rule_packs_performance(self, performance_tester, fixture_manager):
        """Test performance when using multiple rule packs."""
        try:
            terraform_file = fixture_manager.get_terraform_fixture("simple")

            # Test with multiple rule packs
            rule_packs = []
            for pack_name in fixture_manager.list_rule_pack_fixtures()[:3]:  # Use first 3 packs
                try:
                    pack_file = fixture_manager.get_rule_pack_fixture(pack_name)
                    rule_packs.append(str(pack_file))
                except FileNotFoundError:
                    continue

            if rule_packs:
                command = ["riveter", "scan", str(terraform_file)]
                for pack in rule_packs:
                    command.extend(["--rule-pack", pack])

                start_time = time.perf_counter()
                import subprocess

                result = subprocess.run(
                    command, capture_output=True, text=True, timeout=60, check=False
                )
                end_time = time.perf_counter()

                scan_time = end_time - start_time

                print(f"Multi-pack scan time: {scan_time:.3f}s ({len(rule_packs)} packs)")

                # Should complete in reasonable time even with multiple packs
                assert scan_time < 20.0, f"Multi-pack scan too slow: {scan_time:.3f}s"
            else:
                pytest.skip("No rule pack fixtures available")

        except FileNotFoundError as e:
            pytest.skip(f"Test fixture not available: {e}")
        except subprocess.TimeoutExpired:
            pytest.fail("Multi-pack scan timed out")


@pytest.mark.performance
@pytest.mark.slow
def test_comprehensive_performance_suite(performance_tester, fixture_manager):
    """Run comprehensive performance test suite."""
    test_data_dir = fixture_manager.fixtures_dir
    results = performance_tester.run_performance_suite(test_data_dir)

    # Generate and print report
    report = performance_tester.generate_performance_report(results)
    print("\n" + report)

    # Assert no critical regressions
    critical_regressions = [r for r in results["regressions"] if "regression" in r["message"]]

    if critical_regressions:
        regression_details = "\n".join(
            [f"  - {r['metric']}: {r['message']}" for r in critical_regressions]
        )
        pytest.fail(f"Critical performance regressions detected:\n{regression_details}")


@pytest.mark.performance
def test_performance_baseline_update(performance_tester, tmp_path):
    """Test updating performance baseline."""
    # Create mock results
    mock_results = {
        "timestamp": time.time(),
        "metrics": {"cli_startup_time": 1.5, "config_parse_time": 0.3, "scan_simple_config": 2.0},
    }

    # Save as baseline
    baseline_file = tmp_path / "test_baseline.json"
    performance_tester.save_results_as_baseline(mock_results, baseline_file)

    # Verify baseline file was created
    assert baseline_file.exists()

    # Load and verify content
    import json

    with open(baseline_file) as f:
        baseline_data = json.load(f)

    assert "metrics" in baseline_data
    assert "cli_startup_time" in baseline_data["metrics"]
    assert baseline_data["metrics"]["cli_startup_time"]["value"] == 1.5


@pytest.mark.performance
class TestPerformanceUtilities:
    """Test performance testing utilities."""

    def test_metric_recording(self, performance_tester):
        """Test metric recording functionality."""
        performance_tester.record_metric("test_metric", 1.23, "seconds")

        assert "test_metric" in performance_tester.current_metrics
        assert performance_tester.current_metrics["test_metric"]["value"] == 1.23
        assert performance_tester.current_metrics["test_metric"]["unit"] == "seconds"

    def test_regression_detection(self, performance_tester):
        """Test regression detection logic."""
        # Test with no baseline (should pass)
        is_ok, message = performance_tester.check_regression("nonexistent_metric", 1.0)
        assert is_ok
        assert "No baseline" in message

        # Test with existing baseline (if available)
        baseline_metrics = performance_tester.baseline_data.get("metrics", {})
        if "cli_startup_time" in baseline_metrics:
            baseline_value = baseline_metrics["cli_startup_time"]["value"]

            # Test improvement
            is_ok, message = performance_tester.check_regression(
                "cli_startup_time", baseline_value * 0.8
            )
            assert is_ok
            assert "improvement" in message.lower()

            # Test regression
            is_ok, message = performance_tester.check_regression(
                "cli_startup_time", baseline_value * 2.0
            )
            assert not is_ok
            assert "regression" in message.lower()
