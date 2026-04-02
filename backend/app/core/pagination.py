import base64


def encode_cursor(last_id: int) -> str:
    raw = str(last_id).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_cursor(cursor: str) -> int:
    padding = "=" * ((4 - len(cursor) % 4) % 4)
    decoded = base64.urlsafe_b64decode((cursor + padding).encode("utf-8")).decode("utf-8")
    value = int(decoded)
    if value <= 0:
        raise ValueError("Cursor must be a positive integer")
    return value
