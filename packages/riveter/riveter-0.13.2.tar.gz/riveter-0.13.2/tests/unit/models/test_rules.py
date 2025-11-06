"""Unit tests for rule data models."""

from pathlib import Path
from typing import Any, Dict

import pytest

from riveter.models.core import Severity, TerraformResource
from riveter.models.rules import Rule, RuleCondition, RuleFilter, RuleMetadata, RulePack


class TestRuleCondition:
    """Test cases for the RuleCondition data class."""

    def test_rule_condition_creation(self):
        """Test creating a RuleCondition instance."""
        condition = RuleCondition(
            property_path="tags.Environment", operator="equals", expected_value="production"
        )

        assert condition.property_path == "tags.Environment"
        assert condition.operator == "equals"
        assert condition.expected_value == "production"

    def test_rule_condition_with_complex_value(self):
        """Test RuleCondition with complex expected value."""
        condition = RuleCondition(
            property_path="security_groups",
            operator="contains",
            expected_value=["sg-12345", "sg-67890"],
        )

        assert condition.expected_value == ["sg-12345", "sg-67890"]

    def test_rule_condition_immutable(self):
        """Test that RuleCondition is immutable."""
        condition = RuleCondition("path", "op", "value")

        with pytest.raises(AttributeError):
            condition.operator = "new_op"  # type: ignore

    def test_rule_condition_equality(self):
        """Test RuleCondition equality comparison."""
        condition1 = RuleCondition("path", "equals", "value")
        condition2 = RuleCondition("path", "equals", "value")
        condition3 = RuleCondition("path", "equals", "different")

        assert condition1 == condition2
        assert condition1 != condition3

    def test_rule_condition_to_dict(self):
        """Test converting RuleCondition to dictionary."""
        condition = RuleCondition(
            property_path="instance_type", operator="regex", expected_value=r"^t3\.(micro|small)$"
        )

        condition_dict = condition.to_dict()

        assert condition_dict["property_path"] == "instance_type"
        assert condition_dict["operator"] == "regex"
        assert condition_dict["expected_value"] == r"^t3\.(micro|small)$"


class TestRuleFilter:
    """Test cases for the RuleFilter data class."""

    def test_rule_filter_creation(self):
        """Test creating a RuleFilter instance."""
        conditions = [
            RuleCondition("tags.Environment", "equals", "production"),
            RuleCondition("instance_type", "regex", r"^t3\."),
        ]

        rule_filter = RuleFilter(conditions=conditions)

        assert len(rule_filter.conditions) == 2
        assert rule_filter.conditions[0].property_path == "tags.Environment"

    def test_rule_filter_empty(self):
        """Test creating an empty RuleFilter."""
        rule_filter = RuleFilter(conditions=[])

        assert len(rule_filter.conditions) == 0

    def test_rule_filter_immutable(self):
        """Test that RuleFilter is immutable."""
        conditions = [RuleCondition("path", "op", "value")]
        rule_filter = RuleFilter(conditions)

        with pytest.raises(AttributeError):
            rule_filter.conditions = []  # type: ignore

    def test_rule_filter_matches_resource(self):
        """Test RuleFilter matching against resources."""
        conditions = [
            RuleCondition("tags.Environment", "equals", "production"),
            RuleCondition("instance_type", "equals", "t3.micro"),
        ]
        rule_filter = RuleFilter(conditions)

        # Matching resource
        matching_resource = TerraformResource(
            type="aws_instance",
            name="web_server",
            attributes={
                "instance_type": "t3.micro",
                "tags": {"Environment": "production", "Name": "web-server"},
            },
        )

        # Non-matching resource
        non_matching_resource = TerraformResource(
            type="aws_instance",
            name="test_server",
            attributes={"instance_type": "t3.large", "tags": {"Environment": "staging"}},
        )

        assert rule_filter.matches(matching_resource) is True
        assert rule_filter.matches(non_matching_resource) is False

    def test_rule_filter_to_dict(self):
        """Test converting RuleFilter to dictionary."""
        conditions = [RuleCondition("tags.Environment", "equals", "production")]
        rule_filter = RuleFilter(conditions)

        filter_dict = rule_filter.to_dict()

        assert "conditions" in filter_dict
        assert len(filter_dict["conditions"]) == 1
        assert filter_dict["conditions"][0]["property_path"] == "tags.Environment"


