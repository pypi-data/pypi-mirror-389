"""Test fixture management utilities."""

import json
import tempfile
from pathlib import Path
from typing import Any

import yaml


class FixtureManager:
    """Manage test fixtures and data."""

    def __init__(self, fixtures_dir: Path | None = None):
        """Initialize fixture manager."""
        if fixtures_dir is None:
            fixtures_dir = Path(__file__).parent.parent / "fixtures"

        self.fixtures_dir = fixtures_dir
        self.terraform_dir = fixtures_dir / "terraform"
        self.rules_dir = fixtures_dir / "rules"
        self.rule_packs_dir = fixtures_dir / "rule_packs"

    def get_terraform_fixture(self, name: str) -> Path:
        """Get path to Terraform fixture file."""
        file_path = self.terraform_dir / f"{name}.tf"
        if not file_path.exists():
            raise FileNotFoundError(f"Terraform fixture '{name}' not found at {file_path}")
        return file_path

    def get_rules_fixture(self, name: str) -> Path:
        """Get path to rules fixture file."""
        file_path = self.rules_dir / f"{name}.yml"
        if not file_path.exists():
            raise FileNotFoundError(f"Rules fixture '{name}' not found at {file_path}")
        return file_path

    def get_rule_pack_fixture(self, name: str) -> Path:
        """Get path to rule pack fixture file."""
        file_path = self.rule_packs_dir / f"{name}.yml"
        if not file_path.exists():
            raise FileNotFoundError(f"Rule pack fixture '{name}' not found at {file_path}")
        return file_path

    def load_yaml_fixture(self, file_path: Path) -> dict[str, Any]:
        """Load YAML fixture data."""
        with open(file_path) as f:
            return yaml.safe_load(f)

    def load_json_fixture(self, file_path: Path) -> dict[str, Any]:
        """Load JSON fixture data."""
        with open(file_path) as f:
            return json.load(f)

    def create_temp_terraform_file(self, content: str) -> Path:
        """Create temporary Terraform file with given content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tf", delete=False) as f:
            f.write(content)
            return Path(f.name)

    def create_temp_rules_file(self, rules_data: dict[str, Any] | list[dict[str, Any]]) -> Path:
        """Create temporary rules file with given data."""
        if isinstance(rules_data, list):
            rules_data = {"rules": rules_data}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(rules_data, f, default_flow_style=False)
            return Path(f.name)

    def list_terraform_fixtures(self) -> list[str]:
        """List available Terraform fixtures."""
        return [f.stem for f in self.terraform_dir.glob("*.tf")]

    def list_rules_fixtures(self) -> list[str]:
        """List available rules fixtures."""
        return [f.stem for f in self.rules_dir.glob("*.yml")]

    def list_rule_pack_fixtures(self) -> list[str]:
        """List available rule pack fixtures."""
        return [f.stem for f in self.rule_packs_dir.glob("*.yml")]

    def validate_fixture_integrity(self) -> dict[str, list[str]]:
        """Validate that all fixtures are properly formatted."""
        results = {
            "valid_terraform": [],
            "invalid_terraform": [],
            "valid_rules": [],
            "invalid_rules": [],
            "valid_rule_packs": [],
            "invalid_rule_packs": [],
        }

        # Validate Terraform fixtures
        for tf_file in self.terraform_dir.glob("*.tf"):
            try:
                # Basic syntax check - just try to read the file
                with open(tf_file) as f:
                    content = f.read()
                    if content.strip():  # Non-empty file
                        results["valid_terraform"].append(tf_file.stem)
                    else:
                        results["invalid_terraform"].append(f"{tf_file.stem}: Empty file")
            except Exception as e:
                results["invalid_terraform"].append(f"{tf_file.stem}: {e!s}")

        # Validate rules fixtures
        for rules_file in self.rules_dir.glob("*.yml"):
            try:
                data = self.load_yaml_fixture(rules_file)
                if isinstance(data, dict) and "rules" in data:
                    results["valid_rules"].append(rules_file.stem)
                else:
                    results["invalid_rules"].append(f"{rules_file.stem}: Invalid structure")
            except Exception as e:
                results["invalid_rules"].append(f"{rules_file.stem}: {e!s}")

        # Validate rule pack fixtures
        for pack_file in self.rule_packs_dir.glob("*.yml"):
            try:
                data = self.load_yaml_fixture(pack_file)
                if isinstance(data, dict):
                    results["valid_rule_packs"].append(pack_file.stem)
                else:
                    results["invalid_rule_packs"].append(f"{pack_file.stem}: Invalid structure")
            except Exception as e:
                results["invalid_rule_packs"].append(f"{pack_file.stem}: {e!s}")

        return results

    def create_test_scenario(
        self,
        terraform_content: str,
        rules_data: list[dict[str, Any]],
        expected_results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a complete test scenario with Terraform and rules."""
        terraform_file = self.create_temp_terraform_file(terraform_content)
        rules_file = self.create_temp_rules_file(rules_data)

        scenario = {
            "terraform_file": terraform_file,
            "rules_file": rules_file,
            "expected_results": expected_results or {},
        }

        return scenario

    def cleanup_temp_files(self, *file_paths: Path):
        """Clean up temporary files."""
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors
