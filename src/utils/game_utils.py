"""
Funkcje do obsługi gierek w bazie danych
"""

import streamlit as st
import uuid
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.datetime_utils import get_next_game_time


def create_new_game_if_needed(supabase: Client):
    """Tworzy nową gierkę jeśli potrzeba"""
    try:
        next_game = get_next_game_time()
        
        # Sprawdź czy już istnieje aktywna gierka na ten dzień
        response = supabase.table('games').select('*').eq('active', True).execute()
        
        active_games = [game for game in response.data 
                       if datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE).date() == next_game.date()]
        
        if not active_games:
            # Utwórz nową gierkę
            new_game = {
                'id': str(uuid.uuid4()),
                'start_time': next_game.isoformat(),
                'active': True
            }
            supabase.table('games').insert(new_game).execute()
            return new_game
        
        return active_games[0]
    except Exception as e:
        st.error(f"Błąd podczas tworzenia nowej gierki: {e}")
        return None


def deactivate_past_games(supabase: Client):
    """Dezaktywuje gierki, które już się odbyły"""
    try:
        now = datetime.now(TIMEZONE)
        response = supabase.table('games').select('*').eq('active', True).execute()
        
        for game in response.data:
            game_time = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE)
            if game_time <= now:
                supabase.table('games').update({'active': False}).eq('id', game['id']).execute()
    except Exception as e:
        st.error(f"Błąd podczas dezaktywacji gierek: {e}")


def get_active_games(supabase: Client):
    """Pobiera aktywne gierki"""
    try:
        response = supabase.table('games').select('*').eq('active', True).order('start_time').execute()
        return response.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania gierek: {e}")
        return []


def get_past_games(supabase: Client):
    """Pobiera nieaktywne gierki (historia)"""
    try:
        response = supabase.table('games').select('*').eq('active', False).order('start_time', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania historii gierek: {e}")
        return []
