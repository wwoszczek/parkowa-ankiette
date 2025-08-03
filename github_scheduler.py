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
from supabase import create_client, Client

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
    from src.utils.datetime_utils import get_next_game_time
    from src.game_config import load_config
except ImportError as e:
    logger.error(f"Błąd importu: {e}")
    sys.exit(1)


def get_supabase_client() -> Client:
    """Initialize Supabase client from GitHub Secrets"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError("❌ Brak zmiennych SUPABASE_URL i SUPABASE_KEY w GitHub Secrets")
    
    logger.info("✅ Łączenie z Supabase...")
    return create_client(url, key)


def deactivate_past_games(supabase: Client) -> int:
    """Deactivate past games"""
    logger.info("🔍 Sprawdzanie przeszłych gierek do dezaktywacji...")
    now = datetime.now(TIMEZONE)
    
    try:
        # Pobierz aktywne gierki
        response = supabase.table('games').select('*').eq('active', True).execute()
        
        deactivated_count = 0
        for game in response.data:
            game_time = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE)
            
            # Dezaktywuj jeśli gierka już się odbyła
            if game_time <= now:
                supabase.table('games').update({'active': False}).eq('id', game['id']).execute()
                logger.info(f"🔴 Dezaktywowano gierkę z {game_time.strftime('%d.%m.%Y %H:%M')}")
                deactivated_count += 1
        
        if deactivated_count == 0:
            logger.info("✅ Brak przeszłych gierek do dezaktywacji")
        
        return deactivated_count
        
    except Exception as e:
        logger.error(f"❌ Błąd dezaktywacji gierek: {e}")
        raise


def create_upcoming_games(supabase: Client) -> int:
    """Create games for next 4 weeks"""
    logger.info("🏗️ Sprawdzanie czy potrzeba utworzyć nowe gierki...")
    
    created_count = 0
    
    try:
        for weeks_ahead in range(4):
            if create_game_for_week(supabase, weeks_ahead):
                created_count += 1
        
        if created_count == 0:
            logger.info("✅ Wszystkie gierki na kolejne 4 tygodnie już istnieją")
        
        return created_count
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia gierek: {e}")
        raise


def create_game_for_week(supabase: Client, weeks_ahead: int) -> bool:
    """Create game for specific week in the future"""
    try:
        base_game_time = get_next_game_time()
        game_time = base_game_time + timedelta(weeks=weeks_ahead)
        
        # Check if game already exists
        response = supabase.table('games').select('*').execute()
        existing_games = [
            game for game in response.data 
            if datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE).date() == game_time.date()
        ]
        
        if not existing_games:
            # Create new game
            new_game = {
                'id': str(uuid.uuid4()),
                'start_time': game_time.isoformat(),
                'active': True
            }
            supabase.table('games').insert(new_game).execute()
            logger.info(f"🟢 Utworzono gierkę na {game_time.strftime('%d.%m.%Y %H:%M')}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia gierki na +{weeks_ahead} tygodni: {e}")
        raise


def get_scheduler_stats(supabase: Client) -> dict:
    """Gets scheduler statistics"""
    try:
        # Active games
        active_games = supabase.table('games').select('*').eq('active', True).execute()
        
        # Next game
        now = datetime.now(TIMEZONE)
        upcoming_games = [
            game for game in active_games.data
            if datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE) > now
        ]
        
        next_game = None
        if upcoming_games:
            next_game_data = min(upcoming_games, 
                key=lambda g: datetime.fromisoformat(g['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE))
            next_game = datetime.fromisoformat(next_game_data['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE)
        
        return {
            'active_games_count': len(active_games.data),
            'upcoming_games_count': len(upcoming_games),
            'next_game': next_game.strftime('%d.%m.%Y %H:%M') if next_game else 'None',
            'total_games_count': len(supabase.table('games').select('*').execute().data)
        }
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk: {e}")
        return {}


def main():
    """Main function of GitHub Actions scheduler"""
    start_time = datetime.now(TIMEZONE)
    logger.info(f"🚀 GitHub Actions Scheduler - start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Check if this is forced run
    force_run = os.getenv('FORCE_RUN', 'false').lower() == 'true'
    if force_run:
        logger.info("⚡ FORCE - full scheduler check")
    
    try:
        # 1. Initialization
        supabase = get_supabase_client()
        
        # 2. Get initial statistics
        initial_stats = get_scheduler_stats(supabase)
        logger.info(f"📊 Initial state: {initial_stats['active_games_count']} active games")
        
        # 4. Deactivate past games
        deactivated = deactivate_past_games(supabase)
        
        # 5. Create new games
        created = create_upcoming_games(supabase)
        
        # 6. Get final statistics
        final_stats = get_scheduler_stats(supabase)
        
        # 7. Summary
        end_time = datetime.now(TIMEZONE)
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 50)
        logger.info("✅ SCHEDULER COMPLETED SUCCESSFULLY")
        logger.info(f"⏱️  Execution time: {duration:.2f}s")
        logger.info(f"🔴 Deactivated: {deactivated} games")
        logger.info(f"🟢 Created: {created} new games")
        logger.info(f"📊 Active games: {final_stats['active_games_count']}")
        logger.info(f"🎯 Next game: {final_stats['next_game']}")
        logger.info("=" * 50)
        
        # Check if everything is OK
        if final_stats['upcoming_games_count'] < 4:
            logger.warning(f"⚠️  Only {final_stats['upcoming_games_count']} upcoming games (should be 4)")
        
    except Exception as e:
        logger.error(f"💥 CRITICAL SCHEDULER ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
