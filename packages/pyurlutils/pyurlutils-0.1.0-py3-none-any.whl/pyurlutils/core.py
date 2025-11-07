"""Core URL utility functions."""

from urllib.parse import urlencode, parse_qs, quote, unquote


def encode_url(text: str) -> str:
    """URL encode text."""
    return quote(text)


def decode_url(text: str) -> str:
    """URL decode text."""
    return unquote(text)


def parse_query(query_string: str) -> dict:
    """Parse query string."""
    return parse_qs(query_string)