class TestRuleMetadata:
    """Test cases for the RuleMetadata data class."""

    def test_rule_metadata_creation(self):
        """Test creating a RuleMetadata instance."""
        metadata = RuleMetadata(
            author="Riveter Team",
            version="1.0.0",
            created_date="2024-01-01",
            updated_date="2024-01-15",
            tags=["security", "aws"],
            references=["https://docs.aws.amazon.com/security/"],
            category="Security",
        )

        assert metadata.author == "Riveter Team"
        assert metadata.version == "1.0.0"
        assert metadata.tags == ["security", "aws"]
        assert metadata.category == "Security"

    def test_rule_metadata_minimal(self):
        """Test creating RuleMetadata with minimal fields."""
        metadata = RuleMetadata()

        assert metadata.author is None
        assert metadata.version is None
        assert metadata.tags == []
        assert metadata.references == []

    def test_rule_metadata_immutable(self):
        """Test that RuleMetadata is immutable."""
        metadata = RuleMetadata(author="Test Author")

        with pytest.raises(AttributeError):
            metadata.author = "New Author"  # type: ignore

    def test_rule_metadata_to_dict(self):
        """Test converting RuleMetadata to dictionary."""
        metadata = RuleMetadata(
            author="Test Author", version="2.0.0", tags=["test", "example"], category="Testing"
        )

        metadata_dict = metadata.to_dict()

        assert metadata_dict["author"] == "Test Author"
        assert metadata_dict["version"] == "2.0.0"
        assert metadata_dict["tags"] == ["test", "example"]
        assert metadata_dict["category"] == "Testing"


class TestRule:
    """Test cases for the Rule data class."""

    def test_rule_creation_basic(self):
        """Test creating a basic Rule instance."""
        conditions = [RuleCondition("tags.Environment", "present", None)]

        rule = Rule(
            id="test-rule-001",
            resource_type="aws_instance",
            description="Test rule for EC2 instances",
            conditions=conditions,
            severity=Severity.ERROR,
        )

        assert rule.id == "test-rule-001"
        assert rule.resource_type == "aws_instance"
        assert rule.description == "Test rule for EC2 instances"
        assert rule.severity == Severity.ERROR
        assert len(rule.conditions) == 1

    def test_rule_creation_with_filter(self):
        """Test creating Rule with filter conditions."""
        filter_conditions = [RuleCondition("tags.Environment", "equals", "production")]
        rule_filter = RuleFilter(filter_conditions)

        assert_conditions = [RuleCondition("tags.CostCenter", "present", None)]

        rule = Rule(
            id="filtered-rule",
            resource_type="aws_instance",
            description="Rule with filter",
            conditions=assert_conditions,
            rule_filter=rule_filter,
            severity=Severity.WARNING,
        )

        assert rule.rule_filter is not None
        assert len(rule.rule_filter.conditions) == 1
        assert rule.rule_filter.conditions[0].property_path == "tags.Environment"

    def test_rule_creation_with_metadata(self):
        """Test creating Rule with metadata."""
        conditions = [RuleCondition("instance_type", "equals", "t3.micro")]
        metadata = RuleMetadata(
            author="Test Author",
            version="1.0.0",
            tags=["cost-optimization"],
            category="Performance",
        )

        rule = Rule(
            id="metadata-rule",
            resource_type="aws_instance",
            description="Rule with metadata",
            conditions=conditions,
            metadata=metadata,
        )

        assert rule.metadata is not None
        assert rule.metadata.author == "Test Author"
        assert rule.metadata.tags == ["cost-optimization"]

    def test_rule_immutable(self):
        """Test that Rule is immutable."""
        conditions = [RuleCondition("path", "op", "value")]
        rule = Rule("id", "type", "desc", conditions)

        with pytest.raises(AttributeError):
            rule.id = "new_id"  # type: ignore

    def test_rule_matches_resource_type(self):
        """Test Rule resource type matching."""
        conditions = [RuleCondition("tags.Environment", "present", None)]

        # Specific resource type rule
        specific_rule = Rule("rule1", "aws_instance", "desc", conditions)

        # Wildcard resource type rule
        wildcard_rule = Rule("rule2", "*", "desc", conditions)

        aws_instance = TerraformResource("aws_instance", "web", {})
        s3_bucket = TerraformResource("aws_s3_bucket", "data", {})

        # Specific rule should only match aws_instance
        assert specific_rule.matches_resource_type(aws_instance) is True
        assert specific_rule.matches_resource_type(s3_bucket) is False

        # Wildcard rule should match all resource types
        assert wildcard_rule.matches_resource_type(aws_instance) is True
        assert wildcard_rule.matches_resource_type(s3_bucket) is True

    def test_rule_applies_to_resource(self):
        """Test Rule application to resources with filters."""
        filter_conditions = [RuleCondition("tags.Environment", "equals", "production")]
        rule_filter = RuleFilter(filter_conditions)

        assert_conditions = [RuleCondition("tags.CostCenter", "present", None)]

        rule = Rule(
            id="filtered-rule",
            resource_type="aws_instance",
            description="Rule with filter",
            conditions=assert_conditions,
            rule_filter=rule_filter,
        )

        # Resource that matches filter
        matching_resource = TerraformResource(
            type="aws_instance",
            name="prod_server",
            attributes={"tags": {"Environment": "production", "Name": "server"}},
        )

        # Resource that doesn't match filter
        non_matching_resource = TerraformResource(
            type="aws_instance", name="test_server", attributes={"tags": {"Environment": "staging"}}
        )

        # Resource with wrong type
        wrong_type_resource = TerraformResource(
            type="aws_s3_bucket", name="bucket", attributes={"tags": {"Environment": "production"}}
        )

        assert rule.applies_to_resource(matching_resource) is True
        assert rule.applies_to_resource(non_matching_resource) is False
        assert rule.applies_to_resource(wrong_type_resource) is False

    def test_rule_to_dict(self):
        """Test converting Rule to dictionary."""
        conditions = [RuleCondition("tags.Environment", "present", None)]
        metadata = RuleMetadata(author="Test", version="1.0")

        rule = Rule(
            id="test-rule",
            resource_type="aws_instance",
            description="Test rule",
            conditions=conditions,
            severity=Severity.ERROR,
            metadata=metadata,
        )

        rule_dict = rule.to_dict()

        assert rule_dict["id"] == "test-rule"
        assert rule_dict["resource_type"] == "aws_instance"
        assert rule_dict["description"] == "Test rule"
        assert rule_dict["severity"] == "error"
        assert "conditions" in rule_dict
        assert "metadata" in rule_dict
        assert len(rule_dict["conditions"]) == 1


