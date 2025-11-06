"""Performance benchmarks for individual components."""

import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

from riveter.models.core import Severity, TerraformResource, ValidationSummary
from riveter.models.rules import Rule, RuleCondition
from riveter.validation.engine import ValidationContext, ValidationEngine


class ComponentBenchmarkRunner:
    """Utility class for running component benchmarks."""

    def __init__(self):
        self.metrics = {}

    def time_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Time an operation and store metrics."""
        start_time = time.perf_counter()
        start_cpu = time.process_time()

        result = operation_func(*args, **kwargs)

        end_time = time.perf_counter()
        end_cpu = time.process_time()

        self.metrics[operation_name] = {
            "wall_time": end_time - start_time,
            "cpu_time": end_cpu - start_cpu,
            "result": result,
        }

        return result

    def get_metrics(self, operation_name: str) -> Dict[str, float]:
        """Get metrics for an operation."""
        return self.metrics.get(operation_name, {})


class TestResourceProcessingPerformance:
    """Benchmark resource processing performance."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = ComponentBenchmarkRunner()

    def create_test_resources(self, count: int) -> List[TerraformResource]:
        """Create test resources for benchmarking."""
        resources = []

        for i in range(count):
            resource = TerraformResource(
                type="aws_instance",
                name=f"instance_{i}",
                attributes={
                    "ami": f"ami-{i:08d}",
                    "instance_type": "t3.micro",
                    "tags": {
                        "Name": f"instance-{i}",
                        "Environment": "production" if i % 2 == 0 else "staging",
                        "Index": str(i),
                        "CostCenter": str(1000 + (i % 5)),
                    },
                    "security_groups": [f"sg-{i:08d}"],
                    "root_block_device": {
                        "volume_size": 20 + (i % 10),
                        "volume_type": "gp3",
                        "encrypted": i % 2 == 0,
                    },
                },
            )
            resources.append(resource)

        return resources

    @pytest.mark.performance
    def test_resource_creation_performance(self):
        """Benchmark resource creation performance."""

        def create_resources():
            return self.create_test_resources(1000)

        resources = self.runner.time_operation("resource_creation", create_resources)
        metrics = self.runner.get_metrics("resource_creation")

        assert len(resources) == 1000
        assert (
            metrics["wall_time"] < 1.0
        ), f"Resource creation too slow: {metrics['wall_time']:.3f}s"

        print(f"Created 1000 resources in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_resource_attribute_access_performance(self):
        """Benchmark resource attribute access performance."""
        resources = self.create_test_resources(100)

        def access_attributes():
            results = []
            for resource in resources:
                # Test various attribute access patterns
                results.append(resource.get_attribute("tags.Environment"))
                results.append(resource.get_attribute("instance_type"))
                results.append(resource.get_attribute("root_block_device.volume_size"))
                results.append(resource.has_attribute("tags.CostCenter"))
            return results

        results = self.runner.time_operation("attribute_access", access_attributes)
        metrics = self.runner.get_metrics("attribute_access")

        assert len(results) == 400  # 4 operations per resource
        assert metrics["wall_time"] < 0.1, f"Attribute access too slow: {metrics['wall_time']:.3f}s"

        print(f"Accessed 400 attributes in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_resource_serialization_performance(self):
        """Benchmark resource serialization performance."""
        resources = self.create_test_resources(100)

        def serialize_resources():
            return [resource.to_dict() for resource in resources]

        serialized = self.runner.time_operation("serialization", serialize_resources)
        metrics = self.runner.get_metrics("serialization")

        assert len(serialized) == 100
        assert metrics["wall_time"] < 0.5, f"Serialization too slow: {metrics['wall_time']:.3f}s"

        print(f"Serialized 100 resources in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_resource_filtering_performance(self):
        """Benchmark resource filtering performance."""
        resources = self.create_test_resources(1000)

        def filter_resources():
            # Filter by environment
            production_resources = [
                r for r in resources if r.get_attribute("tags.Environment") == "production"
            ]

            # Filter by instance type
            micro_instances = [
                r for r in resources if r.get_attribute("instance_type") == "t3.micro"
            ]

            return production_resources, micro_instances

        filtered = self.runner.time_operation("filtering", filter_resources)
        metrics = self.runner.get_metrics("filtering")

        production_resources, micro_instances = filtered
        assert len(production_resources) == 500  # Half should be production
        assert len(micro_instances) == 1000  # All should be t3.micro
        assert metrics["wall_time"] < 0.5, f"Filtering too slow: {metrics['wall_time']:.3f}s"

        print(f"Filtered 1000 resources in {metrics['wall_time']:.3f}s")


class TestRuleProcessingPerformance:
    """Benchmark rule processing performance."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = ComponentBenchmarkRunner()

    def create_test_rules(self, count: int) -> List[Rule]:
        """Create test rules for benchmarking."""
        rules = []

        for i in range(count):
            conditions = [
                RuleCondition("tags.Environment", "present", None),
                RuleCondition("instance_type", "equals", "t3.micro"),
                RuleCondition("tags.CostCenter", "present", None),
            ]

            rule = Rule(
                id=f"rule-{i:03d}",
                resource_type="aws_instance",
                description=f"Test rule {i}",
                conditions=conditions,
                severity=Severity.ERROR if i % 3 == 0 else Severity.WARNING,
            )
            rules.append(rule)

        return rules

    @pytest.mark.performance
    def test_rule_creation_performance(self):
        """Benchmark rule creation performance."""

        def create_rules():
            return self.create_test_rules(500)

        rules = self.runner.time_operation("rule_creation", create_rules)
        metrics = self.runner.get_metrics("rule_creation")

        assert len(rules) == 500
        assert metrics["wall_time"] < 1.0, f"Rule creation too slow: {metrics['wall_time']:.3f}s"

        print(f"Created 500 rules in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_rule_resource_matching_performance(self):
        """Benchmark rule-resource matching performance."""
        rules = self.create_test_rules(50)

        # Create resources of different types
        resources = []
        for i in range(100):
            resource_type = ["aws_instance", "aws_s3_bucket", "aws_rds_instance"][i % 3]
            resources.append(
                TerraformResource(
                    type=resource_type,
                    name=f"resource_{i}",
                    attributes={"tags": {"Environment": "production"}},
                )
            )

        def match_rules_to_resources():
            matches = []
            for rule in rules:
                for resource in resources:
                    if rule.matches_resource_type(resource):
                        matches.append((rule, resource))
            return matches

        matches = self.runner.time_operation("rule_matching", match_rules_to_resources)
        metrics = self.runner.get_metrics("rule_matching")

        # Should have matches for aws_instance resources only
        expected_matches = 50 * (100 // 3)  # 50 rules * ~33 aws_instance resources
        assert len(matches) >= expected_matches - 50  # Allow some variance
        assert metrics["wall_time"] < 0.5, f"Rule matching too slow: {metrics['wall_time']:.3f}s"

        print(f"Matched {len(matches)} rule-resource pairs in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_rule_serialization_performance(self):
        """Benchmark rule serialization performance."""
        rules = self.create_test_rules(100)

        def serialize_rules():
            return [rule.to_dict() for rule in rules]

        serialized = self.runner.time_operation("rule_serialization", serialize_rules)
        metrics = self.runner.get_metrics("rule_serialization")

        assert len(serialized) == 100
        assert (
            metrics["wall_time"] < 0.5
        ), f"Rule serialization too slow: {metrics['wall_time']:.3f}s"

        print(f"Serialized 100 rules in {metrics['wall_time']:.3f}s")


class TestValidationEnginePerformance:
    """Benchmark validation engine performance."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = ComponentBenchmarkRunner()

    def create_mock_evaluator(self):
        """Create a mock evaluator for benchmarking."""
        evaluator = Mock()

        def mock_evaluate(rule, resource):
            from riveter.models.core import RuleResult

            # Simulate some processing time
            time.sleep(0.001)  # 1ms per evaluation

            return RuleResult(
                rule_id=rule.id,
                resource=resource,
                status=True,
                message="Mock evaluation",
                severity=rule.severity,
                assertion_results=[],
            )

        evaluator.evaluate.side_effect = mock_evaluate
        return evaluator

    @pytest.mark.performance
    def test_validation_engine_small_scale(self):
        """Benchmark validation engine with small dataset."""
        evaluator = self.create_mock_evaluator()
        engine = ValidationEngine(evaluator)

        # Create small dataset
        resources = [
            TerraformResource("aws_instance", f"instance_{i}", {"tags": {"Environment": "prod"}})
            for i in range(10)
        ]

        rules = [
            Rule(
                f"rule_{i}",
                "aws_instance",
                f"Rule {i}",
                [RuleCondition("tags.Environment", "present", None)],
            )
            for i in range(5)
        ]

        context = ValidationContext(resources, rules, {}, {})

        def run_validation():
            return engine.validate(context)

        result = self.runner.time_operation("small_validation", run_validation)
        metrics = self.runner.get_metrics("small_validation")

        assert len(result.rule_results) == 50  # 10 resources * 5 rules
        assert metrics["wall_time"] < 2.0, f"Small validation too slow: {metrics['wall_time']:.3f}s"

        print(f"Small validation (50 evaluations) in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_validation_engine_medium_scale(self):
        """Benchmark validation engine with medium dataset."""
        evaluator = self.create_mock_evaluator()
        engine = ValidationEngine(evaluator)

        # Create medium dataset
        resources = [
            TerraformResource("aws_instance", f"instance_{i}", {"tags": {"Environment": "prod"}})
            for i in range(50)
        ]

        rules = [
            Rule(
                f"rule_{i}",
                "aws_instance",
                f"Rule {i}",
                [RuleCondition("tags.Environment", "present", None)],
            )
            for i in range(20)
        ]

        context = ValidationContext(resources, rules, {}, {})

        def run_validation():
            return engine.validate(context)

        result = self.runner.time_operation("medium_validation", run_validation)
        metrics = self.runner.get_metrics("medium_validation")

        assert len(result.rule_results) == 1000  # 50 resources * 20 rules
        assert (
            metrics["wall_time"] < 10.0
        ), f"Medium validation too slow: {metrics['wall_time']:.3f}s"

        print(f"Medium validation (1000 evaluations) in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_validation_engine_large_scale(self):
        """Benchmark validation engine with large dataset."""
        evaluator = self.create_mock_evaluator()
        engine = ValidationEngine(evaluator)

        # Create large dataset
        resources = [
            TerraformResource("aws_instance", f"instance_{i}", {"tags": {"Environment": "prod"}})
            for i in range(200)
        ]

        rules = [
            Rule(
                f"rule_{i}",
                "aws_instance",
                f"Rule {i}",
                [RuleCondition("tags.Environment", "present", None)],
            )
            for i in range(50)
        ]

        context = ValidationContext(resources, rules, {}, {})

        def run_validation():
            return engine.validate(context)

        result = self.runner.time_operation("large_validation", run_validation)
        metrics = self.runner.get_metrics("large_validation")

        assert len(result.rule_results) == 10000  # 200 resources * 50 rules
        assert (
            metrics["wall_time"] < 60.0
        ), f"Large validation too slow: {metrics['wall_time']:.3f}s"

        print(f"Large validation (10000 evaluations) in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_validation_context_creation_performance(self):
        """Benchmark validation context creation performance."""
        # Create large datasets
        resources = [
            TerraformResource("aws_instance", f"instance_{i}", {"tags": {"Environment": "prod"}})
            for i in range(1000)
        ]

        rules = [
            Rule(
                f"rule_{i}",
                "aws_instance",
                f"Rule {i}",
                [RuleCondition("tags.Environment", "present", None)],
            )
            for i in range(100)
        ]

        def create_context():
            return ValidationContext(resources, rules, {}, {})

        context = self.runner.time_operation("context_creation", create_context)
        metrics = self.runner.get_metrics("context_creation")

        assert len(context.resources) == 1000
        assert len(context.rules) == 100
        assert metrics["wall_time"] < 1.0, f"Context creation too slow: {metrics['wall_time']:.3f}s"

        print(f"Created validation context in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_validation_summary_calculation_performance(self):
        """Benchmark validation summary calculation performance."""
        from riveter.models.core import RuleResult

        # Create large result set
        rule_results = []
        for i in range(10000):
            result = RuleResult(
                rule_id=f"rule_{i % 100}",
                resource=TerraformResource("aws_instance", f"instance_{i % 1000}", {}),
                status=i % 3 != 0,  # 2/3 pass, 1/3 fail
                message="Test result",
                severity=Severity.ERROR if i % 3 == 0 else Severity.INFO,
                assertion_results=[],
            )
            rule_results.append(result)

        def calculate_summary():
            passed_rules = sum(1 for r in rule_results if r.status)
            failed_rules = sum(1 for r in rule_results if not r.status)
            error_count = sum(1 for r in rule_results if r.severity == Severity.ERROR)
            info_count = sum(1 for r in rule_results if r.severity == Severity.INFO)

            return ValidationSummary(
                total_rules=100,
                total_resources=1000,
                passed_rules=passed_rules,
                failed_rules=failed_rules,
                skipped_rules=0,
                total_assertions=len(rule_results),
                passed_assertions=passed_rules,
                failed_assertions=failed_rules,
                execution_time=1.0,
                error_count=error_count,
                warning_count=0,
                info_count=info_count,
            )

        summary = self.runner.time_operation("summary_calculation", calculate_summary)
        metrics = self.runner.get_metrics("summary_calculation")

        assert summary.total_assertions == 10000
        assert (
            metrics["wall_time"] < 0.5
        ), f"Summary calculation too slow: {metrics['wall_time']:.3f}s"

        print(f"Calculated summary for 10000 results in {metrics['wall_time']:.3f}s")


class TestMemoryUsagePerformance:
    """Benchmark memory usage of components."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = ComponentBenchmarkRunner()

    def get_memory_usage(self):
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0  # Skip if psutil not available

    @pytest.mark.performance
    def test_resource_memory_usage(self):
        """Benchmark memory usage of resource creation."""
        initial_memory = self.get_memory_usage()

        # Create large number of resources
        resources = []
        for i in range(10000):
            resource = TerraformResource(
                type="aws_instance",
                name=f"instance_{i}",
                attributes={
                    "ami": f"ami-{i:08d}",
                    "instance_type": "t3.micro",
                    "tags": {f"Tag{j}": f"Value{j}" for j in range(10)},  # 10 tags each
                    "complex_data": {
                        "nested": {"deep": {"value": f"data_{i}"}},
                        "list": [f"item_{j}" for j in range(5)],
                    },
                },
            )
            resources.append(resource)

        final_memory = self.get_memory_usage()
        memory_used = final_memory - initial_memory

        if memory_used > 0:  # Only check if we can measure memory
            memory_per_resource = memory_used / len(resources)

            assert memory_used < 500, f"Too much memory used: {memory_used:.1f}MB"
            assert (
                memory_per_resource < 0.1
            ), f"Too much memory per resource: {memory_per_resource:.3f}MB"

            print(
                f"Created {len(resources)} resources using {memory_used:.1f}MB ({memory_per_resource:.3f}MB per resource)"
            )

    @pytest.mark.performance
    def test_rule_memory_usage(self):
        """Benchmark memory usage of rule creation."""
        initial_memory = self.get_memory_usage()

        # Create large number of rules
        rules = []
        for i in range(5000):
            conditions = [
                RuleCondition(f"tags.Tag{j}", "present", None)
                for j in range(5)  # 5 conditions each
            ]

            rule = Rule(
                id=f"rule-{i:04d}",
                resource_type="aws_instance",
                description=f"Complex test rule {i} with detailed description and metadata",
                conditions=conditions,
                severity=Severity.ERROR,
            )
            rules.append(rule)

        final_memory = self.get_memory_usage()
        memory_used = final_memory - initial_memory

        if memory_used > 0:  # Only check if we can measure memory
            memory_per_rule = memory_used / len(rules)

            assert memory_used < 200, f"Too much memory used: {memory_used:.1f}MB"
            assert memory_per_rule < 0.05, f"Too much memory per rule: {memory_per_rule:.3f}MB"

            print(
                f"Created {len(rules)} rules using {memory_used:.1f}MB ({memory_per_rule:.3f}MB per rule)"
            )

    @pytest.mark.performance
    def test_validation_result_memory_usage(self):
        """Benchmark memory usage of validation results."""
        from riveter.models.core import AssertionResult, RuleResult

        initial_memory = self.get_memory_usage()

        # Create large number of results
        results = []
        for i in range(20000):
            assertion_results = [
                AssertionResult(
                    property_path=f"tags.Tag{j}",
                    operator="present",
                    expected=None,
                    actual=f"value_{j}",
                    passed=True,
                    message="Assertion passed",
                )
                for j in range(3)  # 3 assertions each
            ]

            result = RuleResult(
                rule_id=f"rule_{i % 100}",
                resource=TerraformResource("aws_instance", f"instance_{i % 1000}", {}),
                status=True,
                message="Validation completed successfully",
                severity=Severity.INFO,
                assertion_results=assertion_results,
            )
            results.append(result)

        final_memory = self.get_memory_usage()
        memory_used = final_memory - initial_memory

        if memory_used > 0:  # Only check if we can measure memory
            memory_per_result = memory_used / len(results)

            assert memory_used < 1000, f"Too much memory used: {memory_used:.1f}MB"
            assert memory_per_result < 0.1, f"Too much memory per result: {memory_per_result:.3f}MB"

            print(
                f"Created {len(results)} results using {memory_used:.1f}MB ({memory_per_result:.3f}MB per result)"
            )


class TestConcurrencyPerformance:
    """Benchmark concurrency and thread safety."""

    def setup_method(self):
        """Set up benchmark runner."""
        self.runner = ComponentBenchmarkRunner()

    @pytest.mark.performance
    def test_concurrent_resource_access(self):
        """Test concurrent access to resources."""
        import concurrent.futures
        import threading

        # Create shared resources
        resources = [
            TerraformResource(
                "aws_instance", f"instance_{i}", {"tags": {"Environment": "prod", "Index": str(i)}}
            )
            for i in range(1000)
        ]

        def access_resources(thread_id):
            results = []
            for i in range(100):  # Each thread accesses 100 resources
                resource = resources[i % len(resources)]
                results.append(resource.get_attribute("tags.Environment"))
                results.append(resource.has_attribute("tags.Index"))
            return len(results)

        def run_concurrent_access():
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(access_resources, i) for i in range(4)]
                return [future.result() for future in futures]

        results = self.runner.time_operation("concurrent_access", run_concurrent_access)
        metrics = self.runner.get_metrics("concurrent_access")

        assert all(r == 200 for r in results)  # Each thread should process 200 operations
        assert (
            metrics["wall_time"] < 2.0
        ), f"Concurrent access too slow: {metrics['wall_time']:.3f}s"

        print(f"Concurrent resource access (4 threads) in {metrics['wall_time']:.3f}s")

    @pytest.mark.performance
    def test_concurrent_rule_evaluation(self):
        """Test concurrent rule evaluation simulation."""
        import concurrent.futures

        # Create test data
        resources = [
            TerraformResource("aws_instance", f"instance_{i}", {"tags": {"Environment": "prod"}})
            for i in range(100)
        ]

        rules = [
            Rule(
                f"rule_{i}",
                "aws_instance",
                f"Rule {i}",
                [RuleCondition("tags.Environment", "present", None)],
            )
            for i in range(20)
        ]

        def evaluate_subset(rule_subset, resource_subset):
            """Simulate evaluation of a subset of rules and resources."""
            count = 0
            for rule in rule_subset:
                for resource in resource_subset:
                    if rule.matches_resource_type(resource):
                        # Simulate some work
                        time.sleep(0.0001)  # 0.1ms per evaluation
                        count += 1
            return count

        def run_concurrent_evaluation():
            # Split work among threads
            rule_chunks = [rules[i : i + 5] for i in range(0, len(rules), 5)]  # 4 chunks of 5 rules
            resource_chunks = [
                resources[i : i + 25] for i in range(0, len(resources), 25)
            ]  # 4 chunks of 25 resources

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for rule_chunk in rule_chunks:
                    for resource_chunk in resource_chunks:
                        futures.append(executor.submit(evaluate_subset, rule_chunk, resource_chunk))

                return sum(future.result() for future in futures)

        total_evaluations = self.runner.time_operation(
            "concurrent_evaluation", run_concurrent_evaluation
        )
        metrics = self.runner.get_metrics("concurrent_evaluation")

        assert total_evaluations == 2000  # 20 rules * 100 resources
        assert (
            metrics["wall_time"] < 5.0
        ), f"Concurrent evaluation too slow: {metrics['wall_time']:.3f}s"

        print(
            f"Concurrent evaluation ({total_evaluations} evaluations) in {metrics['wall_time']:.3f}s"
        )
