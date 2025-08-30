"""
Functions for handling teams in the database
"""

import streamlit as st
import uuid
import json
from src.database import SupabaseDB


def save_teams(db: SupabaseDB, game_id: str, teams: dict):
    """Saves team lineups to database"""
    try:
        # Remove previous lineups for this game
        db.execute_query("DELETE FROM teams WHERE game_id = %s", (game_id,))
        
        # Add new lineups
        for color, players in teams.items():
            team_id = str(uuid.uuid4())
            db.execute_query(
                "INSERT INTO teams (id, game_id, team_color, players) VALUES (%s, %s, %s, %s)",
                (team_id, game_id, color, json.dumps(players))  # Store players as JSON string
            )
        return True
    except Exception as e:
        st.error(f"Błąd podczas zapisywania składów: {e}")
        return False


def get_teams_for_game(db: SupabaseDB, game_id: str):
    """Gets team lineups for a given game"""
    try:
        teams_data = db.execute_query("SELECT * FROM teams WHERE game_id = %s", (game_id,))
        if not teams_data:
            return []
        
        # Parse JSON players data back to lists
        for team in teams_data:
            try:
                team['players'] = json.loads(team['players'])
            except (json.JSONDecodeError, TypeError):
                # Fallback for old string format data
                players_str = team['players']
                if players_str.startswith('[') and players_str.endswith(']'):
                    # Try to parse old format: "['name1', 'name2']"
                    import ast
                    try:
                        team['players'] = ast.literal_eval(players_str)
                    except:
                        # If all else fails, split by comma and clean
                        team['players'] = [p.strip(" '\"[]") for p in players_str.split(',')]
                else:
                    # Single player or malformed data
                    team['players'] = [players_str] if players_str else []
        
        return teams_data
    except Exception as e:
        st.error(f"Błąd podczas pobierania składów: {e}")
        return []
