# src/database/utils.py
from __future__ import annotations
import hashlib


def hash_password(password: str) -> str:
    """Return a stable SHA-256 hash for a plaintext password.
    Note: will migrate to bycrypt in future development.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

