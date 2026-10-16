#!/usr/bin/env python3
"""
GitHub Actions scheduler - independent from the Streamlit UI.
Runs on a fixed cron schedule via GitHub Actions (.github/workflows/scheduler.yml).
"""

import os
import sys
import logging
from datetime import date, datetime, timedelta
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import yaml
import pytz
from pathlib import Path

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/scheduler.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration - load from YAML file directly
def load_scheduler_config():
    """Load configuration from YAML file for scheduler"""
    config_file = Path(__file__).parent / "game_consts.yaml"
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return {
                'TIMEZONE': pytz.timezone('Europe/Warsaw'),
                'GAME_DAY': config['game']['day'],
                'GAME_START_HOUR': config['game']['hour'],
                'GAME_START_MINUTE': config['game']['minute'],
                'GAME_TIME_CHANGES': sorted(
                    (date.fromisoformat(str(change['from'])), change['hour'], change['minute'])
                    for change in config['game'].get('time_changes') or []
                ),
                'SIGNUP_OPEN_DAY': config['signup']['day'],
                'SIGNUP_OPEN_HOUR': config['signup']['hour'],
                'SIGNUP_OPEN_MINUTE': config['signup']['minute']
            }
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

# Load config
CONFIG = load_scheduler_config()
TIMEZONE = CONFIG['TIMEZONE']
GAME_DAY = CONFIG['GAME_DAY']
GAME_START_HOUR = CONFIG['GAME_START_HOUR']
GAME_START_MINUTE = CONFIG['GAME_START_MINUTE']
GAME_TIME_CHANGES = CONFIG['GAME_TIME_CHANGES']
SIGNUP_OPEN_DAY = CONFIG['SIGNUP_OPEN_DAY']
SIGNUP_OPEN_HOUR = CONFIG['SIGNUP_OPEN_HOUR']
SIGNUP_OPEN_MINUTE = CONFIG['SIGNUP_OPEN_MINUTE']


def at_local_time(day, hour, minute):
    """Warsaw datetime for a wall-clock time on a date. localize() picks that
    date's UTC offset (CET/CEST) - shifting another datetime by days and
    calling replace() would keep its old offset across a DST switch."""
    return TIMEZONE.localize(datetime(day.year, day.month, day.day, hour, minute))


def game_start_on(day):
    """Game start on the given date: the base time unless a `time_changes` entry applies"""
    hour, minute = GAME_START_HOUR, GAME_START_MINUTE
    for since, change_hour, change_minute in GAME_TIME_CHANGES:
        if since <= day:
            hour, minute = change_hour, change_minute
    return at_local_time(day, hour, minute)


def get_next_game_time(weeks_ahead=0):
    """Gets the date of the next game (never today's - on game day it's next week's)"""
    now = datetime.now(TIMEZONE)
    days_ahead = GAME_DAY - now.weekday()
    
    if days_ahead <= 0:
        days_ahead += 7
    
    return game_start_on(now.date() + timedelta(days=days_ahead, weeks=weeks_ahead))


def parse_game_time(start_time):
    """Safely parse game start_time from database, handling both string and datetime objects"""
    if isinstance(start_time, str):
        return datetime.fromisoformat(start_time.replace('Z', '+00:00')).astimezone(TIMEZONE)
    else:
        # start_time is already a datetime object
        return start_time.astimezone(TIMEZONE)


def get_signup_opening_time(game_time):
    """Calculate when signups open for a given game"""
    # Signups open on a specific day of the week before the game
    days_to_signup = game_time.weekday() - SIGNUP_OPEN_DAY
    
    # If the signup day is later in the week than the game,
    # or it's the same day but after the hour, take the previous week
    if days_to_signup <= 0:
        days_to_signup += 7
    
    signup_day = game_time.date() - timedelta(days=days_to_signup)
    return at_local_time(signup_day, SIGNUP_OPEN_HOUR, SIGNUP_OPEN_MINUTE)


def activate_games_for_signup(connection) -> int:
    """Activate games when their signup period should open"""
    logger.info("Checking for games to activate...")
    now = datetime.now(TIMEZONE)
    
    try:
        # Get inactive games
        inactive_games = execute_query(connection, "SELECT * FROM games WHERE active = FALSE")
        
        activated_count = 0
        for game in inactive_games:
            game_time = parse_game_time(game['start_time'])
            signup_open_time = get_signup_opening_time(game_time)
            
            # Activate if signups should already be open AND the game hasn't happened yet
            if now >= signup_open_time and game_time > now:
                execute_query(
                    connection, 
                    "UPDATE games SET active = TRUE WHERE id = %s",
                    (game['id'],)
                )
                logger.info(f"Activated game on {game_time.strftime('%d.%m.%Y %H:%M')} (signups open since {signup_open_time.strftime('%d.%m.%Y %H:%M')})")
                activated_count += 1
            elif now >= signup_open_time and game_time <= now:
                logger.info(f"Skipped activating game on {game_time.strftime('%d.%m.%Y %H:%M')} - it already took place")
        
        if activated_count == 0:
            logger.info("No games to activate")
        
        return activated_count
        
    except Exception as e:
        logger.error(f"Failed to activate games: {e}")
        raise


