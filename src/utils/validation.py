"""
Input validation and sanitization for player names.
"""

_ALLOWED_CHARS = set(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_'
    'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'
)
_FORBIDDEN_NAMES = {'admin', 'test', 'null', 'undefined', 'system'}


def sanitize_input(text: str) -> str:
    """Trims and collapses whitespace."""
    if not text:
        return ""
    return ' '.join(text.split())


def validate_player_name(name: str) -> tuple[bool, str]:
    """
    Validate a player/guest display name.

    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Imię/nick nie może być puste"

    if len(name) < 2:
        return False, "Imię/nick musi mieć co najmniej 2 znaki"

    if len(name) > 20:
        return False, "Imię/nick nie może być dłuższy niż 20 znaków"

    if not all(char in _ALLOWED_CHARS for char in name):
        return False, "Imię/nick zawiera niedozwolone znaki"

    if name.lower() in _FORBIDDEN_NAMES:
        return False, "Ta nazwa jest zarezerwowana"

    return True, ""
