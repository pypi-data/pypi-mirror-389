"""Tests for pytextutils core functions."""

import pytest
from pytextutils import (
    reverse_string,
    slugify,
    capitalize_words,
    remove_punctuation,
    remove_whitespace,
    truncate,
    word_count,
    is_palindrome,
)


def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""


def test_slugify():
    assert slugify("Hello World") == "hello-world"
    assert slugify("Test@#$%") == "test"


def test_capitalize_words():
    assert capitalize_words("hello world") == "Hello World"


def test_remove_punctuation():
    assert remove_punctuation("Hello, World!") == "Hello World"


def test_remove_whitespace():
    assert remove_whitespace("hello world") == "helloworld"


def test_truncate():
    assert truncate("hello world", 8) == "hello..."
    assert truncate("hi", 10) == "hi"


def test_word_count():
    assert word_count("hello world") == 2
    assert word_count("") == 0


def test_is_palindrome():
    assert is_palindrome("racecar") is True
    assert is_palindrome("hello") is False
    assert is_palindrome("A man a plan a canal Panama") is True

