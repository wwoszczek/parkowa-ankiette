"""
What an account may set on its own card: a position and a photo. Stats and
rating are never editable - they come only from played games (utils.cards).

The position is decoration only: it is printed on the card and never moves
anyone in the squads or on the pitch. Photos are re-encoded server-side
(square crop, small WebP) so the stored image is a few KB whatever was
uploaded. Both live in `player_cards`; until that table exists the app runs
as before, with placeholders and no positions.
"""

import base64
import io
import logging
from datetime import datetime

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

from src.constants import TIMEZONE
from src.database import SupabaseDB

logger = logging.getLogger(__name__)

POSITIONS = {"BR": "Bramkarz", "OBR": "Obrońca", "POM": "Pomocnik", "NAP": "Napastnik"}
PHOTO_TYPES = ["jpg", "jpeg", "png", "webp"]
MAX_UPLOAD_MB = 5           # keep in sync with server.maxUploadSize in .streamlit/config.toml
_MAX_PIXELS = 40_000_000    # refuse huge images before decoding them
_PHOTO_PX = 256             # stored photos are square, this many pixels a side


def profiles_ready(db: SupabaseDB) -> bool:
    """player_cards exists (checked without raising, so a missing table never
    shows a database error on the page)."""
    try:
        rows = db.execute_query("SELECT to_regclass('player_cards') IS NOT NULL AS ready")
        return bool(rows and rows[0]["ready"])
    except Exception:
        return False


def _data_uri(photo) -> str | None:
    if not photo:
        return None
    data = bytes(photo)
    mime = (
        "image/webp" if data[8:12] == b"WEBP"
        else "image/png" if data.startswith(b"\x89PNG")
        else "image/jpeg"
    )
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


@st.cache_data(ttl=600, show_spinner=False)
def load_profiles(_db: SupabaseDB) -> dict:
    """{email: {"position", "photo": data URI or None}} for every account
    that set either."""
    if not profiles_ready(_db):
        return {}
    rows = _db.execute_query("SELECT user_email, position, photo FROM player_cards") or []
    return {
        row["user_email"].lower(): {"position": row["position"], "photo": _data_uri(row["photo"])}
        for row in rows
    }


def process_photo(data: bytes):
    """Uploaded bytes -> (small square WebP, None) or (None, error message).
    Transparency is kept, so a cut-out photo sits on the card like in FUT."""
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        return None, f"Zdjęcie jest za duże — limit to {MAX_UPLOAD_MB} MB"
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > _MAX_PIXELS:
                return None, "Zdjęcie ma za dużą rozdzielczość"
            image = ImageOps.exif_transpose(image)
            alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
            image = image.convert("RGBA" if alpha else "RGB")
            # Faces sit in the upper part of most photos
            image = ImageOps.fit(image, (_PHOTO_PX, _PHOTO_PX), Image.Resampling.LANCZOS, centering=(0.5, 0.35))
            out = io.BytesIO()
            image.save(out, "WEBP", quality=82, method=6)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        return None, "Nie udało się odczytać zdjęcia — wgraj plik JPG, PNG albo WebP"
    return out.getvalue(), None


def _allowed(email: str, actor: str, admin: bool) -> bool:
    return admin or (actor or "").lower() == (email or "").lower()


def _upsert(db: SupabaseDB, email: str, column_values: dict):
    columns = ", ".join(column_values)
    placeholders = ", ".join(["%s"] * len(column_values))
    updates = ", ".join(f"{column} = EXCLUDED.{column}" for column in column_values)
    db.execute_query(
        f"INSERT INTO player_cards (user_email, {columns}) VALUES (LOWER(%s), {placeholders}) "
        f"ON CONFLICT (user_email) DO UPDATE SET {updates}",
        (email, *column_values.values())
    )


def set_position(db: SupabaseDB, email: str, position: str | None, actor: str, admin: bool = False):
    """Position on the card (None clears it). Decoration only."""
    if not _allowed(email, actor, admin):
        return False, "Możesz zmieniać tylko swoją kartę"
    if position is not None and position not in POSITIONS:
        return False, "Nieznana pozycja"
    if not profiles_ready(db):
        return False, "Karty nie są jeszcze skonfigurowane w bazie (tabela player_cards)"
    try:
        _upsert(db, email, {"position": position, "updated_at": datetime.now(TIMEZONE)})
        load_profiles.clear()
        if position is None:
            return True, "Usunięto pozycję z karty"
        return True, f"Pozycja na karcie: {POSITIONS[position].lower()}"
    except Exception:
        logger.exception("Saving card position failed")
        return False, "Błąd podczas zapisywania pozycji"


def set_photo(db: SupabaseDB, email: str, data: bytes, actor: str, admin: bool = False):
    """Store a photo for the account's card (re-encoded, see process_photo)."""
    if not _allowed(email, actor, admin):
        return False, "Możesz zmieniać tylko swoją kartę"
    if not profiles_ready(db):
        return False, "Karty nie są jeszcze skonfigurowane w bazie (tabela player_cards)"
    photo, error = process_photo(data)
    if error:
        return False, error
    try:
        now = datetime.now(TIMEZONE)
        _upsert(db, email, {
            "photo": photo, "photo_updated_at": now,
            "photo_uploaded_by": (actor or "").lower(), "updated_at": now,
        })
        load_profiles.clear()
        return True, "Zdjęcie jest już na karcie"
    except Exception:
        logger.exception("Saving card photo failed")
        return False, "Błąd podczas zapisywania zdjęcia"


def remove_photo(db: SupabaseDB, email: str, actor: str, admin: bool = False):
    if not _allowed(email, actor, admin):
        return False, "Możesz zmieniać tylko swoją kartę"
    try:
        db.execute_query(
            "UPDATE player_cards SET photo = NULL, photo_updated_at = %s, photo_uploaded_by = LOWER(%s), "
            "updated_at = %s WHERE user_email = LOWER(%s)",
            (datetime.now(TIMEZONE), actor or "", datetime.now(TIMEZONE), email)
        )
        load_profiles.clear()
        return True, "Usunięto zdjęcie — na karcie jest znowu sylwetka"
    except Exception:
        logger.exception("Removing card photo failed")
        return False, "Błąd podczas usuwania zdjęcia"
