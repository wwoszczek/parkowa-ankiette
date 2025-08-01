"""
Funkcje do obsługi drużyn w bazie danych
"""

import streamlit as st
import uuid
from supabase import Client


def save_teams(supabase: Client, game_id: str, teams: dict):
    """Zapisuje składy drużyn do bazy"""
    try:
        # Usuń poprzednie składy dla tej gierki
        supabase.table('teams').delete().eq('game_id', game_id).execute()
        
        # Dodaj nowe składy
        for color, players in teams.items():
            team = {
                'id': str(uuid.uuid4()),
                'game_id': game_id,
                'team_color': color,
                'players': players
            }
            supabase.table('teams').insert(team).execute()
        return True
    except Exception as e:
        st.error(f"Błąd podczas zapisywania składów: {e}")
        return False


def get_teams_for_game(supabase: Client, game_id: str):
    """Pobiera składy drużyn dla danej gierki"""
    try:
        response = supabase.table('teams').select('*').eq('game_id', game_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania składów: {e}")
        return []
