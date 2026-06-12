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


def account_display_name(db: SupabaseDB, game_id: str, email: str, account_name: str) -> str:
    """The name this account uses on the game's list: its signup nickname when
    signed up, otherwise the name it WOULD get (dedup-aware preview), so the
    guests panel and the list stay consistent even before/after signing up."""
    entry = get_account_signup(db, game_id, email)
    if entry:
        return entry["nickname"]
    return _unique_nickname(db, game_id, _base_nickname(account_name, email))


def resolve_adder_names(db: SupabaseDB, signups: list) -> dict:
    """Map added_by_email (lowercased) -> display label for every guest's adder,
    so the list can always show who added a guest - even when that account is
    not itself on this game's list. Falls back across games, then to the e-mail
    local part."""
    guest_emails = {
        s["added_by_email"].lower()
        for s in signups
        if s.get("is_guest") and s.get("added_by_email")
    }
    if not guest_emails:
        return {}

    names = {}
    # 1) adder is signed up in THIS game -> their current nickname
    for s in signups:
        if not s.get("is_guest") and s.get("user_email"):
            email = s["user_email"].lower()
            if email in guest_emails:
                names[email] = s["nickname"]

    # 2) otherwise -> most recent nickname the adder used in any game
    missing = [e for e in guest_emails if e not in names]
    if missing:
        try:
            rows = db.execute_query(
                "SELECT DISTINCT ON (LOWER(user_email)) LOWER(user_email) AS email, nickname "
                "FROM signups WHERE is_guest = FALSE AND user_email IS NOT NULL "
                "AND LOWER(user_email) = ANY(%s) "
                "ORDER BY LOWER(user_email), timestamp DESC",
                (missing,)
            ) or []
            for row in rows:
                names[row["email"]] = row["nickname"]
        except Exception:
            pass

    # 3) still unknown -> e-mail local part
    for email in guest_emails:
        names.setdefault(email, email.split("@")[0])

    return names


def _nickname_taken(db: SupabaseDB, game_id: str, nickname: str) -> bool:
    rows = db.execute_query(
        "SELECT 1 FROM signups WHERE game_id = %s AND nickname = %s",
        (game_id, nickname)
    )
    return bool(rows)


def _base_nickname(name: str, email: str) -> str:
    """Display name derived from the account: full name, e-mail local part
    as fallback, 'Gracz' as the last resort."""
    base = sanitize_input(name or "")[:20].strip()
    if validate_player_name(base)[0]:
        return base
    local = (email or "").split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ")
    base = sanitize_input(local)[:20].strip()
    if validate_player_name(base)[0]:
        return base
    return "Gracz"


def _unique_nickname(db: SupabaseDB, game_id: str, base: str) -> str:
    """Appends ' 2', ' 3', ... when the name is already on the list."""
    candidate, n = base, 2
    while _nickname_taken(db, game_id, candidate):
        suffix = f" {n}"
        candidate = base[:20 - len(suffix)].rstrip() + suffix
        n += 1
    return candidate


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


def add_account_signup(db: SupabaseDB, game_id: str, email: str, name: str):
    """Signs up the logged-in user under their account name (deduplicated
    with a numeric suffix when two players share the name)."""
    try:
        if get_account_signup(db, game_id, email):
            return False, f"Jesteś już zapisany na tę gierkę (konto: {email})"

        nickname = _unique_nickname(db, game_id, _base_nickname(name, email))
        _insert_signup(db, game_id, nickname, user_email=email)
        return True, f"Jesteś na liście jako {nickname}!"
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
            return False, f"Możesz dodać maksymalnie {MAX_GUESTS_PER_USER} gości"
        if _nickname_taken(db, game_id, guest_name):
            return False, "Gracz o tym imieniu/nicku już jest na liście"

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
            return False, "Nie znaleziono zapisu"
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
            return False, "Możesz wypisać tylko siebie i swoich gości"

        db.execute_query("DELETE FROM signups WHERE id = %s", (signup_id,))
        return True, f"Wypisano: {entry['nickname']}"
    except Exception as e:
        return False, f"Błąd podczas wypisywania: {str(e)[:120]}"
