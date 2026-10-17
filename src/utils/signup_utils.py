"""
Player signups: account-based entries and guests added by signed-in users.
"""

import logging
import uuid
from datetime import datetime

import streamlit as st

from src.constants import TIMEZONE
from src.database import SupabaseDB
from src.game_config import MAX_GUESTS_PER_USER
from src.utils.profile import get_display_name
from src.utils.validation import sanitize_input, validate_player_name

logger = logging.getLogger(__name__)


def get_signups_for_game(db: SupabaseDB, game_id: str):
    """Gets signups for a given game (oldest first)"""
    try:
        return db.execute_query(
            "SELECT * FROM signups WHERE game_id = %s ORDER BY timestamp",
            (game_id,)
        )
    except Exception:
        st.error("Błąd podczas pobierania zapisów")
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
    return _unique_nickname(db, game_id, account_base_nickname(db, email, account_name))


def resolve_adder_names(db: SupabaseDB, signups: list) -> dict:
    """Map added_by_email (lowercased) -> display label for every guest's adder,
    so the list can always show who added a guest - even when that account is
    not itself on this game's list."""
    return resolve_account_names(db, signups, [
        s["added_by_email"] for s in signups if s.get("is_guest") and s.get("added_by_email")
    ])


def resolve_account_names(db: SupabaseDB, signups: list, emails) -> dict:
    """Map e-mails (lowercased) -> display label: the account's nickname on this
    game's list, else the latest one it used in any game, else the e-mail local
    part."""
    wanted = {e.lower() for e in emails if e}
    if not wanted:
        return {}

    names = {}
    # 1) account is signed up in THIS game -> its current nickname
    for s in signups:
        if not s.get("is_guest") and s.get("user_email"):
            email = s["user_email"].lower()
            if email in wanted:
                names[email] = s["nickname"]

    # 2) otherwise -> most recent nickname the account used in any game
    missing = [e for e in wanted if e not in names]
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
    for email in wanted:
        names.setdefault(email, email.split("@")[0])

    return names


def _nickname_taken(db: SupabaseDB, game_id: str, nickname: str, exclude_id=None) -> bool:
    """True when another signup in this game already uses the name. `exclude_id`
    skips one row, so a player renaming their own entry does not clash with it."""
    if exclude_id:
        rows = db.execute_query(
            "SELECT 1 FROM signups WHERE game_id = %s AND nickname = %s AND id <> %s",
            (game_id, nickname, exclude_id)
        )
    else:
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


def _unique_nickname(db: SupabaseDB, game_id: str, base: str, exclude_id=None) -> str:
    """Appends ' 2', ' 3', ... when the name is already on the list. `exclude_id`
    skips one row, so renaming a player's own entry never collides with itself."""
    candidate, n = base, 2
    while _nickname_taken(db, game_id, candidate, exclude_id):
        suffix = f" {n}"
        candidate = base[:20 - len(suffix)].rstrip() + suffix
        n += 1
    return candidate


def account_base_nickname(db: SupabaseDB, email: str, account_name: str) -> str:
    """The base name for an account before per-game dedup: the player's own
    chosen display name when set, otherwise derived from the Google account."""
    custom = get_display_name(db, email)
    if custom:
        return custom
    return _base_nickname(account_name, email)


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

        nickname = _unique_nickname(db, game_id, account_base_nickname(db, email, name))
        _insert_signup(db, game_id, nickname, user_email=email)
        return True, f"Jesteś na liście jako {nickname}!"
    except Exception:
        logger.exception("Account signup failed")
        return False, "Błąd podczas zapisu"


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
    except Exception:
        logger.exception("Guest signup failed")
        return False, "Błąd podczas dodawania gościa"


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
    except Exception:
        logger.exception("Signup removal failed")
        return False, "Błąd podczas wypisywania"
