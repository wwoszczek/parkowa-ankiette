"""
Functions for handling teams in the database
"""

import streamlit as st
import uuid
from supabase import Client


def save_teams(supabase: Client, game_id: str, teams: dict):
    """Saves team lineups to database"""
    try:
        # Remove previous lineups for this game
        supabase.table('teams').delete().eq('game_id', game_id).execute()
        
        # Add new lineups
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
    """Gets team lineups for a given game"""
    try:
        response = supabase.table('teams').select('*').eq('game_id', game_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania składów: {e}")
        return []
