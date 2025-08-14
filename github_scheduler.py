#!/usr/bin/env python3
"""
GitHub Actions Scheduler - independent from Streamlit UI
Runs automatically every hour via GitHub Actions
"""

import os
import sys
import logging
from datetime import datetime, timedelta
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
                'SIGNUP_OPEN_DAY': config['signup']['day'],
                'SIGNUP_OPEN_HOUR': config['signup']['hour'],
                'SIGNUP_OPEN_MINUTE': config['signup']['minute']
            }
    except Exception as e:
        logger.error(f"Błąd wczytywania konfiguracji: {e}")
        sys.exit(1)

# Load config
CONFIG = load_scheduler_config()
TIMEZONE = CONFIG['TIMEZONE']
GAME_DAY = CONFIG['GAME_DAY']
GAME_START_HOUR = CONFIG['GAME_START_HOUR']
GAME_START_MINUTE = CONFIG['GAME_START_MINUTE']
SIGNUP_OPEN_DAY = CONFIG['SIGNUP_OPEN_DAY']
SIGNUP_OPEN_HOUR = CONFIG['SIGNUP_OPEN_HOUR']
SIGNUP_OPEN_MINUTE = CONFIG['SIGNUP_OPEN_MINUTE']


def get_next_game_time():
    """Gets the date of the next game"""
    now = datetime.now(TIMEZONE)
    days_ahead = GAME_DAY - now.weekday()
    
    # If today is game day but after start time, take next week
    if days_ahead <= 0 or (days_ahead == 0 and now.hour >= GAME_START_HOUR):
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


def get_signup_opening_time(game_time):
    """Calculate when signups open for a given game"""
    # Signups open on a specific day of the week before the game
    days_to_signup = game_time.weekday() - SIGNUP_OPEN_DAY
    
    # If the signup day is later in the week than the game,
    # or it's the same day but after the hour, take the previous week
    if days_to_signup <= 0:
        days_to_signup += 7
    
    signup_open = game_time - timedelta(days=days_to_signup)
    return signup_open.replace(hour=SIGNUP_OPEN_HOUR, minute=SIGNUP_OPEN_MINUTE, second=0, microsecond=0)


def activate_games_for_signup(connection) -> int:
    """Activate games when their signup period should open"""
    logger.info("🔍 Sprawdzanie gierek do aktywacji...")
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
                logger.info(f"🟢 Aktywowano gierkę z {game_time.strftime('%d.%m.%Y %H:%M')} (zapisy otwarte od {signup_open_time.strftime('%d.%m.%Y %H:%M')})")
                activated_count += 1
            elif now >= signup_open_time and game_time <= now:
                logger.info(f"⏭️  Pominięto aktywację gierki z {game_time.strftime('%d.%m.%Y %H:%M')} - gierka już się odbyła")
        
        if activated_count == 0:
            logger.info("✅ Brak gierek do aktywacji")
        
        return activated_count
        
    except Exception as e:
        logger.error(f"❌ Błąd aktywacji gierek: {e}")
        raise


def get_database_connection():
    """Get database connection from GitHub Secrets"""
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        raise ValueError("❌ Brak zmiennej NEON_DATABASE_URL w GitHub Secrets")
    
    logger.info("✅ Łączenie z Neon PostgreSQL...")
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
    logger.info("🔍 Sprawdzanie przeszłych gierek do dezaktywacji...")
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
                logger.info(f"🔴 Dezaktywowano gierkę z {game_time.strftime('%d.%m.%Y %H:%M')}")
                deactivated_count += 1
        
        if deactivated_count == 0:
            logger.info("✅ Brak przeszłych gierek do dezaktywacji")
        
        return deactivated_count
        
    except Exception as e:
        logger.error(f"❌ Błąd dezaktywacji gierek: {e}")
        raise


def create_upcoming_games(connection) -> int:
    """Create games for next week"""
    logger.info("🏗️ Sprawdzanie czy potrzeba utworzyć nowe gierki...")
    
    created_count = 0
    
    try:
        for weeks_ahead in range(1):
            if create_game_for_week(connection, weeks_ahead):
                created_count += 1
        
        if created_count == 0:
            logger.info("✅ Wszystkie gierki na kolejny 1 tydzień już istnieją")

        return created_count
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia gierek: {e}")
        raise


def create_game_for_week(connection, weeks_ahead: int) -> bool:
    """Create game for specific week if it doesn't exist"""
    try:
        game_time = get_next_game_time() + timedelta(weeks=weeks_ahead)
        
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
        
        logger.info(f"🆕 Utworzono nową gierkę na {game_time.strftime('%d.%m.%Y %H:%M')} (nieaktywna)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia gierki: {e}")
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
        logger.error(f"❌ Błąd pobierania statystyk: {e}")
        return {
            'active_games_count': 0,
            'total_signups': 0,
            'total_games_count': 0
        }


def main():
    """Main scheduler function"""
    logger.info("=" * 50)
    logger.info("🤖 SCHEDULER STARTED")
    logger.info("=" * 50)
    
    try:
        # Database connection
        connection = get_database_connection()
        
        # Initial statistics
        initial_stats = get_scheduler_stats(connection)
        logger.info(f"📊 Stan początkowy: {initial_stats['active_games_count']} aktywnych gierek, {initial_stats['total_signups']} zapisów")
        
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
        logger.info("📈 PODSUMOWANIE:")
        logger.info(f"   🔴 Dezaktywowano: {deactivated} gierek")
        logger.info(f"   🟢 Aktywowano: {activated} gierek")
        logger.info(f"   🆕 Utworzono: {created} nowych gierek")
        logger.info(f"   📊 Stan końcowy: {final_stats['active_games_count']} aktywnych gierek")
        logger.info(f"   👥 Łącznie zapisów: {final_stats['total_signups']}")
        logger.info(f"   🎯 Wszystkich gierek: {final_stats['total_games_count']}")
        logger.info("✅ SCHEDULER COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        
        connection.close()
        
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR: {e}")
        logger.error("❌ SCHEDULER FAILED")
        logger.info("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
