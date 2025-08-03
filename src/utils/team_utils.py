"""
Functions for drawing team lineups
"""

import random
from src.game_config import TEAM_CONFIGS, ALLOWED_PLAYER_COUNTS


def draw_teams(players: list, num_players: int):
    """Draws team lineups based on configuration"""
    if num_players not in ALLOWED_PLAYER_COUNTS:
        return None
    
    config = TEAM_CONFIGS[num_players]
    random.shuffle(players)
    
    teams = {}
    start_idx = 0
    
    for i, color in enumerate(config["colors"]):
        players_count = config["players_per_team"][i]
        end_idx = start_idx + players_count
        teams[color] = players[start_idx:end_idx]
        start_idx = end_idx
    
    return teams


def is_valid_player_count(num_players: int) -> bool:
    """Checks if the number of players allows for automatic drawing"""
    return num_players in ALLOWED_PLAYER_COUNTS


def get_team_info(num_players: int) -> dict:
    """Returns team configuration information for given number of players"""
    if num_players in TEAM_CONFIGS:
        return TEAM_CONFIGS[num_players]
    return None
