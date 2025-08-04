"""
Application time configuration - loaded from YAML file
"""

import yaml
import os
from pathlib import Path

# Path to configuration file
CONFIG_FILE = Path(__file__).parent.parent / "game_consts.yaml"

def load_config():
    """Loads configuration from YAML file"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise Exception(f"Błąd wczytywania konfiguracji z {CONFIG_FILE}: {e}")

# Load configuration
_config = load_config()

# ===== GAME SCHEDULE =====
GAME_DAY = _config['game']['day']
GAME_START_HOUR = _config['game']['hour']
GAME_START_MINUTE = _config['game']['minute']

# ===== SIGNUP OPENING =====
SIGNUP_OPEN_DAY = _config['signup']['day']
SIGNUP_OPEN_HOUR = _config['signup']['hour']
SIGNUP_OPEN_MINUTE = _config['signup']['minute']

# ===== LINEUP DRAWING =====
DRAW_ALLOWED_DAY = _config['draw']['day']
DRAW_ALLOWED_HOUR = _config['draw']['hour']
DRAW_ALLOWED_MINUTE = _config['draw']['minute']

# ===== TEAM LINEUPS =====
TEAM_CONFIGS = {}
for players_count, config in _config['teams'].items():
    TEAM_CONFIGS[int(players_count)] = {
        "teams": config['count'],
        "colors": config['colors'],
        "players_per_team": config['players_per_team']
    }

ALLOWED_PLAYER_COUNTS = list(TEAM_CONFIGS.keys())

# ===== MESSAGES =====
MANUAL_DRAW_MESSAGE = _config['messages']['manual_draw']

# ===== PAYMENTS =====
# Treasurer password loaded from Streamlit secrets for security
import streamlit as st
try:
    TREASURER_PASSWORD = st.secrets["treasurer_password"]
except KeyError:
    TREASURER_PASSWORD = "default_password"  # Fallback for development
    
BLIK_NUMBER = _config['payments']['blik_number']

# Generating messages based on configuration
_day_names = _config['day_names']

DRAW_NOT_AVAILABLE_MESSAGE = (
    f"Losowanie składów jest dostępne tylko w {_day_names[DRAW_ALLOWED_DAY]} "
    f"od {DRAW_ALLOWED_HOUR:02d}:{DRAW_ALLOWED_MINUTE:02d}!"
)

SIGNUP_OPENING_MESSAGE = (
    f"Nowa gierka otworzy się w {_day_names[SIGNUP_OPEN_DAY]} "
    f"o {SIGNUP_OPEN_HOUR:02d}:{SIGNUP_OPEN_MINUTE:02d}."
)
