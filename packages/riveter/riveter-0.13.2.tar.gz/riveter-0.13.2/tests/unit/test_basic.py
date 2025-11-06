"""Basic unit tests to verify pytest is working."""

import pytest


class TestBasicFunctionality:
    """Basic tests to verify pytest infrastructure."""

    def test_pytest_working(self):
        """Test that pytest is working correctly."""
        assert True

    def test_basic_math(self):
        """Test basic math operations."""
        assert 1 + 1 == 2
        assert 2 * 3 == 6

    def test_string_operations(self):
        """Test basic string operations."""
        test_string = "riveter"
        assert test_string.upper() == "RIVETER"
        assert len(test_string) == 7

    def test_list_operations(self):
        """Test basic list operations."""
        test_list = [1, 2, 3]
        test_list.append(4)
        assert len(test_list) == 4
        assert test_list[-1] == 4

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            (1, 2),
            (2, 4),
            (3, 6),
            (0, 0),
        ],
    )
    def test_parametrized(self, input_val, expected):
        """Test parametrized test functionality."""
        assert input_val * 2 == expected
