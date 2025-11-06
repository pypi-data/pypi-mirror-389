"""Backward compatibility testing utilities."""

import json
import subprocess
from pathlib import Path
from typing import Any


class CompatibilityTester:
    """Test backward compatibility of CLI commands and outputs."""

    def __init__(self, baseline_file: Path | None = None):
        """Initialize with baseline data."""
        if baseline_file is None:
            baseline_file = (
                Path(__file__).parent.parent / "fixtures" / "compatibility_baseline.json"
            )

        self.baseline_file = baseline_file
        self.baseline_data = self._load_baseline()

    def _load_baseline(self) -> dict[str, Any]:
        """Load baseline compatibility data."""
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                return json.load(f)
        return {}

    def test_cli_command_compatibility(
        self, command: list[str], expected_exit_code: int = 0, check_output_structure: bool = True
    ) -> tuple[bool, str]:
        """Test that a CLI command maintains backward compatibility.

        Args:
            command: CLI command as list of arguments
            expected_exit_code: Expected exit code
            check_output_structure: Whether to validate output structure

        Returns:
            Tuple of (success, message)
        """
        try:
            # Run the command
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=30, check=False
            )

            # Check exit code
            if result.returncode != expected_exit_code:
                return (
                    False,
                    f"Exit code mismatch: expected {expected_exit_code}, got {result.returncode}",
                )

            # Check output structure if requested
            if check_output_structure:
                command_key = "_".join(command[1:])  # Skip 'riveter'
                if command_key in self.baseline_data.get("commands", {}):
                    structure_valid = self._validate_output_structure(
                        result.stdout,
                        self.baseline_data["commands"][command_key]["output_structure"],
                    )
                    if not structure_valid:
                        return (
                            False,
                            f"Output structure validation failed for command: {' '.join(command)}",
                        )

            return True, "Command compatibility validated"

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, f"Command execution failed: {e!s}"

    def _validate_output_structure(self, output: str, expected_structure: dict[str, Any]) -> bool:
        """Validate output structure against expected format."""
        if not output.strip():
            return False

        output_type = expected_structure.get("type", "table")

        if output_type == "object":
            return self._validate_json_structure(output, expected_structure)
        if output_type == "xml":
            return self._validate_xml_structure(output, expected_structure)
        # table format
        return self._validate_table_structure(output, expected_structure)

    def _validate_json_structure(self, output: str, expected_structure: dict[str, Any]) -> bool:
        """Validate JSON output structure."""
        try:
            data = json.loads(output)

            # Check required fields
            required_fields = expected_structure.get("required_fields", [])
            for field in required_fields:
                if field not in data:
                    return False

            # Check summary fields if present
            if "summary" in data and "summary_fields" in expected_structure:
                summary_fields = expected_structure["summary_fields"]
                for field in summary_fields:
                    if field not in data["summary"]:
                        return False

            return True

        except json.JSONDecodeError:
            return False

    def _validate_xml_structure(self, output: str, expected_structure: dict[str, Any]) -> bool:
        """Validate XML output structure."""
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(output)

            # Check root element
            expected_root = expected_structure.get("root_element")
            if expected_root and root.tag != expected_root:
                return False

            # Check required attributes
            required_attrs = expected_structure.get("required_attributes", [])
            for attr in required_attrs:
                if attr not in root.attrib:
                    return False

            return True

        except ET.ParseError:
            return False

    def _validate_table_structure(self, output: str, expected_structure: dict[str, Any]) -> bool:
        """Validate table output structure."""
        lines = output.strip().split("\n")
        if not lines:
            return False

        # Check column count
        expected_columns = expected_structure.get("column_count")
        if expected_columns:
            separator = expected_structure.get("separator", "|")
            header_line = lines[0]
            actual_columns = len([col for col in header_line.split(separator) if col.strip()])
            if actual_columns != expected_columns:
                return False

        # Check headers if specified
        expected_headers = expected_structure.get("headers")
        if expected_headers:
            header_line = lines[0]
            for header in expected_headers:
                if header not in header_line:
                    return False

        return True

    def test_exit_code_compatibility(self, scenario: str, command: list[str]) -> bool:
        """Test that exit codes match expected values."""
        expected_codes = self.baseline_data.get("exit_codes", {})
        if scenario not in expected_codes:
            return True  # No baseline to compare against

        expected_code = expected_codes[scenario]

        try:
            result = subprocess.run(command, capture_output=True, timeout=30, check=False)
            return result.returncode == expected_code
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    def test_file_format_compatibility(self, file_type: str, file_path: Path) -> bool:
        """Test that file formats are still supported."""
        supported_formats = self.baseline_data.get("file_formats", {})
        if file_type not in supported_formats:
            return True  # No baseline to compare against

        expected_extensions = supported_formats[file_type]
        return file_path.suffix in expected_extensions

    def generate_compatibility_report(self, test_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate a comprehensive compatibility report."""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result.get("passed", False))

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            },
            "details": test_results,
            "baseline_version": self.baseline_data.get("cli_version", "unknown"),
        }

        return report
