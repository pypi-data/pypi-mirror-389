"""Tests for helper utilities."""

import pytest
from resume.utils.helpers import format_text, validate_input, format_category_name, safe_get


class TestFormatText:
    """Tests for format_text function."""

    def test_basic_formatting(self):
        """Test basic text formatting."""
        assert format_text("  hello  ") == "hello"

    def test_uppercase_formatting(self):
        """Test uppercase conversion."""
        assert format_text("hello", uppercase=True) == "HELLO"

    def test_empty_string(self):
        """Test with empty string."""
        assert format_text("") == ""

    def test_whitespace_trimming(self):
        """Test that leading and trailing whitespace is removed."""
        assert format_text("\n  text with spaces  \t") == "text with spaces"


class TestValidateInput:
    """Tests for validate_input function."""

    def test_valid_input(self):
        """Test with valid input."""
        assert validate_input("test", min_length=1) is True

    def test_too_short(self):
        """Test with input too short."""
        assert validate_input("", min_length=1) is False

    def test_too_long(self):
        """Test with input too long."""
        assert validate_input("toolong", min_length=1, max_length=5) is False

    def test_exact_length(self):
        """Test with exact length match."""
        assert validate_input("exact", min_length=5, max_length=5) is True


class TestFormatCategoryName:
    """Tests for format_category_name function."""

    def test_snake_case_to_title(self):
        """Test converting snake_case to Title Case."""
        assert format_category_name("programming_languages") == "Programming Languages"

    def test_single_word(self):
        """Test with single word."""
        assert format_category_name("python") == "Python"

    def test_multiple_underscores(self):
        """Test with multiple underscores."""
        assert format_category_name("backend_frameworks_and_tools") == "Backend Frameworks And Tools"

    def test_empty_string(self):
        """Test with empty string."""
        assert format_category_name("") == ""


class TestSafeGet:
    """Tests for safe_get function."""

    def test_key_exists(self):
        """Test getting existing key."""
        data = {"name": "John", "age": 30}
        assert safe_get(data, "name") == "John"

    def test_key_missing_default(self):
        """Test missing key returns default."""
        data = {"name": "John"}
        assert safe_get(data, "email") == "N/A"

    def test_key_missing_custom_default(self):
        """Test missing key returns custom default."""
        data = {"name": "John"}
        assert safe_get(data, "email", "Not provided") == "Not provided"

    def test_empty_dict(self):
        """Test with empty dictionary."""
        assert safe_get({}, "key") == "N/A"

    def test_none_value(self):
        """Test when value is None."""
        data = {"name": None}
        assert safe_get(data, "name") is None