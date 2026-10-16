"""
Per-account display name preferences.

A player's name on the lists defaults to their Google account name, but they can
set their own persistent display name (stored in `user_profiles`, keyed by
e-mail). The chosen name applies to every future signup and is propagated to
their entries in currently-active games so the change shows immediately.
"""

import logging
from datetime import datetime

from src.constants import TIMEZONE
from src.database import SupabaseDB
from src.utils.teams_db import rename_in_squads
from src.utils.validation import sanitize_input, validate_player_name

logger = logging.getLogger(__name__)


def get_display_name(db: SupabaseDB, email: str):
    """The account's chosen display name, or None when it never set one."""
    if not email:
        return None
    try:
        rows = db.execute_query(
            "SELECT display_name FROM user_profiles WHERE LOWER(user_email) = LOWER(%s)",
            (email,)
        )
        return rows[0]["display_name"] if rows else None
    except Exception:
        logger.exception("Reading display name failed")
        return None


def _propagate(db: SupabaseDB, email: str, base: str):
    """Rewrite the account's nickname (deduped per game) in every active game it
    is signed up for - and in that game's saved squads - so a rename is visible
    on the current list right away."""
    from src.utils.signup_utils import _unique_nickname  # avoid import cycle

    rows = db.execute_query(
        "SELECT s.id, s.game_id, s.nickname FROM signups s "
        "JOIN games g ON g.id = s.game_id "
        "WHERE s.is_guest = FALSE AND LOWER(s.user_email) = LOWER(%s) AND g.active = TRUE",
        (email,)
    ) or []
    for row in rows:
        nickname = _unique_nickname(db, row["game_id"], base, exclude_id=row["id"])
        db.execute_query(
            "UPDATE signups SET nickname = %s WHERE id = %s",
            (nickname, row["id"])
        )
        if nickname != row["nickname"]:
            rename_in_squads(db, row["game_id"], row["nickname"], nickname)


def set_display_name(db: SupabaseDB, email: str, name: str):
    """Save the account's chosen display name and apply it to active signups."""
    try:
        name = sanitize_input(name)
        valid, error = validate_player_name(name)
        if not valid:
            return False, error

        db.execute_query(
            "INSERT INTO user_profiles (user_email, display_name, updated_at) "
            "VALUES (LOWER(%s), %s, %s) "
            "ON CONFLICT (user_email) DO UPDATE "
            "SET display_name = EXCLUDED.display_name, updated_at = EXCLUDED.updated_at",
            (email, name, datetime.now(TIMEZONE).isoformat())
        )
        _propagate(db, email, name)
        return True, f"Twoja nazwa to teraz {name}"
    except Exception:
        logger.exception("Saving display name failed")
        return False, "Błąd podczas zapisywania nazwy"


def clear_display_name(db: SupabaseDB, email: str, account_name: str):
    """Drop the chosen name, reverting active signups to the Google account name."""
    from src.utils.signup_utils import _base_nickname  # avoid import cycle
    try:
        db.execute_query(
            "DELETE FROM user_profiles WHERE LOWER(user_email) = LOWER(%s)",
            (email,)
        )
        _propagate(db, email, _base_nickname(account_name, email))
        return True, "Przywrócono nazwę z konta Google"
    except Exception:
        logger.exception("Clearing display name failed")
        return False, "Błąd podczas przywracania nazwy"
