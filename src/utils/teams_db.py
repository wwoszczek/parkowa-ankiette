"""
Functions for handling teams in the database
"""

import logging
import streamlit as st
import uuid
import json
import ast
from src.database import SupabaseDB

logger = logging.getLogger(__name__)


def save_teams(db: SupabaseDB, game_id: str, teams: dict):
    """Saves team lineups to database. Runs as a single transaction so the
    previous lineups are replaced atomically (no partial state on failure)."""
    connection = None
    try:
        connection = db.get_connection()
        with connection.cursor() as cur:
            # Remove previous lineups for this game
            cur.execute("DELETE FROM teams WHERE game_id = %s", (game_id,))
            # Add new lineups (players stored as a JSON string)
            cur.executemany(
                "INSERT INTO teams (id, game_id, team_color, players) VALUES (%s, %s, %s, %s)",
                [
                    (str(uuid.uuid4()), game_id, color, json.dumps(players))
                    for color, players in teams.items()
                ],
            )
        connection.commit()
        return True
    except Exception:
        if connection and not connection.closed:
            connection.rollback()
        logger.exception("Failed to save teams")
        st.error("Błąd podczas zapisywania składów")
        return False
    finally:
        if connection and not connection.closed:
            connection.close()


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
    except Exception:
        st.error("Błąd podczas pobierania składów")
        return []
