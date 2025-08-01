"""
Funkcje do obsługi zapisów graczy
"""

import streamlit as st
import uuid
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.auth import hash_password, verify_password


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
        # Sprawdź czy nickname już istnieje w tej gierce
        existing = supabase.table('signups').select('*').eq('game_id', game_id).eq('nickname', nickname).execute()
        if existing.data:
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
        return False, f"Błąd podczas zapisu: {e}"


def remove_signup(supabase: Client, game_id: str, nickname: str, password: str):
    """Usuwa zapis gracza"""
    try:
        # Znajdź zapis
        response = supabase.table('signups').select('*').eq('game_id', game_id).eq('nickname', nickname).execute()
        if not response.data:
            return False, "Nie znaleziono zapisu z tym nickiem!"
        
        signup = response.data[0]
        if not verify_password(password, signup['password_hash']):
            return False, "Nieprawidłowe hasło!"
        
        # Usuń zapis
        supabase.table('signups').delete().eq('id', signup['id']).execute()
        return True, "Wypisano pomyślnie!"
    except Exception as e:
        return False, f"Błąd podczas wypisywania: {e}"
