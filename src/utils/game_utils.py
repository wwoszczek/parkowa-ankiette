"""
Functions for handling games in the database
"""

import streamlit as st
import uuid
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.datetime_utils import get_next_game_time


def create_new_game_if_needed(supabase: Client):
    """Creates new game if needed"""
    try:
        next_game = get_next_game_time()
        
        # Check if active game already exists for this day
        response = supabase.table('games').select('*').eq('active', True).execute()
        
        active_games = [game for game in response.data 
                       if datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE).date() == next_game.date()]
        
        if not active_games:
            # Create new game
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
    """Deactivates games that have already taken place"""
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
    """Gets active games"""
    try:
        response = supabase.table('games').select('*').eq('active', True).order('start_time').execute()
        return response.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania gierek: {e}")
        return []


def get_past_games(supabase: Client):
    """Gets inactive games (history)"""
    try:
        response = supabase.table('games').select('*').eq('active', False).order('start_time', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania historii gierek: {e}")
        return []
