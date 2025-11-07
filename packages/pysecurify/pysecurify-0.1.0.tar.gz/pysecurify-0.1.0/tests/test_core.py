"""Tests for pysecurify core functions."""

from pysecurify import hash_password, encrypt, decrypt


def test_hash_password():
    result = hash_password("password")
    assert ":" in result


def test_encrypt_decrypt():
    text = "hello"
    key = "secret"
    encrypted = encrypt(text, key)
    decrypted = decrypt(encrypted, key)
    assert decrypted == text
