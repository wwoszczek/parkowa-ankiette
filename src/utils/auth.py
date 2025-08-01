"""
Funkcje do hashowania i weryfikacji haseł
"""

import bcrypt


def hash_password(password: str) -> str:
    """Hashowanie hasła"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Weryfikacja hasła"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
