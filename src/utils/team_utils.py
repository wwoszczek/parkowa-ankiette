"""
Funkcje do losowania składów drużyn
"""

import random
from src.game_config import TEAM_CONFIGS, ALLOWED_PLAYER_COUNTS


def draw_teams(players: list, num_players: int):
    """Losuje składy drużyn na podstawie konfiguracji"""
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
    """Sprawdza czy liczba graczy pozwala na automatyczne losowanie"""
    return num_players in ALLOWED_PLAYER_COUNTS


def get_team_info(num_players: int) -> dict:
    """Zwraca informacje o konfiguracji drużyn dla danej liczby graczy"""
    if num_players in TEAM_CONFIGS:
        return TEAM_CONFIGS[num_players]
    return None
