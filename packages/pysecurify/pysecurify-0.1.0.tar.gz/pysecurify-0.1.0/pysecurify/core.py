"""Core security functions."""

import hashlib
import secrets


def hash_password(password: str, salt: str = None) -> str:
    """Hash password."""
    if salt is None:
        salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest() + ":" + salt


def encrypt(text: str, key: str) -> str:
    """Simple encryption (XOR)."""
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))


def decrypt(text: str, key: str) -> str:
    """Simple decryption."""
    return encrypt(text, key)
