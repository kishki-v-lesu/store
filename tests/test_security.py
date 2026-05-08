import pytest
from datetime import datetime, timezone, timedelta

from auth_service.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)

pytestmark = pytest.mark.asyncio


class TestPasswordHashing:
    def test_hash_password(self):
        password = "TestPassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert hashed.startswith("$pbkdf2-sha256$")

    def test_verify_password_correct(self):
        password = "TestPassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_password_truncation(self):
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True


class TestJWTTokens:
    def test_create_access_token(self):
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload

    def test_create_refresh_token(self):
        data = {"sub": "123"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        invalid_token = "invalid.token.here"
        payload = decode_token(invalid_token)
        assert payload is None

    def test_token_expiration(self):
        data = {"sub": "123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)
        assert payload is None

    def test_refresh_token_has_jti(self):
        data = {"sub": "123"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert "jti" in payload

    def test_different_tokens_have_different_jti(self):
        data = {"sub": "123"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        assert payload1["jti"] != payload2["jti"]


class TestPasswordValidation:
    def test_short_password_rejected(self):
        from pydantic import ValidationError
        from auth_service.app.schemas.auth import UserCreate
        
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="12345",
                first_name="Test",
                last_name="User",
            )

    def test_valid_password_accepted(self):
        from auth_service.app.schemas.auth import UserCreate
        
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePassword123!",
            first_name="Test",
            last_name="User",
        )
        assert user.password == "SecurePassword123!"

    def test_email_validation(self):
        from pydantic import ValidationError
        from auth_service.app.schemas.auth import UserCreate
        
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="SecurePassword123!",
                first_name="Test",
                last_name="User",
            )