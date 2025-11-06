"""Unit tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from riveter.cli.commands import ScanCommand
from riveter.cli.interface import BaseCommand, Command, CommandResult
from riveter.models.core import RuleResult, Severity, ValidationSummary


class TestCommandResult:
    """Test cases for the CommandResult data class."""

    def test_command_result_success(self):
        """Test creating a successful CommandResult."""
        result = CommandResult(
            exit_code=0,
            output="Command completed successfully",
        )

        assert result.exit_code == 0
        assert result.output == "Command completed successfully"
        assert result.error is None

    def test_command_result_failure(self):
        """Test creating a failed CommandResult."""
        result = CommandResult(exit_code=1, output="Command failed", error="File not found")

        assert result.exit_code == 1
        assert result.output == "Command failed"
        assert result.error == "File not found"

    def test_command_result_immutable(self):
        """Test that CommandResult is immutable."""
        result = CommandResult(exit_code=0, output="Success")

        with pytest.raises(AttributeError):
            result.exit_code = 1  # type: ignore


# CommandError tests removed - class doesn't exist in current implementation


class TestCommand:
    """Test cases for the base Command class."""

    def test_command_abstract_methods(self):
        """Test that Command is abstract and requires implementation."""
        with pytest.raises(TypeError):
            Command()  # type: ignore

    def test_command_subclass_implementation(self):
        """Test implementing Command subclass."""

        class TestCommand(Command):
            def execute(self, args: dict) -> CommandResult:
                return CommandResult(True, 0, "Test command executed")

        command = TestCommand()
        result = command.execute({})

        assert result.success is True
        assert result.message == "Test command executed"


class TestScanCommand:
    """Test cases for the ScanCommand class."""

    def test_scan_command_creation(self):
        """Test creating a ScanCommand instance."""
        command = ScanCommand()
        assert isinstance(command, ScanCommand)

    @patch("riveter.cli.commands.ValidationEngine")
    @patch("riveter.cli.commands.ConfigurationManager")
    @patch("riveter.cli.commands.RuleManager")
    def test_scan_command_execute_success(
        self, mock_rule_manager, mock_config_manager, mock_validation_engine
    ):
        """Test successful scan command execution."""
        # Mock dependencies
        mock_config = Mock()
        mock_config_manager.return_value.load_terraform_config.return_value = mock_config

        mock_rules = [Mock()]
        mock_rule_manager.return_value.load_rules.return_value = mock_rules

        mock_validation_result = Mock()
        mock_validation_result.summary = ValidationSummary(
            total_rules=1,
            total_resources=1,
            passed_rules=1,
            failed_rules=0,
            skipped_rules=0,
            total_assertions=1,
            passed_assertions=1,
            failed_assertions=0,
            execution_time=0.1,
            error_count=0,
            warning_count=0,
            info_count=1,
        )
        mock_validation_result.rule_results = []
        mock_validation_engine.return_value.validate.return_value = mock_validation_result

        command = ScanCommand()
        args = {
            "terraform_file": Path("test.tf"),
            "rule_packs": ["aws-security"],
            "output_format": "json",
            "verbose": False,
        }

        result = command.execute(args)

        assert result.success is True
        assert result.exit_code == 0
        assert "validation completed" in result.message.lower()

    @patch("riveter.cli.commands.ConfigurationManager")
    def test_scan_command_execute_config_error(self, mock_config_manager):
        """Test scan command with configuration error."""
        mock_config_manager.return_value.load_terraform_config.side_effect = Exception(
            "Config error"
        )

        command = ScanCommand()
        args = {
            "terraform_file": Path("nonexistent.tf"),
            "rule_packs": ["aws-security"],
            "output_format": "json",
            "verbose": False,
        }

        result = command.execute(args)

        assert result.success is False
        assert result.exit_code == 1
        assert "config error" in result.message.lower()

    @patch("riveter.cli.commands.ValidationEngine")
    @patch("riveter.cli.commands.ConfigurationManager")
    @patch("riveter.cli.commands.RuleManager")
    def test_scan_command_execute_with_failures(
        self, mock_rule_manager, mock_config_manager, mock_validation_engine
    ):
        """Test scan command execution with validation failures."""
        # Mock dependencies
        mock_config = Mock()
        mock_config_manager.return_value.load_terraform_config.return_value = mock_config

        mock_rules = [Mock()]
        mock_rule_manager.return_value.load_rules.return_value = mock_rules

        # Mock validation result with failures
        mock_validation_result = Mock()
        mock_validation_result.summary = ValidationSummary(
            total_rules=2,
            total_resources=1,
            passed_rules=1,
            failed_rules=1,
            skipped_rules=0,
            total_assertions=2,
            passed_assertions=1,
            failed_assertions=1,
            execution_time=0.2,
            error_count=1,
            warning_count=0,
            info_count=1,
        )
        mock_validation_result.rule_results = [Mock(status=False, severity=Severity.ERROR)]
        mock_validation_engine.return_value.validate.return_value = mock_validation_result

        command = ScanCommand()
        args = {
            "terraform_file": Path("test.tf"),
            "rule_packs": ["aws-security"],
            "output_format": "table",
            "verbose": True,
        }

        result = command.execute(args)

        # Should succeed but with exit code 1 due to validation failures
        assert result.success is True
        assert result.exit_code == 1  # Non-zero due to validation failures

    def test_scan_command_validate_args(self):
        """Test scan command argument validation."""
        command = ScanCommand()

        # Valid args
        valid_args = {
            "terraform_file": Path("test.tf"),
            "rule_packs": ["aws-security"],
            "output_format": "json",
            "verbose": False,
        }

        # Should not raise exception
        command._validate_args(valid_args)

        # Invalid args - missing terraform_file
        invalid_args = {"rule_packs": ["aws-security"], "output_format": "json", "verbose": False}

        with pytest.raises(CommandError):
            command._validate_args(invalid_args)

    def test_scan_command_format_output(self):
        """Test scan command output formatting."""
        command = ScanCommand()

        # Mock validation result
        validation_result = Mock()
        validation_result.summary = ValidationSummary(
            total_rules=1,
            total_resources=1,
            passed_rules=1,
            failed_rules=0,
            skipped_rules=0,
            total_assertions=1,
            passed_assertions=1,
            failed_assertions=0,
            execution_time=0.1,
            error_count=0,
            warning_count=0,
            info_count=1,
        )
        validation_result.rule_results = []

        # Test JSON format
        json_output = command._format_output(validation_result, "json")
        assert isinstance(json_output, str)
        assert "{" in json_output  # Should be JSON

        # Test table format
        table_output = command._format_output(validation_result, "table")
        assert isinstance(table_output, str)
        assert len(table_output) > 0


class TestListRulePacksCommand:
    """Test cases for the ListRulePacksCommand class."""

    def test_list_rule_packs_command_creation(self):
        """Test creating a ListRulePacksCommand instance."""
        command = ListRulePacksCommand()
        assert isinstance(command, ListRulePacksCommand)

    @patch("riveter.cli.commands.RulePackManager")
    def test_list_rule_packs_command_execute_success(self, mock_rule_pack_manager):
        """Test successful list rule packs command execution."""
        # Mock rule pack manager
        mock_packs = [
            Mock(name="aws-security", description="AWS Security Rules", rules=[Mock(), Mock()]),
            Mock(name="gcp-security", description="GCP Security Rules", rules=[Mock()]),
        ]
        mock_rule_pack_manager.return_value.list_available_packs.return_value = mock_packs

        command = ListRulePacksCommand()
        args = {"verbose": False}

        result = command.execute(args)

        assert result.success is True
        assert result.exit_code == 0
        assert "rule packs" in result.message.lower()
        assert result.data is not None
        assert len(result.data["rule_packs"]) == 2

    @patch("riveter.cli.commands.RulePackManager")
    def test_list_rule_packs_command_execute_verbose(self, mock_rule_pack_manager):
        """Test list rule packs command with verbose output."""
        mock_packs = [
            Mock(
                name="aws-security",
                description="AWS Security Rules",
                rules=[Mock(), Mock()],
                metadata=Mock(version="1.0.0", author="Riveter Team"),
            )
        ]
        mock_rule_pack_manager.return_value.list_available_packs.return_value = mock_packs

        command = ListRulePacksCommand()
        args = {"verbose": True}

        result = command.execute(args)

        assert result.success is True
        assert result.exit_code == 0
        # Verbose output should include more details
        assert "version" in result.message.lower() or "author" in result.message.lower()

    @patch("riveter.cli.commands.RulePackManager")
    def test_list_rule_packs_command_execute_error(self, mock_rule_pack_manager):
        """Test list rule packs command with error."""
        mock_rule_pack_manager.return_value.list_available_packs.side_effect = Exception(
            "Pack loading error"
        )

        command = ListRulePacksCommand()
        args = {"verbose": False}

        result = command.execute(args)

        assert result.success is False
        assert result.exit_code == 1
        assert "error" in result.message.lower()

    def test_list_rule_packs_command_format_output(self):
        """Test list rule packs command output formatting."""
        command = ListRulePacksCommand()

        mock_packs = [
            Mock(name="aws-security", description="AWS Security Rules", rules=[Mock(), Mock()]),
            Mock(name="gcp-security", description="GCP Security Rules", rules=[Mock()]),
        ]

        # Test basic formatting
        output = command._format_pack_list(mock_packs, verbose=False)
        assert "aws-security" in output
        assert "gcp-security" in output
        assert "2 rules" in output or "1 rule" in output

        # Test verbose formatting
        verbose_output = command._format_pack_list(mock_packs, verbose=True)
        assert len(verbose_output) >= len(output)  # Verbose should be longer


class TestValidateRulePackCommand:
    """Test cases for the ValidateRulePackCommand class."""

    def test_validate_rule_pack_command_creation(self):
        """Test creating a ValidateRulePackCommand instance."""
        command = ValidateRulePackCommand()
        assert isinstance(command, ValidateRulePackCommand)

    @patch("riveter.cli.commands.RulePackManager")
    def test_validate_rule_pack_command_execute_success(self, mock_rule_pack_manager):
        """Test successful validate rule pack command execution."""
        # Mock successful validation
        mock_validation_result = Mock(
            is_valid=True,
            errors=[],
            warnings=[],
            rule_count=5,
            metadata=Mock(name="test-pack", version="1.0.0"),
        )
        mock_rule_pack_manager.return_value.validate_pack.return_value = mock_validation_result

        command = ValidateRulePackCommand()
        args = {"rule_pack_file": Path("test-pack.yml")}

        result = command.execute(args)

        assert result.success is True
        assert result.exit_code == 0
        assert "valid" in result.message.lower()

    @patch("riveter.cli.commands.RulePackManager")
    def test_validate_rule_pack_command_execute_with_errors(self, mock_rule_pack_manager):
        """Test validate rule pack command with validation errors."""
        # Mock validation with errors
        mock_validation_result = Mock(
            is_valid=False,
            errors=["Rule ID 'test-rule' is missing", "Invalid operator 'unknown'"],
            warnings=["Deprecated field 'old_field' used"],
            rule_count=3,
            metadata=Mock(name="invalid-pack", version="1.0.0"),
        )
        mock_rule_pack_manager.return_value.validate_pack.return_value = mock_validation_result

        command = ValidateRulePackCommand()
        args = {"rule_pack_file": Path("invalid-pack.yml")}

        result = command.execute(args)

        assert result.success is False
        assert result.exit_code == 1
        assert "error" in result.message.lower()
        assert "2 errors" in result.message or "errors" in result.message

    @patch("riveter.cli.commands.RulePackManager")
    def test_validate_rule_pack_command_execute_file_not_found(self, mock_rule_pack_manager):
        """Test validate rule pack command with missing file."""
        mock_rule_pack_manager.return_value.validate_pack.side_effect = FileNotFoundError(
            "File not found"
        )

        command = ValidateRulePackCommand()
        args = {"rule_pack_file": Path("nonexistent.yml")}

        result = command.execute(args)

        assert result.success is False
        assert result.exit_code == 1
        assert "not found" in result.message.lower()

    def test_validate_rule_pack_command_validate_args(self):
        """Test validate rule pack command argument validation."""
        command = ValidateRulePackCommand()

        # Valid args
        valid_args = {"rule_pack_file": Path("test.yml")}
        command._validate_args(valid_args)  # Should not raise

        # Invalid args - missing file
        invalid_args = {}
        with pytest.raises(CommandError):
            command._validate_args(invalid_args)

    def test_validate_rule_pack_command_format_validation_result(self):
        """Test formatting validation results."""
        command = ValidateRulePackCommand()

        # Valid result
        valid_result = Mock(
            is_valid=True,
            errors=[],
            warnings=[],
            rule_count=5,
            metadata=Mock(name="test-pack", version="1.0.0"),
        )

        output = command._format_validation_result(valid_result)
        assert "✓" in output or "valid" in output.lower()
        assert "5 rules" in output

        # Invalid result with errors and warnings
        invalid_result = Mock(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            rule_count=3,
            metadata=Mock(name="invalid-pack", version="1.0.0"),
        )

        output = command._format_validation_result(invalid_result)
        assert "✗" in output or "invalid" in output.lower()
        assert "2 errors" in output
        assert "1 warning" in output


class TestCommandIntegration:
    """Integration tests for command interactions."""

    def test_command_error_propagation(self):
        """Test that command errors are properly propagated."""

        class FailingCommand(Command):
            def execute(self, args: dict) -> CommandResult:
                raise CommandError("Command failed", exit_code=2)

        command = FailingCommand()

        with pytest.raises(CommandError) as exc_info:
            command.execute({})

        assert str(exc_info.value) == "Command failed"
        assert exc_info.value.exit_code == 2

    def test_command_result_serialization(self):
        """Test that command results can be serialized."""
        result = CommandResult(
            success=True,
            exit_code=0,
            message="Success",
            data={"count": 5, "items": ["a", "b", "c"]},
            execution_time=1.5,
        )

        # Test conversion to dict
        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["exit_code"] == 0
        assert result_dict["message"] == "Success"
        assert result_dict["data"]["count"] == 5
        assert result_dict["execution_time"] == 1.5

    @patch("riveter.cli.commands.ValidationEngine")
    @patch("riveter.cli.commands.ConfigurationManager")
    @patch("riveter.cli.commands.RuleManager")
    def test_scan_command_with_real_file_paths(
        self, mock_rule_manager, mock_config_manager, mock_validation_engine
    ):
        """Test scan command with realistic file paths."""
        # Mock successful execution
        mock_config_manager.return_value.load_terraform_config.return_value = Mock()
        mock_rule_manager.return_value.load_rules.return_value = [Mock()]

        mock_validation_result = Mock()
        mock_validation_result.summary = ValidationSummary(
            total_rules=1,
            total_resources=1,
            passed_rules=1,
            failed_rules=0,
            skipped_rules=0,
            total_assertions=1,
            passed_assertions=1,
            failed_assertions=0,
            execution_time=0.1,
            error_count=0,
            warning_count=0,
            info_count=1,
        )
        mock_validation_result.rule_results = []
        mock_validation_engine.return_value.validate.return_value = mock_validation_result

        command = ScanCommand()

        # Test with various file path formats
        test_cases = [
            Path("main.tf"),
            Path("./terraform/main.tf"),
            Path("/absolute/path/to/main.tf"),
            Path("../relative/path/main.tf"),
        ]

        for terraform_file in test_cases:
            args = {
                "terraform_file": terraform_file,
                "rule_packs": ["aws-security"],
                "output_format": "json",
                "verbose": False,
            }

            result = command.execute(args)
            assert result.success is True

    def test_command_performance_tracking(self):
        """Test that commands track execution time."""

        class TimedCommand(Command):
            def execute(self, args: dict) -> CommandResult:
                import time

                time.sleep(0.1)  # Simulate work
                return CommandResult(True, 0, "Completed", execution_time=0.1)

        command = TimedCommand()
        result = command.execute({})

        assert result.execution_time is not None
        assert result.execution_time > 0
