import jwt

from app.config import get_settings
from app.security import create_access_token, hash_password, verify_password


def test_password_hash_round_trip() -> None:
    digest = hash_password("A-secure-password-123")
    assert verify_password("A-secure-password-123", digest)
    assert not verify_password("wrong-password", digest)


def test_access_token_contains_user_and_roles() -> None:
    token, expires_in = create_access_token("user-123", ["ADMIN"])
    payload = jwt.decode(token, get_settings().jwt_secret.get_secret_value(), algorithms=[get_settings().jwt_algorithm])
    assert payload["sub"] == "user-123"
    assert payload["roles"] == ["ADMIN"]
    assert expires_in > 0
