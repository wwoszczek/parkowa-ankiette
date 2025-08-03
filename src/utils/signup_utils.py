"""
Funkcje do obsługi zapisów graczy
"""

import streamlit as st
import uuid
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.auth import hash_password, verify_password
from src.utils.security import sanitize_input, log_security_event


def get_signups_for_game(supabase: Client, game_id: str):
    """Pobiera zapisy na daną gierkę"""
    try:
        response = supabase.table('signups').select('*').eq('game_id', game_id).order('timestamp').execute()
        return response.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania zapisów: {e}")
        return []


def add_signup(supabase: Client, game_id: str, nickname: str, password: str):
    """Dodaje zapis gracza"""
    try:
        # Sanityzacja danych
        nickname = sanitize_input(nickname)
        password = sanitize_input(password)
        
        # Sprawdź czy nickname już istnieje w tej gierce
        existing = supabase.table('signups').select('*').eq('game_id', game_id).eq('nickname', nickname).execute()
        if existing.data:
            log_security_event("duplicate_signup_attempt", f"nickname: {nickname}, game: {game_id[:8]}...")
            return False, "Ten nickname jest już zajęty w tej gierce!"
        
        # Dodaj zapis
        signup = {
            'id': str(uuid.uuid4()),
            'game_id': game_id,
            'nickname': nickname,
            'password_hash': hash_password(password),
            'timestamp': datetime.now(TIMEZONE).isoformat()
        }
        supabase.table('signups').insert(signup).execute()
        return True, "Zapisano pomyślnie!"
    except Exception as e:
        error_msg = str(e)
        # Nie loguj pełnego błędu jeśli może zawierać wrażliwe dane
        safe_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
        log_security_event("signup_error", f"error: {safe_error}")
        return False, f"Błąd podczas zapisu: {safe_error}"


def remove_signup(supabase: Client, game_id: str, nickname: str, password: str):
    """Usuwa zapis gracza"""
    try:
        # Sanityzacja danych
        nickname = sanitize_input(nickname)
        password = sanitize_input(password)
        
        # Znajdź zapis
        response = supabase.table('signups').select('*').eq('game_id', game_id).eq('nickname', nickname).execute()
        if not response.data:
            return False, "Nie znaleziono zapisu z tym nickiem!"
        
        signup = response.data[0]
        if not verify_password(password, signup['password_hash']):
            log_security_event("invalid_password_attempt", f"nickname: {nickname}, game: {game_id[:8]}...")
            return False, "Nieprawidłowe hasło!"
        
        # Usuń zapis
        supabase.table('signups').delete().eq('id', signup['id']).execute()
        return True, "Wypisano pomyślnie!"
    except Exception as e:
        error_msg = str(e)
        safe_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
        log_security_event("signout_error", f"error: {safe_error}")
        return False, f"Błąd podczas wypisywania: {safe_error}"