def get_database_connection():
    """Get database connection from GitHub Secrets"""
    database_url = os.getenv('SUPABASE_DATABASE_URL')
    
    if not database_url:
        raise ValueError("Missing SUPABASE_DATABASE_URL environment variable (GitHub Secrets)")

    logger.info("Connecting to Supabase PostgreSQL...")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor, sslmode='require')


def execute_query(connection, query: str, params=None):
    """Execute query and return results"""
    with connection.cursor() as cur:
        cur.execute(query, params)
        if query.strip().lower().startswith('select'):
            return [dict(row) for row in cur.fetchall()]
        connection.commit()
        return cur.rowcount


def deactivate_past_games(connection) -> int:
    """Deactivate past games"""
    logger.info("Checking for past games to deactivate...")
    now = datetime.now(TIMEZONE)
    
    try:
        # Get active games
        active_games = execute_query(connection, "SELECT * FROM games WHERE active = TRUE")
        
        deactivated_count = 0
        for game in active_games:
            game_time = parse_game_time(game['start_time'])
            
            # Deactivate if the game has already taken place
            if game_time <= now:
                execute_query(
                    connection, 
                    "UPDATE games SET active = FALSE WHERE id = %s",
                    (game['id'],)
                )
                logger.info(f"Deactivated game from {game_time.strftime('%d.%m.%Y %H:%M')}")
                deactivated_count += 1
        
        if deactivated_count == 0:
            logger.info("No past games to deactivate")
        
        return deactivated_count
        
    except Exception as e:
        logger.error(f"Failed to deactivate games: {e}")
        raise


def create_upcoming_games(connection) -> int:
    """Create games for next week"""
    logger.info("Checking whether new games need to be created...")
    
    created_count = 0
    
    try:
        for weeks_ahead in range(1):
            if create_game_for_week(connection, weeks_ahead):
                created_count += 1
        
        if created_count == 0:
            logger.info("All games for the upcoming week already exist")

        return created_count
        
    except Exception as e:
        logger.error(f"Failed to create games: {e}")
        raise


def create_game_for_week(connection, weeks_ahead: int) -> bool:
    """Create game for specific week if it doesn't exist"""
    try:
        game_time = get_next_game_time(weeks_ahead)
        
        # Check if a game already exists
        existing_games = execute_query(connection, "SELECT * FROM games")
        
        for game in existing_games:
            existing_time = parse_game_time(game['start_time'])
            if existing_time.date() == game_time.date():
                return False
        
        # Create a new game (inactive until signup opening)
        new_game_id = str(uuid.uuid4())
        execute_query(
            connection,
            "INSERT INTO games (id, start_time, active) VALUES (%s, %s, %s)",
            (new_game_id, game_time.isoformat(), False)
        )
        
        logger.info(f"Created new game for {game_time.strftime('%d.%m.%Y %H:%M')} (inactive)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create game: {e}")
        return False


def get_scheduler_stats(connection) -> dict:
    """Get current scheduler statistics"""
    try:
        # Active games
        active_games = execute_query(connection, "SELECT * FROM games WHERE active = TRUE")
        
        # Signup statistics
        total_signups = 0
        for game in active_games:
            signups = execute_query(
                connection,
                "SELECT COUNT(*) as count FROM signups WHERE game_id = %s",
                (game['id'],)
            )
            total_signups += signups[0]['count'] if signups else 0
        
        # All games
        all_games = execute_query(connection, "SELECT COUNT(*) as count FROM games")
        total_games_count = all_games[0]['count'] if all_games else 0
        
        return {
            'active_games_count': len(active_games),
            'total_signups': total_signups,
            'total_games_count': total_games_count
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
        return {
            'active_games_count': 0,
            'total_signups': 0,
            'total_games_count': 0
        }


def main():
    """Main scheduler function"""
    logger.info("=" * 50)
    logger.info("SCHEDULER STARTED")
    logger.info("=" * 50)
    
    try:
        # Database connection
        connection = get_database_connection()
        
        # Initial statistics
        initial_stats = get_scheduler_stats(connection)
        logger.info(f"Initial state: {initial_stats['active_games_count']} active games, {initial_stats['total_signups']} signups")
        
        # Deactivate past games
        deactivated = deactivate_past_games(connection)
        
        # Create new games
        created = create_upcoming_games(connection)
        
        # Activate games for which it's time for signups (after creating new ones)
        activated = activate_games_for_signup(connection)
        
        # Final statistics
        final_stats = get_scheduler_stats(connection)
        
        # Summary
        logger.info("=" * 50)
        logger.info("SUMMARY:")
        logger.info(f"   Deactivated: {deactivated} games")
        logger.info(f"   Activated: {activated} games")
        logger.info(f"   Created: {created} new games")
        logger.info(f"   Final state: {final_stats['active_games_count']} active games")
        logger.info(f"   Total signups: {final_stats['total_signups']}")
        logger.info(f"   Total games: {final_stats['total_games_count']}")
        logger.info("SCHEDULER COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        
        connection.close()
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}")
        logger.error("SCHEDULER FAILED")
        logger.info("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
