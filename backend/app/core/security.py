"""Password hashing for saved score sets.

Uses only the standard library (PBKDF2-HMAC-SHA256 with a per-record random
salt) so the project gains password protection without a new dependency or an
ABI-sensitive native wheel. Hashes are self-describing strings of the form::

    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

Verification is constant-time (:func:`hmac.compare_digest`).
"""

from __future__ import annotations

import hashlib
import hmac
import os

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 240_000
_SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
    """Return a self-describing PBKDF2 hash of ``password``."""
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_ALGORITHM}${iterations}${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Return True iff ``password`` matches the previously stored ``encoded`` hash."""
    try:
        algorithm, iterations_s, salt_hex, hash_hex = encoded.split("$")
    except ValueError:
        return False
    if algorithm != _ALGORITHM:
        return False
    try:
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(derived, expected)
