from app.core.security import hash_password, verify_password
from datetime import timedelta

import pytest
from jose import ExpiredSignatureError, JWTError

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_password_does_not_store_plain_text():
    password = "EmeraldWave123!"

    hashed = hash_password(password)

    assert hashed != password


def test_verify_password_accepts_correct_password():
    password = "EmeraldWave123!"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("EmeraldWave123!")

    assert verify_password("WrongPassword", hashed,) is False


def test_create_and_decode_access_token():
    token = create_access_token(
        subject="42",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert "exp" in payload


def test_access_token_rejects_tampering():
    token = create_access_token(
        subject="42",
    )

    tampered_token = token[:-1] + (
        "a" if token[-1] != "a" else "b"
    )

    with pytest.raises(JWTError):
        decode_access_token(tampered_token)


def test_expired_access_token_is_rejected():
    token = create_access_token(subject="42", expires_delta=timedelta(seconds=-1))

    with pytest.raises(ExpiredSignatureError):
        decode_access_token(token)