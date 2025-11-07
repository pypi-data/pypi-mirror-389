"""Core text normalization functions."""

import re
import unicodedata


def normalize_unicode(text: str, form: str = "NFKC") -> str:
    """Normalize Unicode text."""
    return unicodedata.normalize(form, text)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace to single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def remove_accents(text: str) -> str:
    """Remove accents from characters."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def normalize_line_endings(text: str, ending: str = "\n") -> str:
    """Normalize line endings."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if ending != "\n":
        text = text.replace("\n", ending)
    return text


def normalize_case(text: str, case: str = "lower") -> str:
    """Normalize text case."""
    if case == "lower":
        return text.lower()
    elif case == "upper":
        return text.upper()
    elif case == "title":
        return text.title()
    return text

