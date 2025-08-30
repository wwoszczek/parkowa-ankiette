"""
Functions for handling games in the database
"""

import streamlit as st
import uuid
from datetime import datetime
from src.database import SupabaseDB
from src.constants import TIMEZONE
from src.utils.datetime_utils import get_next_game_time, parse_game_time


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_active_games(_db: SupabaseDB):
    """Get active games with caching"""
    try:
        return _db.execute_query("SELECT * FROM games WHERE active = TRUE ORDER BY start_time")
    except Exception as e:
        st.error(f"Błąd podczas pobierania aktywnych gierek: {e}")
        return []


def create_new_game_if_needed(db: SupabaseDB):
    """Creates new game if needed"""
    try:
        next_game = get_next_game_time()
        
        # Check if active game already exists for this day
        active_games = db.execute_query("SELECT * FROM games WHERE active = TRUE")
        
        active_games_today = [game for game in active_games 
                             if parse_game_time(game['start_time']).date() == next_game.date()]
        
        if not active_games_today:
            # Create new game
            new_game_id = str(uuid.uuid4())
            db.execute_query(
                "INSERT INTO games (id, start_time, active) VALUES (%s, %s, %s)",
                (new_game_id, next_game.isoformat(), True)
            )
            return {
                'id': new_game_id,
                'start_time': next_game.isoformat(),
                'active': True
            }
        
        return active_games_today[0]
    except Exception as e:
        st.error(f"Błąd podczas tworzenia nowej gierki: {e}")
        return None


def deactivate_past_games(db: SupabaseDB):
    """Deactivates games that have already taken place"""
    try:
        now = datetime.now(TIMEZONE)
        active_games = get_active_games(db)  # Use cached version
        
        for game in active_games:
            game_time = parse_game_time(game['start_time'])
            if game_time <= now:
                db.execute_query(
                    "UPDATE games SET active = FALSE WHERE id = %s",
                    (game['id'],)
                )
                # Clear cache after modification
                get_active_games.clear()
    except Exception as e:
        st.error(f"Błąd podczas dezaktywacji gierek: {e}")


def get_past_games(db: SupabaseDB):
    """Gets inactive games (history)"""
    try:
        return db.execute_query("SELECT * FROM games WHERE active = FALSE ORDER BY start_time DESC")
    except Exception as e:
        st.error(f"Błąd podczas pobierania historii gierek: {e}")
        return []
