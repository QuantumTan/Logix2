# src/database/utils.py
from __future__ import annotations
import hashlib


def hash_password(password: str) -> str:
    """Return a stable SHA-256 hash for a plaintext password.
    Note: For production, consider using a stronger key derivation (bcrypt/argon2).
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

