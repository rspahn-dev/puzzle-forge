import os

from cryptography.fernet import Fernet


def _get_fernet():
    key = os.environ.get("APP_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("APP_ENCRYPTION_KEY is not set")
    return Fernet(key.encode())


def encrypt_api_key(plaintext: str) -> bytes:
    return _get_fernet().encrypt(plaintext.encode())


def decrypt_api_key(ciphertext: bytes) -> str:
    return _get_fernet().decrypt(ciphertext).decode()
