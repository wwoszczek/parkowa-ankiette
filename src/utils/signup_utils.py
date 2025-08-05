"""
Functions for handling player signups
"""

import streamlit as st
import uuid
from datetime import datetime
from src.database import NeonDB
from src.constants import TIMEZONE
from src.utils.auth import hash_password, verify_password
from src.utils.security import sanitize_input, log_security_event


def get_signups_for_game(db: NeonDB, game_id: str):
    """Gets signups for a given game"""
    try:
        return db.execute_query(
            "SELECT * FROM signups WHERE game_id = %s ORDER BY timestamp",
            (game_id,)
        )
    except Exception as e:
        st.error(f"Błąd podczas pobierania zapisów: {e}")
        return []


def add_signup(db: NeonDB, game_id: str, nickname: str, password: str):
    """Adds player signup"""
    try:
        # Data sanitization
        nickname = sanitize_input(nickname)
        password = sanitize_input(password)
        
        # Check if nickname already exists in this game
        existing = db.execute_query(
            "SELECT * FROM signups WHERE game_id = %s AND nickname = %s",
            (game_id, nickname)
        )
        if existing:
            log_security_event("duplicate_signup_attempt", f"nickname: {nickname}, game: {game_id[:8]}...")
            return False, "Ten nickname jest już zajęty w tej gierce!"
        
        # Add signup
        signup_id = str(uuid.uuid4())
        db.execute_query(
            "INSERT INTO signups (id, game_id, nickname, password_hash, timestamp) VALUES (%s, %s, %s, %s, %s)",
            (signup_id, game_id, nickname, hash_password(password), datetime.now(TIMEZONE).isoformat())
        )
        return True, "Zapisano pomyślnie!"
    except Exception as e:
        error_msg = str(e)
        # Don't log full error if it may contain sensitive data
        safe_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
        log_security_event("signup_error", f"error: {safe_error}")
        return False, f"Błąd podczas zapisu: {safe_error}"


def remove_signup(db: NeonDB, game_id: str, nickname: str, password: str):
    """Removes player signup"""
    try:
        # Data sanitization
        nickname = sanitize_input(nickname)
        password = sanitize_input(password)
        
        # Find signup
        signups = db.execute_query(
            "SELECT * FROM signups WHERE game_id = %s AND nickname = %s",
            (game_id, nickname)
        )
        if not signups:
            return False, "Nie znaleziono zapisu z tym nickiem!"
        
        signup = signups[0]
        if not verify_password(password, signup['password_hash']):
            log_security_event("invalid_password_attempt", f"nickname: {nickname}, game: {game_id[:8]}...")
            return False, "Nieprawidłowe hasło!"
        
        # Remove signup
        db.execute_query("DELETE FROM signups WHERE id = %s", (signup['id'],))
        return True, "Wypisano pomyślnie!"
    except Exception as e:
        error_msg = str(e)
        safe_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
        log_security_event("signout_error", f"error: {safe_error}")
        return False, f"Błąd podczas wypisywania: {safe_error}"