class TestRulePack:
    """Test cases for the RulePack data class."""

    def test_rule_pack_creation(self):
        """Test creating a RulePack instance."""
        rules = [
            Rule("rule1", "aws_instance", "Rule 1", [RuleCondition("path1", "op", "val")]),
            Rule("rule2", "aws_s3_bucket", "Rule 2", [RuleCondition("path2", "op", "val")]),
        ]

        metadata = RuleMetadata(
            author="Pack Author", version="2.0.0", tags=["security", "compliance"]
        )

        rule_pack = RulePack(
            name="test-pack", description="Test rule pack", rules=rules, metadata=metadata
        )

        assert rule_pack.name == "test-pack"
        assert rule_pack.description == "Test rule pack"
        assert len(rule_pack.rules) == 2
        assert rule_pack.metadata.author == "Pack Author"

    def test_rule_pack_empty(self):
        """Test creating an empty RulePack."""
        rule_pack = RulePack(name="empty-pack", description="Empty pack", rules=[])

        assert len(rule_pack.rules) == 0
        assert rule_pack.metadata is None

    def test_rule_pack_immutable(self):
        """Test that RulePack is immutable."""
        rules = [Rule("rule1", "type", "desc", [RuleCondition("path", "op", "val")])]
        rule_pack = RulePack("pack", "desc", rules)

        with pytest.raises(AttributeError):
            rule_pack.name = "new_name"  # type: ignore

    def test_rule_pack_get_rules_by_type(self):
        """Test getting rules by resource type from RulePack."""
        rules = [
            Rule("rule1", "aws_instance", "EC2 rule", [RuleCondition("path1", "op", "val")]),
            Rule("rule2", "aws_s3_bucket", "S3 rule", [RuleCondition("path2", "op", "val")]),
            Rule(
                "rule3", "aws_instance", "Another EC2 rule", [RuleCondition("path3", "op", "val")]
            ),
            Rule("rule4", "*", "Universal rule", [RuleCondition("path4", "op", "val")]),
        ]

        rule_pack = RulePack("test-pack", "Test pack", rules)

        # Get rules for specific resource type
        ec2_rules = rule_pack.get_rules_for_resource_type("aws_instance")
        s3_rules = rule_pack.get_rules_for_resource_type("aws_s3_bucket")
        rds_rules = rule_pack.get_rules_for_resource_type("aws_rds_instance")

        # Should include specific rules + universal rules
        assert len(ec2_rules) == 3  # 2 specific + 1 universal
        assert len(s3_rules) == 2  # 1 specific + 1 universal
        assert len(rds_rules) == 1  # 0 specific + 1 universal

        # Check rule IDs
        ec2_rule_ids = [rule.id for rule in ec2_rules]
        assert "rule1" in ec2_rule_ids
        assert "rule3" in ec2_rule_ids
        assert "rule4" in ec2_rule_ids  # Universal rule

    def test_rule_pack_get_rule_by_id(self):
        """Test getting a specific rule by ID from RulePack."""
        rules = [
            Rule("rule1", "aws_instance", "Rule 1", [RuleCondition("path1", "op", "val")]),
            Rule("rule2", "aws_s3_bucket", "Rule 2", [RuleCondition("path2", "op", "val")]),
        ]

        rule_pack = RulePack("test-pack", "Test pack", rules)

        # Get existing rule
        rule1 = rule_pack.get_rule_by_id("rule1")
        assert rule1 is not None
        assert rule1.id == "rule1"
        assert rule1.resource_type == "aws_instance"

        # Get non-existing rule
        missing_rule = rule_pack.get_rule_by_id("missing")
        assert missing_rule is None

    def test_rule_pack_to_dict(self):
        """Test converting RulePack to dictionary."""
        rules = [Rule("rule1", "aws_instance", "Rule 1", [RuleCondition("path1", "op", "val")])]
        metadata = RuleMetadata(author="Author", version="1.0")

        rule_pack = RulePack("test-pack", "Test pack", rules, metadata)

        pack_dict = rule_pack.to_dict()

        assert pack_dict["name"] == "test-pack"
        assert pack_dict["description"] == "Test pack"
        assert "rules" in pack_dict
        assert "metadata" in pack_dict
        assert len(pack_dict["rules"]) == 1
        assert pack_dict["metadata"]["author"] == "Author"

    def test_rule_pack_statistics(self):
        """Test RulePack statistics calculation."""
        rules = [
            Rule(
                "rule1", "aws_instance", "Rule 1", [RuleCondition("p1", "op", "v")], Severity.ERROR
            ),
            Rule(
                "rule2",
                "aws_s3_bucket",
                "Rule 2",
                [RuleCondition("p2", "op", "v")],
                Severity.WARNING,
            ),
            Rule(
                "rule3", "aws_instance", "Rule 3", [RuleCondition("p3", "op", "v")], Severity.INFO
            ),
            Rule("rule4", "*", "Rule 4", [RuleCondition("p4", "op", "v")], Severity.ERROR),
        ]

        rule_pack = RulePack("test-pack", "Test pack", rules)

        stats = rule_pack.get_statistics()

        assert stats["total_rules"] == 4
        assert stats["error_rules"] == 2
        assert stats["warning_rules"] == 1
        assert stats["info_rules"] == 1
        assert stats["resource_types"] == {"aws_instance", "aws_s3_bucket", "*"}
        assert len(stats["resource_types"]) == 3


