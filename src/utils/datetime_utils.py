"""
Helper functions for date and time handling
"""

from datetime import datetime, timedelta
from src.constants import TIMEZONE
from src.game_config import (
    GAME_DAY, GAME_START_HOUR, GAME_START_MINUTE,
    SIGNUP_OPEN_DAY, SIGNUP_OPEN_HOUR, SIGNUP_OPEN_MINUTE,
    DRAW_ALLOWED_DAY, DRAW_ALLOWED_HOUR, DRAW_ALLOWED_MINUTE,
    DAY_NAMES,
)


def get_next_game_time():
    """Gets the date of the next game"""
    now = datetime.now(TIMEZONE)
    days_ahead = GAME_DAY - now.weekday()

    # If today is game day but after start time, take next week
    if days_ahead < 0 or (days_ahead == 0 and (now.hour > GAME_START_HOUR or
                                               (now.hour == GAME_START_HOUR and now.minute >= GAME_START_MINUTE))):
        days_ahead += 7

    next_game = now + timedelta(days=days_ahead)
    return next_game.replace(hour=GAME_START_HOUR, minute=GAME_START_MINUTE, second=0, microsecond=0)


def parse_game_time(start_time):
    """Safely parse game start_time from database, handling both string and datetime objects"""
    if isinstance(start_time, str):
        return datetime.fromisoformat(start_time.replace('Z', '+00:00')).astimezone(TIMEZONE)
    else:
        # start_time is already a datetime object
        return start_time.astimezone(TIMEZONE)


def parse_timestamp(timestamp):
    """Safely parse timestamp from database, handling both string and datetime objects"""
    if isinstance(timestamp, str):
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone(TIMEZONE)
    else:
        # timestamp is already a datetime object
        return timestamp.astimezone(TIMEZONE)


def get_last_signup_opening():
    """Gets the date of the last signup opening"""
    now = datetime.now(TIMEZONE)
    days_back = now.weekday() - SIGNUP_OPEN_DAY

    # If today is opening day but before the hour, take previous week
    if days_back < 0:
        days_back += 7
    elif days_back == 0 and now.hour < SIGNUP_OPEN_HOUR:
        days_back = 7

    last_opening = now - timedelta(days=days_back)
    return last_opening.replace(hour=SIGNUP_OPEN_HOUR, minute=SIGNUP_OPEN_MINUTE, second=0, microsecond=0)


def is_draw_time_allowed():
    """Checks if lineup draw time is allowed"""
    now = datetime.now(TIMEZONE)
    is_correct_day = now.weekday() == DRAW_ALLOWED_DAY
    is_correct_time = now.hour >= DRAW_ALLOWED_HOUR or (
        now.hour == DRAW_ALLOWED_HOUR and now.minute >= DRAW_ALLOWED_MINUTE
    )
    return is_correct_day and is_correct_time


def format_game_date(dt, with_time=True):
    """Formats a game date as 'Środa, 17.06.2026 · 18:30'"""
    day_name = DAY_NAMES[dt.weekday()].capitalize()
    base = f"{day_name}, {dt.strftime('%d.%m.%Y')}"
    return f"{base} · {dt.strftime('%H:%M')}" if with_time else base


def relative_day_label(dt):
    """Returns 'dzisiaj' / 'jutro' / 'za N dni' relative to now"""
    days = (dt.date() - datetime.now(TIMEZONE).date()).days
    if days <= 0:
        return "dzisiaj"
    if days == 1:
        return "jutro"
    return f"za {days} dni"


# Meteorological seasons: wiosna (Mar-May), lato (Jun-Aug),
# jesień (Sep-Nov), zima (Dec-Feb).
_SEASON_BY_MONTH = {
    3: ("wiosna", 3), 4: ("wiosna", 3), 5: ("wiosna", 3),
    6: ("lato", 6), 7: ("lato", 6), 8: ("lato", 6),
    9: ("jesień", 9), 10: ("jesień", 9), 11: ("jesień", 9),
    12: ("zima", 12), 1: ("zima", 12), 2: ("zima", 12),
}


def season_bounds(dt):
    """The meteorological season containing dt, as a dict with key, name,
    label and the [start, end) bounds (timezone-aware)."""
    name, start_month = _SEASON_BY_MONTH[dt.month]
    # Winter starts in December, so Jan/Feb belong to the previous year's winter.
    start_year = dt.year - 1 if start_month == 12 and dt.month in (1, 2) else dt.year

    start = TIMEZONE.localize(datetime(start_year, start_month, 1))
    end_month, end_year = start_month + 3, start_year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    end = TIMEZONE.localize(datetime(end_year, end_month, 1))

    if name == "zima":
        label = f"Zima {start_year}/{str(start_year + 1)[2:]}"
    else:
        label = f"{name.capitalize()} {start_year}"

    return {"key": f"{start_year}-{start_month:02d}", "name": name,
            "label": label, "start": start, "end": end}
