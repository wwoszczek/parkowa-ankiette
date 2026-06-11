"""
Player signups: account-based entries and guests added by signed-in users.
"""

import uuid
from datetime import datetime

import streamlit as st

from src.constants import TIMEZONE
from src.database import SupabaseDB
from src.game_config import MAX_GUESTS_PER_USER
from src.utils.validation import sanitize_input, validate_player_name


def get_signups_for_game(db: SupabaseDB, game_id: str):
    """Gets signups for a given game (oldest first)"""
    try:
        return db.execute_query(
            "SELECT * FROM signups WHERE game_id = %s ORDER BY timestamp",
            (game_id,)
        )
    except Exception as e:
        st.error(f"Błąd podczas pobierania zapisów: {e}")
        return []


def get_account_signup(db: SupabaseDB, game_id: str, email: str):
    """The signed-in user's own (non-guest) entry, or None."""
    rows = db.execute_query(
        "SELECT * FROM signups WHERE game_id = %s AND is_guest = FALSE AND LOWER(user_email) = LOWER(%s)",
        (game_id, email)
    )
    return rows[0] if rows else None


def get_guests_added_by(db: SupabaseDB, game_id: str, email: str):
    """Guest entries added by the given account for a game."""
    return db.execute_query(
        "SELECT * FROM signups WHERE game_id = %s AND is_guest = TRUE AND LOWER(added_by_email) = LOWER(%s) "
        "ORDER BY timestamp",
        (game_id, email)
    ) or []


def _nickname_taken(db: SupabaseDB, game_id: str, nickname: str) -> bool:
    rows = db.execute_query(
        "SELECT 1 FROM signups WHERE game_id = %s AND nickname = %s",
        (game_id, nickname)
    )
    return bool(rows)


def _insert_signup(db: SupabaseDB, game_id: str, nickname: str,
                   user_email=None, is_guest=False, added_by_email=None):
    db.execute_query(
        "INSERT INTO signups (id, game_id, nickname, user_email, is_guest, added_by_email, timestamp) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            str(uuid.uuid4()), game_id, nickname,
            user_email, is_guest, added_by_email,
            datetime.now(TIMEZONE).isoformat(),
        )
    )


def add_account_signup(db: SupabaseDB, game_id: str, nickname: str, email: str):
    """Signs up the logged-in user under the given display name."""
    try:
        nickname = sanitize_input(nickname)
        valid, error = validate_player_name(nickname)
        if not valid:
            return False, error

        if get_account_signup(db, game_id, email):
            return False, "Jesteś już na liście!"
        if _nickname_taken(db, game_id, nickname):
            return False, "Ten nick jest już zajęty w tej gierce — wybierz inny."

        _insert_signup(db, game_id, nickname, user_email=email)
        return True, "Jesteś na liście!"
    except Exception as e:
        return False, f"Błąd podczas zapisu: {str(e)[:120]}"


def add_guest_signup(db: SupabaseDB, game_id: str, guest_name: str, added_by_email: str):
    """Adds a guest (player without an account) on behalf of a logged-in user."""
    try:
        guest_name = sanitize_input(guest_name)
        valid, error = validate_player_name(guest_name)
        if not valid:
            return False, error

        if len(get_guests_added_by(db, game_id, added_by_email)) >= MAX_GUESTS_PER_USER:
            return False, f"Możesz dodać maksymalnie {MAX_GUESTS_PER_USER} gości."
        if _nickname_taken(db, game_id, guest_name):
            return False, "Gracz o tym imieniu/nicku już jest na liście."

        _insert_signup(db, game_id, guest_name, is_guest=True, added_by_email=added_by_email)
        return True, f"Dodano gościa: {guest_name}"
    except Exception as e:
        return False, f"Błąd podczas dodawania gościa: {str(e)[:120]}"


def remove_signup(db: SupabaseDB, signup_id: str, requester_email: str, admin: bool = False):
    """
    Removes an entry. Allowed for: the entry's owner (own signup),
    the user who added the guest, and admins.
    """
    try:
        rows = db.execute_query("SELECT * FROM signups WHERE id = %s", (signup_id,))
        if not rows:
            return False, "Nie znaleziono zapisu."
        entry = rows[0]

        requester = (requester_email or "").lower()
        owner = (entry.get("user_email") or "").lower()
        adder = (entry.get("added_by_email") or "").lower()
        allowed = admin or (
            requester and (
                (not entry.get("is_guest") and owner == requester)
                or (entry.get("is_guest") and adder == requester)
            )
        )
        if not allowed:
            return False, "Możesz wypisać tylko siebie i swoich gości."

        db.execute_query("DELETE FROM signups WHERE id = %s", (signup_id,))
        return True, f"Wypisano: {entry['nickname']}"
    except Exception as e:
        return False, f"Błąd podczas wypisywania: {str(e)[:120]}"
