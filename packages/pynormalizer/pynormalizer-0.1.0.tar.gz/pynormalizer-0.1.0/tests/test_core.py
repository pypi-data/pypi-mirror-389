"""Tests for pynormalizer core functions."""

from pynormalizer import (
    normalize_unicode,
    normalize_whitespace,
    remove_accents,
    normalize_line_endings,
    normalize_case,
)


def test_normalize_whitespace():
    assert normalize_whitespace("hello    world") == "hello world"
    assert normalize_whitespace("  test  ") == "test"


def test_remove_accents():
    assert remove_accents("café") == "cafe"
    assert remove_accents("naïve") == "naive"


def test_normalize_line_endings():
    assert normalize_line_endings("hello\r\nworld") == "hello\nworld"
    assert normalize_line_endings("hello\rworld") == "hello\nworld"


def test_normalize_case():
    assert normalize_case("Hello", "lower") == "hello"
    assert normalize_case("hello", "upper") == "HELLO"
    assert normalize_case("hello world", "title") == "Hello World"

