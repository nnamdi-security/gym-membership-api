from app.core.security import (
    hash_password,
    verify_password,
)


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

    assert verify_password(
        "WrongPassword",
        hashed,
    ) is False