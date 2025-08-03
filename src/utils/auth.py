"""
Functions for password hashing and verification
"""

import bcrypt


def hash_password(password: str) -> str:
    """Password hashing"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Password verification"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
