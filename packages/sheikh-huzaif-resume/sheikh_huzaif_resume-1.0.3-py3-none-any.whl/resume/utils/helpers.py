"""Helper utility functions."""

from typing import Optional


def format_text(text: str, uppercase: bool = False) -> str:
    """
    Format text with optional transformations.

    Args:
        text: The text to format
        uppercase: Whether to convert to uppercase

    Returns:
        Formatted text
    """
    result = text.strip()
    if uppercase:
        result = result.upper()
    return result


def validate_input(value: str, min_length: int = 1, max_length: Optional[int] = None) -> bool:
    """
    Validate input string length.

    Args:
        value: The input to validate
        min_length: Minimum required length
        max_length: Maximum allowed length (optional)

    Returns:
        True if valid, False otherwise
    """
    if len(value) < min_length:
        return False
    if max_length and len(value) > max_length:
        return False
    return True


def format_category_name(name: str) -> str:
    """
    Convert snake_case category names to Title Case.

    Args:
        name: The category name in snake_case (e.g., 'programming_languages')

    Returns:
        Formatted title case string (e.g., 'Programming Languages')
    """
    return name.replace("_", " ").title()


def safe_get(data: dict, key: str, default: str = "N/A") -> str:
    """
    Safely get a value from a dictionary with a default fallback.

    Args:
        data: The dictionary to retrieve from
        key: The key to look up
        default: Default value if key not found

    Returns:
        The value or default
    """
    return data.get(key, default)