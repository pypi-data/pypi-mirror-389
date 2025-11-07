"""Tests for pyurlutils core functions."""

from pyurlutils import encode_url, decode_url, parse_query


def test_encode_url():
    assert encode_url("hello world") == "hello%20world"


def test_decode_url():
    assert decode_url("hello%20world") == "hello world"
