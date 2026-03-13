from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify():
    password = "strong-password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_jwt_round_trip():
    token = create_access_token({"sub": "12", "tenant_id": 3, "role": "student"})
    payload = decode_access_token(token)
    assert payload["sub"] == "12"
    assert payload["tenant_id"] == 3
    assert payload["role"] == "student"
