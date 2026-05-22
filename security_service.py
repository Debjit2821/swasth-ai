from cryptography.fernet import (
    Fernet
)

import hashlib

# CREATE ENCRYPTION KEY

def generate_key():

    return Fernet.generate_key()

# ENCRYPT REPORT

def encrypt_report(
    report,
    key
):

    fernet = Fernet(key)

    encrypted = (
        fernet.encrypt(
            report.encode()
        )
    )

    return encrypted.decode()

# DECRYPT REPORT

def decrypt_report(
    encrypted_report,
    key
):

    fernet = Fernet(key)

    decrypted = (
        fernet.decrypt(
            encrypted_report.encode()
        )
    )

    return decrypted.decode()

# HASH FUNCTION

def generate_hash(text):

    return hashlib.sha256(
        text.encode()
    ).hexdigest()