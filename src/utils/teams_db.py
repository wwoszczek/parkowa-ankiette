"""
Functions for handling teams in the database
"""

import streamlit as st
import uuid
from src.database import NeonDB


def save_teams(db: NeonDB, game_id: str, teams: dict):
    """Saves team lineups to database"""
    try:
        # Remove previous lineups for this game
        db.execute_query("DELETE FROM teams WHERE game_id = %s", (game_id,))
        
        # Add new lineups
        for color, players in teams.items():
            team_id = str(uuid.uuid4())
            db.execute_query(
                "INSERT INTO teams (id, game_id, team_color, players) VALUES (%s, %s, %s, %s)",
                (team_id, game_id, color, str(players))  # Store players as JSON string
            )
        return True
    except Exception as e:
        st.error(f"Błąd podczas zapisywania składów: {e}")
        return False


def get_teams_for_game(db: NeonDB, game_id: str):
    """Gets team lineups for a given game"""
    try:
        return db.execute_query("SELECT * FROM teams WHERE game_id = %s", (game_id,))
    except Exception as e:
        st.error(f"Błąd podczas pobierania składów: {e}")
        return []
