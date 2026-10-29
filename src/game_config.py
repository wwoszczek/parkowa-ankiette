"""
Application time configuration - loaded from YAML file
"""

import yaml
from datetime import date
from pathlib import Path

# Path to configuration file
CONFIG_FILE = Path(__file__).parent.parent / "game_consts.yaml"

def load_config():
    """Loads configuration from YAML file"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise Exception(f"Failed to load configuration from {CONFIG_FILE}: {e}")

# Load configuration
_config = load_config()

# ===== GAME SCHEDULE =====
GAME_DAY = _config['game']['day']
GAME_START_HOUR = _config['game']['hour']
GAME_START_MINUTE = _config['game']['minute']
# [(from_date, hour, minute)] sorted by date; YAML parses ISO dates to date objects
GAME_TIME_CHANGES = sorted(
    (date.fromisoformat(str(change['from'])), change['hour'], change['minute'])
    for change in _config['game'].get('time_changes') or []
)

# ===== SIGNUP OPENING =====
SIGNUP_OPEN_DAY = _config['signup']['day']
SIGNUP_OPEN_HOUR = _config['signup']['hour']
SIGNUP_OPEN_MINUTE = _config['signup']['minute']

# ===== GUESTS =====
MAX_GUESTS_PER_USER = int(_config.get('guests', {}).get('max_per_user', 2))

# ===== TEAM LINEUPS =====
TEAM_CONFIGS = {}
for players_count, config in _config['teams'].items():
    TEAM_CONFIGS[int(players_count)] = {
        "teams": config['count'],
        "colors": config['colors'],
        "players_per_team": config['players_per_team']
    }

# ===== PLAYER CARDS =====
_cards = {
    "since": None, "bronze_share": 0.35, "silver_share": 0.35, "silver_games": 3, "gold_games": 8, "legend": 90,
    "legend_streak": 4, "in_form_streak": 3, "in_form_chance": 0.75, "in_form_max": 3,
    "toty_size": 3,
    **(_config.get('cards') or {}),
}
CARDS_SINCE = date.fromisoformat(str(_cards["since"])) if _cards["since"] else None
CARD_THRESHOLDS = {k: v for k, v in _cards.items() if k != "since"}

# Day names: nominative ("środa") and accusative ("w środę")
DAY_NAMES = _config['day_names']
DAY_NAMES_ACCUSATIVE = _config.get('day_names_accusative', DAY_NAMES)

SIGNUP_OPENING_MESSAGE = (
    f"Nowa gierka otworzy się w {DAY_NAMES_ACCUSATIVE[SIGNUP_OPEN_DAY]} "
    f"o {SIGNUP_OPEN_HOUR:02d}:{SIGNUP_OPEN_MINUTE:02d}"
)
