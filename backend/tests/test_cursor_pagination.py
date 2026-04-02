import pytest

from app.core.pagination import decode_cursor, encode_cursor


def test_cursor_round_trip():
    cursor = encode_cursor(123)
    assert decode_cursor(cursor) == 123


def test_cursor_invalid_raises():
    with pytest.raises(ValueError):
        decode_cursor("not-a-valid-token")
