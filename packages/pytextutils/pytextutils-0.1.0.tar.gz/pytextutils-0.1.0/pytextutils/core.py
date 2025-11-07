"""Core string utility functions."""

import re
import string


def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


def slugify(text: str, separator: str = "-") -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", separator, text)
    return text.strip(separator)


def capitalize_words(text: str) -> str:
    """Capitalize first letter of each word."""
    return text.title()


def remove_punctuation(text: str) -> str:
    """Remove all punctuation from text."""
    return text.translate(str.maketrans("", "", string.punctuation))


def remove_whitespace(text: str) -> str:
    """Remove all whitespace from text."""
    return re.sub(r"\s+", "", text)


def truncate(text: str, length: int, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= length:
        return text
    return text[: length - len(suffix)] + suffix


def word_count(text: str) -> int:
    """Count words in text."""
    words = text.split()
    return len(words)


def is_palindrome(text: str) -> bool:
    """Check if text is a palindrome."""
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text.lower())
    return cleaned == cleaned[::-1]

