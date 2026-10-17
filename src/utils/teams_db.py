"""
Functions for handling teams in the database
"""

import logging
import streamlit as st
import uuid
import json
import ast
from src.database import SupabaseDB
from src.utils.team_utils import sort_teams

logger = logging.getLogger(__name__)


def save_squads(db: SupabaseDB, game_id: str, teams: dict, email: str, admin: bool = False):
    """Saves the game's squads, first come first served: the account that saves
    them owns them, and until it deletes them nobody else (admins aside) can
    save new ones. One transaction with the game row locked, so two setters
    approving at the same moment cannot both win. Returns (ok, message)."""
    connection = None
    try:
        connection = db.get_connection()
        with connection.cursor() as cur:
            cur.execute("SELECT id FROM games WHERE id = %s FOR UPDATE", (game_id,))
            cur.execute("SELECT created_by_email FROM teams WHERE game_id = %s", (game_id,))
            existing = cur.fetchall()
            owner = squads_owner(existing)
            if existing and not admin and (owner or "").lower() != email.lower():
                connection.rollback()
                return False, "Składy na tę gierkę zdążył już zapisać ktoś inny"
            # An admin editing someone's squads leaves them with their owner.
            owner = owner or email
            cur.execute("DELETE FROM teams WHERE game_id = %s", (game_id,))
            # Players stored as a JSON string
            cur.executemany(
                "INSERT INTO teams (id, game_id, team_color, players, created_by_email) "
                "VALUES (%s, %s, %s, %s, %s)",
                [
                    (str(uuid.uuid4()), game_id, color, json.dumps(players), owner)
                    for color, players in teams.items()
                ],
            )
        connection.commit()
        return True, "Składy zapisane — widzą je wszyscy"
    except Exception:
        if connection and not connection.closed:
            connection.rollback()
        logger.exception("Failed to save squads")
        return False, "Błąd podczas zapisywania składów"
    finally:
        if connection and not connection.closed:
            connection.close()


def delete_squads(db: SupabaseDB, game_id: str, email: str, admin: bool = False):
    """Deletes the game's squads (their owner or an admin only), so anyone can
    set new ones. Returns (ok, message)."""
    try:
        deleted = db.execute_query(
            "DELETE FROM teams WHERE game_id = %s AND (%s OR LOWER(created_by_email) = LOWER(%s))",
            (game_id, admin, email)
        )
        if deleted:
            return True, "Składy usunięte — każdy może teraz ustalić nowe"
        if db.execute_query("SELECT 1 FROM teams WHERE game_id = %s", (game_id,)):
            return False, "Składy może usunąć tylko osoba, która je ustaliła, albo admin"
        return False, "Tych składów już nie ma"
    except Exception:
        logger.exception("Failed to delete squads")
        return False, "Błąd podczas usuwania składów"


def rename_in_squads(db: SupabaseDB, game_id: str, old: str, new: str):
    """Follow a renamed signup in the game's saved squads."""
    for row in db.execute_query("SELECT id, players FROM teams WHERE game_id = %s", (game_id,)) or []:
        players = _normalize_players(row["players"])
        if old in players:
            db.execute_query(
                "UPDATE teams SET players = %s WHERE id = %s",
                (json.dumps([new if p == old else p for p in players]), row["id"])
            )


def squads_owner(teams_data):
    """E-mail of the account that set the squads (None for legacy draws)."""
    return next((t["created_by_email"] for t in teams_data if t.get("created_by_email")), None)


def squads_of(teams_data) -> dict:
    """{team_color: [players]} in the configured colour order."""
    return sort_teams({t["team_color"]: t["players"] for t in teams_data})


def _normalize_players(players_value):
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


def get_squads_between(db: SupabaseDB, start, end) -> dict:
    """{game_id: {team_color: [players]}} for games starting within [start, end)."""
    rows = db.execute_query(
        "SELECT t.game_id, t.team_color, t.players FROM teams t "
        "JOIN games g ON g.id = t.game_id WHERE g.start_time >= %s AND g.start_time < %s",
        (start, end)
    ) or []
    squads = {}
    for row in rows:
        squads.setdefault(row["game_id"], {})[row["team_color"]] = _normalize_players(row["players"])
    return squads


def get_teams_for_game(db: SupabaseDB, game_id: str):
    """Gets team lineups for a given game"""
    try:
        teams_data = db.execute_query(
            "SELECT * FROM teams WHERE game_id = %s", (game_id,)
        )
        if not teams_data:
            return []

        # Parse players data back to Python lists (supports JSON strings and legacy formats)
        for team in teams_data:
            players_value = team.get("players")
            team["players"] = _normalize_players(players_value)

        return teams_data
    except Exception:
        st.error("Błąd podczas pobierania składów")
        return []
