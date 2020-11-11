"""
Application: Maitenotas
Made by Taksan Tong
https://github.com/maitelab/maitenotas_v4

Functions related to encrypt / decrypt data """
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet


def generateUserKey(userPassword: str) -> Fernet:
    """Create a key for encryption/decryption purposes"""
    password_provided_bytes = bytes(userPassword, 'utf-8')
    password = userPassword.encode()  # Convert to type bytes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=password_provided_bytes,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))  # Can only use kdf once
    fernet_key = Fernet(key)
    return fernet_key


def encryptTextToData(input_text: str, user_key: Fernet) -> bytes:
    """Encrypt text"""
    message_data = input_text.encode(encoding='UTF-8')
    encrypted_data = user_key.encrypt(message_data)
    return encrypted_data


def decryptDataToText(input_data: bytes, user_key: Fernet) -> str:
    """Decrypt data to clear text"""
    decrypted_data = user_key.decrypt(input_data)
    clear_text = decrypted_data.decode(encoding='UTF-8')
    return clear_text
