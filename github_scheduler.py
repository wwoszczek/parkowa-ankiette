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

# Add path to main directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.config import TIMEZONE
    from src.utils.datetime_utils import get_next_game_time, parse_game_time
    from src.game_config import load_config
except ImportError as e:
    logger.error(f"Błąd importu: {e}")
    sys.exit(1)


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
        # Pobierz aktywne gierki
        active_games = execute_query(connection, "SELECT * FROM games WHERE active = TRUE")
        
        deactivated_count = 0
        for game in active_games:
            game_time = parse_game_time(game['start_time'])
            
            # Dezaktywuj jeśli gierka już się odbyła
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
    """Create games for next 4 weeks"""
    logger.info("🏗️ Sprawdzanie czy potrzeba utworzyć nowe gierki...")
    
    created_count = 0
    
    try:
        for weeks_ahead in range(4):
            if create_game_for_week(connection, weeks_ahead):
                created_count += 1
        
        if created_count == 0:
            logger.info("✅ Wszystkie gierki na kolejne 4 tygodnie już istnieją")
        
        return created_count
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia gierek: {e}")
        raise


def create_game_for_week(connection, weeks_ahead: int) -> bool:
    """Create game for specific week if it doesn't exist"""
    try:
        game_time = get_next_game_time() + timedelta(weeks=weeks_ahead)
        
        # Sprawdź czy gierka już istnieje
        existing_games = execute_query(connection, "SELECT * FROM games")
        
        for game in existing_games:
            existing_time = parse_game_time(game['start_time'])
            if existing_time.date() == game_time.date():
                return False
        
        # Utwórz nową gierkę
        new_game_id = str(uuid.uuid4())
        execute_query(
            connection,
            "INSERT INTO games (id, start_time, active) VALUES (%s, %s, %s)",
            (new_game_id, game_time.isoformat(), True)
        )
        
        logger.info(f"🆕 Utworzono nową gierkę na {game_time.strftime('%d.%m.%Y %H:%M')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia gierki: {e}")
        return False


def get_scheduler_stats(connection) -> dict:
    """Get current scheduler statistics"""
    try:
        # Aktywne gierki
        active_games = execute_query(connection, "SELECT * FROM games WHERE active = TRUE")
        
        # Statystyki zapisów
        total_signups = 0
        for game in active_games:
            signups = execute_query(
                connection,
                "SELECT COUNT(*) as count FROM signups WHERE game_id = %s",
                (game['id'],)
            )
            total_signups += signups[0]['count'] if signups else 0
        
        # Wszystkie gierki
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
        # Połączenie z bazą danych
        connection = get_database_connection()
        
        # Początkowe statystyki
        initial_stats = get_scheduler_stats(connection)
        logger.info(f"📊 Stan początkowy: {initial_stats['active_games_count']} aktywnych gierek, {initial_stats['total_signups']} zapisów")
        
        # Dezaktywuj przeszłe gierki
        deactivated = deactivate_past_games(connection)
        
        # Utwórz nowe gierki
        created = create_upcoming_games(connection)
        
        # Finalne statystyki
        final_stats = get_scheduler_stats(connection)
        
        # Podsumowanie
        logger.info("=" * 50)
        logger.info("📈 PODSUMOWANIE:")
        logger.info(f"   🔴 Dezaktywowano: {deactivated} gierek")
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