class TestRuleEdgeCases:
    """Test edge cases and complex scenarios for rule models."""

    def test_rule_with_complex_conditions(self):
        """Test Rule with complex condition combinations."""
        conditions = [
            RuleCondition("tags.Environment", "equals", "production"),
            RuleCondition("instance_type", "regex", r"^(t3|m5)\.(large|xlarge)$"),
            RuleCondition("security_groups", "length", {"gte": 1}),
            RuleCondition("root_block_device.volume_size", "gte", 100),
            RuleCondition("network_interfaces[0].subnet_id", "present", None),
        ]

        rule = Rule(
            id="complex-rule",
            resource_type="aws_instance",
            description="Complex validation rule",
            conditions=conditions,
            severity=Severity.ERROR,
        )

        assert len(rule.conditions) == 5
        assert rule.conditions[1].operator == "regex"
        assert rule.conditions[2].expected_value == {"gte": 1}

    def test_rule_filter_with_nested_conditions(self):
        """Test RuleFilter with deeply nested conditions."""
        conditions = [
            RuleCondition("metadata.labels.environment", "equals", "prod"),
            RuleCondition("spec.containers[0].resources.limits.memory", "gte", "1Gi"),
            RuleCondition("spec.template.spec.securityContext.runAsNonRoot", "equals", True),
        ]

        rule_filter = RuleFilter(conditions)

        # Test with Kubernetes-like resource
        k8s_resource = TerraformResource(
            type="kubernetes_deployment",
            name="web_app",
            attributes={
                "metadata": {"labels": {"environment": "prod", "app": "web"}},
                "spec": {
                    "containers": [{"resources": {"limits": {"memory": "2Gi", "cpu": "1000m"}}}],
                    "template": {"spec": {"securityContext": {"runAsNonRoot": True}}},
                },
            },
        )

        # This would require actual implementation of the matching logic
        # For now, we just test that the filter structure is correct
        assert len(rule_filter.conditions) == 3
        assert rule_filter.conditions[0].property_path == "metadata.labels.environment"

    def test_rule_pack_with_duplicate_rule_ids(self):
        """Test RulePack handling of duplicate rule IDs."""
        rules = [
            Rule("duplicate-id", "aws_instance", "Rule 1", [RuleCondition("p1", "op", "v")]),
            Rule("duplicate-id", "aws_s3_bucket", "Rule 2", [RuleCondition("p2", "op", "v")]),
            Rule("unique-id", "aws_rds_instance", "Rule 3", [RuleCondition("p3", "op", "v")]),
        ]

        rule_pack = RulePack("test-pack", "Test pack with duplicates", rules)

        # Should still contain all rules
        assert len(rule_pack.rules) == 3

        # get_rule_by_id should return the first matching rule
        found_rule = rule_pack.get_rule_by_id("duplicate-id")
        assert found_rule is not None
        assert found_rule.resource_type == "aws_instance"  # First one

    def test_rule_metadata_with_complex_data(self):
        """Test RuleMetadata with complex data structures."""
        metadata = RuleMetadata(
            author="Complex Author",
            version="1.2.3-beta.1",
            created_date="2024-01-01T10:00:00Z",
            updated_date="2024-01-15T15:30:00Z",
            tags=["security", "compliance", "aws", "ec2"],
            references=[
                "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security.html",
                "https://aws.amazon.com/security/security-bulletins/",
                "CIS AWS Foundations Benchmark v1.4.0 - Section 2.1",
            ],
            category="Security/Network",
            custom_fields={
                "compliance_frameworks": ["CIS", "SOC2", "PCI-DSS"],
                "risk_level": "high",
                "remediation_effort": "medium",
                "automation_available": True,
            },
        )

        assert len(metadata.tags) == 4
        assert len(metadata.references) == 3
        assert metadata.custom_fields["compliance_frameworks"] == ["CIS", "SOC2", "PCI-DSS"]
        assert metadata.custom_fields["automation_available"] is True

        # Test serialization
        metadata_dict = metadata.to_dict()
        assert "custom_fields" in metadata_dict
        assert metadata_dict["custom_fields"]["risk_level"] == "high"

    def test_rule_condition_with_operator_parameters(self):
        """Test RuleCondition with complex operator parameters."""
        # Test regex with flags
        regex_condition = RuleCondition(
            property_path="name",
            operator="regex",
            expected_value={"pattern": r"^web-\d+$", "flags": ["IGNORECASE"]},
        )

        # Test range condition
        range_condition = RuleCondition(
            property_path="port", operator="range", expected_value={"min": 80, "max": 8080}
        )

        # Test list operations
        list_condition = RuleCondition(
            property_path="allowed_ips",
            operator="all_match",
            expected_value={"pattern": r"^10\.0\.\d+\.\d+$"},
        )

        assert regex_condition.expected_value["pattern"] == r"^web-\d+$"
        assert range_condition.expected_value["min"] == 80
        assert list_condition.operator == "all_match"
