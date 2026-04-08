"""
Functions for handling teams in the database
"""

import streamlit as st
import uuid
import json
import ast
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
                (
                    team_id,
                    game_id,
                    color,
                    json.dumps(players),
                ),  # Store players as JSON string
            )
        return True
    except Exception as e:
        st.error(f"Błąd podczas zapisywania składów: {e}")
        return False


def get_teams_for_game(db: SupabaseDB, game_id: str):
    """Gets team lineups for a given game"""
    try:
        teams_data = db.execute_query(
            "SELECT * FROM teams WHERE game_id = %s", (game_id,)
        )
        if not teams_data:
            return []

        def normalize_players(players_value):
            """Normalizes various DB formats into a list of player nicknames."""
            if players_value is None:
                return []

            if isinstance(players_value, list):
                return [str(player) for player in players_value if player is not None]

            if isinstance(players_value, tuple):
                return [str(player) for player in players_value if player is not None]

            if isinstance(players_value, str):
                players_str = players_value.strip()
                if not players_str:
                    return []

                # Preferred format: JSON array string.
                try:
                    parsed = json.loads(players_str)
                    if isinstance(parsed, list):
                        return [str(player) for player in parsed if player is not None]
                    if isinstance(parsed, str):
                        return [parsed] if parsed else []
                except json.JSONDecodeError:
                    pass

                # Legacy format: Python-like list string "['name1', 'name2']".
                if players_str.startswith("[") and players_str.endswith("]"):
                    try:
                        parsed = ast.literal_eval(players_str)
                        if isinstance(parsed, list):
                            return [
                                str(player) for player in parsed if player is not None
                            ]
                        return [str(parsed)] if parsed is not None else []
                    except Exception:
                        return [
                            p.strip(" '\"[]")
                            for p in players_str.split(",")
                            if p.strip(" '\"[]")
                        ]

                # Single nickname saved as plain text.
                return [players_str]

            # Fallback for unexpected types.
            return [str(players_value)]

        # Parse players data back to Python lists (supports JSON strings and legacy formats)
        for team in teams_data:
            players_value = team.get("players")
            team["players"] = normalize_players(players_value)

        return teams_data
    except Exception as e:
        st.error(f"Błąd podczas pobierania składów: {e}")
        return []
