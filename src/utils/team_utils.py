"""
Functions for drawing team lineups
"""

import random
from src.game_config import TEAM_CONFIGS, ALLOWED_PLAYER_COUNTS


def draw_teams(players: list, num_players: int, pins: dict | None = None):
    """Draws team lineups based on configuration.

    `pins` optionally fixes players to a shirt colour (for people who only have
    one colour available): {color: [players]}. Pinned players are placed in
    their colour first, the rest are shuffled into the remaining slots.
    Returns None if the count is invalid or the pins don't fit.
    """
    if num_players not in ALLOWED_PLAYER_COUNTS:
        return None

    config = TEAM_CONFIGS[num_players]
    colors = config["colors"]
    caps = config["players_per_team"]
    pins = pins or {}

    # Validate pins: known colours, within capacity, each player once, on the list.
    pinned = []
    for i, color in enumerate(colors):
        chosen = pins.get(color, [])
        if len(chosen) > caps[i]:
            return None
        pinned.extend(chosen)
    if len(pinned) != len(set(pinned)):
        return None
    if not set(pinned).issubset(set(players)):
        return None

    teams = {color: list(pins.get(color, [])) for color in colors}
    rest = [p for p in players if p not in set(pinned)]
    random.shuffle(rest)

    for i, color in enumerate(colors):
        need = caps[i] - len(teams[color])
        teams[color].extend(rest[:need])
        rest = rest[need:]

    return teams


def is_valid_player_count(num_players: int) -> bool:
    """Checks if the number of players allows for automatic drawing"""
    return num_players in ALLOWED_PLAYER_COUNTS


def get_team_info(num_players: int) -> dict:
    """Returns team configuration information for given number of players"""
    if num_players in TEAM_CONFIGS:
        return TEAM_CONFIGS[num_players]
    return None
