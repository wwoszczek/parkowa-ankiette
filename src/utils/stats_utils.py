"""
Season-based signup statistics (most active players).
"""

from datetime import datetime

import streamlit as st

from src.constants import TIMEZONE
from src.database import SupabaseDB
from src.utils.datetime_utils import parse_game_time, season_bounds


def list_seasons(db: SupabaseDB) -> list:
    """Seasons that contain at least one already-played game, newest first."""
    try:
        rows = db.execute_query(
            "SELECT start_time FROM games WHERE start_time < %s",
            (datetime.now(TIMEZONE),)
        ) or []
    except Exception as e:
        st.error(f"Błąd podczas pobierania sezonów: {e}")
        return []

    seasons = {}
    for row in rows:
        s = season_bounds(parse_game_time(row["start_time"]))
        seasons.setdefault(s["key"], s)
    return sorted(seasons.values(), key=lambda s: s["start"], reverse=True)


def _player_key(row) -> str:
    """Group account entries by e-mail (stable across nickname changes),
    guests by name, legacy rows by name."""
    if row.get("is_guest"):
        return "g:" + row["nickname"].lower()
    if row.get("user_email"):
        return "a:" + row["user_email"].lower()
    return "n:" + row["nickname"].lower()


def season_stats(db: SupabaseDB, start, end):
    """Overview totals and the attendance ranking for games already played
    within [start, end). Returns (overview, ranking) where ranking is a list of
    {name, count, is_guest} sorted by attendance desc."""
    try:
        rows = db.execute_query(
            "SELECT s.nickname, s.user_email, s.is_guest, s.game_id, g.start_time "
            "FROM signups s JOIN games g ON g.id = s.game_id "
            "WHERE g.start_time >= %s AND g.start_time < %s AND g.start_time < %s",
            (start, end, datetime.now(TIMEZONE))
        ) or []
    except Exception as e:
        st.error(f"Błąd podczas liczenia statystyk: {e}")
        return {"games": 0, "players": 0, "signups": 0}, []

    players, games = {}, set()
    for row in rows:
        games.add(row["game_id"])
        key = _player_key(row)
        played_at = parse_game_time(row["start_time"])
        player = players.get(key)
        if not player:
            player = players[key] = {
                "name": row["nickname"], "last": played_at,
                "is_guest": bool(row["is_guest"]), "games": set(),
            }
        player["games"].add(row["game_id"])
        # Display the most recent nickname this player used.
        if played_at >= player["last"]:
            player["last"], player["name"] = played_at, row["nickname"]

    ranking = sorted(
        (
            {"name": p["name"], "count": len(p["games"]), "is_guest": p["is_guest"]}
            for p in players.values()
        ),
        key=lambda r: (-r["count"], r["name"].lower()),
    )
    overview = {"games": len(games), "players": len(players), "signups": len(rows)}
    return overview, ranking
