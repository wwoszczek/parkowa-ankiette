"""
Funkcje pomocnicze do obsługi dat i czasu
"""

from datetime import datetime, timedelta
from src.config import TIMEZONE
from src.game_config import (
    GAME_DAY, GAME_START_HOUR, GAME_START_MINUTE,
    SIGNUP_OPEN_DAY, SIGNUP_OPEN_HOUR, SIGNUP_OPEN_MINUTE,
    DRAW_ALLOWED_DAY, DRAW_ALLOWED_HOUR, DRAW_ALLOWED_MINUTE
)


def get_next_game_time():
    """Pobiera datę najbliższej gierki"""
    now = datetime.now(TIMEZONE)
    days_ahead = GAME_DAY - now.weekday()
    
    # Jeśli dziś jest dzień gierki ale już po godzinie rozpoczęcia, weź następny tydzień
    if days_ahead <= 0 or (days_ahead == 0 and now.hour >= GAME_START_HOUR):
        days_ahead += 7
    
    next_game = now + timedelta(days=days_ahead)
    return next_game.replace(hour=GAME_START_HOUR, minute=GAME_START_MINUTE, second=0, microsecond=0)


def get_last_signup_opening():
    """Pobiera datę ostatniego otwarcia zapisów"""
    now = datetime.now(TIMEZONE)
    days_back = now.weekday() - SIGNUP_OPEN_DAY
    
    # Jeśli dziś jest dzień otwarcia ale jeszcze przed godziną, weź poprzedni tydzień
    if days_back < 0:
        days_back += 7
    elif days_back == 0 and now.hour < SIGNUP_OPEN_HOUR:
        days_back = 7
    
    last_opening = now - timedelta(days=days_back)
    return last_opening.replace(hour=SIGNUP_OPEN_HOUR, minute=SIGNUP_OPEN_MINUTE, second=0, microsecond=0)


def is_draw_time_allowed():
    """Sprawdza czy jest dozwolony czas na losowanie składów"""
    now = datetime.now(TIMEZONE)
    is_correct_day = now.weekday() == DRAW_ALLOWED_DAY
    is_correct_time = now.hour >= DRAW_ALLOWED_HOUR or (
        now.hour == DRAW_ALLOWED_HOUR and now.minute >= DRAW_ALLOWED_MINUTE
    )
    return is_correct_day and is_correct_time


# Zachowaj stare nazwy funkcji dla kompatybilności wstecznej
def get_next_wednesday_1830():
    """Deprecated: użyj get_next_game_time()"""
    return get_next_game_time()


def get_last_monday_1000():
    """Deprecated: użyj get_last_signup_opening()"""
    return get_last_signup_opening()


def is_wednesday_after_1500():
    """Deprecated: użyj is_draw_time_allowed()"""
    return is_draw_time_allowed()
