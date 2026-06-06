"""Tests for password hashing used by saved score sets."""

from __future__ import annotations

from app.core.security import hash_password, verify_password


def test_hash_roundtrip_accepts_correct_password() -> None:
    encoded = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", encoded) is True


def test_hash_rejects_wrong_password() -> None:
    encoded = hash_password("s3cret")
    assert verify_password("s3cre", encoded) is False
    assert verify_password("", encoded) is False


def test_hashes_are_salted_and_unique() -> None:
    a = hash_password("same")
    b = hash_password("same")
    assert a != b  # random per-record salt
    assert verify_password("same", a)
    assert verify_password("same", b)


def test_verify_tolerates_malformed_encoding() -> None:
    assert verify_password("anything", "not-a-valid-hash") is False
    assert verify_password("anything", "pbkdf2_sha256$abc$def") is False
