"""
Functions for handling games in the database
"""

import streamlit as st
from datetime import datetime
from src.database import SupabaseDB
from src.constants import TIMEZONE


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_active_games(_db: SupabaseDB):
    """Get active games with caching"""
    try:
        return _db.execute_query("SELECT * FROM games WHERE active = TRUE ORDER BY start_time")
    except Exception as e:
        st.error(f"Błąd podczas pobierania aktywnych gierek: {e}")
        return []


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_past_games(_db: SupabaseDB):
    """Games that already took place (newest first). Excludes future inactive
    games pre-created by the scheduler before their signup window opens."""
    try:
        return _db.execute_query(
            "SELECT * FROM games WHERE active = FALSE AND start_time < %s ORDER BY start_time DESC",
            (datetime.now(TIMEZONE),)
        )
    except Exception as e:
        st.error(f"Błąd podczas pobierania historii gierek: {e}")
        return []
