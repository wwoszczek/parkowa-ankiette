#!/usr/bin/env python3
"""
GitHub Actions Scheduler - niezależny od UI Streamlit
Uruchamiany automatycznie co godzinę przez GitHub Actions
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import uuid
from supabase import create_client, Client

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/scheduler.log')
    ]
)
logger = logging.getLogger(__name__)

# Dodaj ścieżkę do głównego katalogu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.config import TIMEZONE
    from src.utils.datetime_utils import get_next_game_time
    from src.game_config import load_config
except ImportError as e:
    logger.error(f"Błąd importu: {e}")
    sys.exit(1)


def get_supabase_client() -> Client:
    """Inicjalizacja klienta Supabase z GitHub Secrets"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError("❌ Brak zmiennych SUPABASE_URL i SUPABASE_KEY w GitHub Secrets")
    
    logger.info("✅ Łączenie z Supabase...")
    return create_client(url, key)


def deactivate_past_games(supabase: Client) -> int:
    """Dezaktywuje przeszłe gierki"""
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
    """Tworzy gierki na kolejne 4 tygodnie"""
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
    """Tworzy gierkę na określony tydzień w przyszłości"""
    try:
        base_game_time = get_next_game_time()
        game_time = base_game_time + timedelta(weeks=weeks_ahead)
        
        # Sprawdź czy gierka już istnieje
        response = supabase.table('games').select('*').execute()
        existing_games = [
            game for game in response.data 
            if datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE).date() == game_time.date()
        ]
        
        if not existing_games:
            # Utwórz nową gierkę
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
    """Pobiera statystyki schedulera"""
    try:
        # Aktywne gierki
        active_games = supabase.table('games').select('*').eq('active', True).execute()
        
        # Najbliższa gierka
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
            'next_game': next_game.strftime('%d.%m.%Y %H:%M') if next_game else 'Brak',
            'total_games_count': len(supabase.table('games').select('*').execute().data)
        }
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk: {e}")
        return {}


def main():
    """Główna funkcja schedulera GitHub Actions"""
    start_time = datetime.now(TIMEZONE)
    logger.info(f"🚀 GitHub Actions Scheduler - start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Sprawdź czy to wymuszenie
    force_run = os.getenv('FORCE_RUN', 'false').lower() == 'true'
    if force_run:
        logger.info("⚡ WYMUSZENIE - pełne sprawdzenie schedulera")
    
    try:
        # 1. Inicjalizacja
        supabase = get_supabase_client()
        
        # 2. Pobierz statystyki początkowe
        initial_stats = get_scheduler_stats(supabase)
        logger.info(f"📊 Stan początkowy: {initial_stats['active_games_count']} aktywnych gierek")
        
        # 4. Dezaktywuj przeszłe gierki
        deactivated = deactivate_past_games(supabase)
        
        # 5. Utwórz nowe gierki
        created = create_upcoming_games(supabase)
        
        # 6. Pobierz statystyki końcowe
        final_stats = get_scheduler_stats(supabase)
        
        # 7. Podsumowanie
        end_time = datetime.now(TIMEZONE)
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 50)
        logger.info("✅ SCHEDULER ZAKOŃCZONY POMYŚLNIE")
        logger.info(f"⏱️  Czas wykonania: {duration:.2f}s")
        logger.info(f"🔴 Dezaktywowano: {deactivated} gierek")
        logger.info(f"🟢 Utworzono: {created} nowych gierek")
        logger.info(f"📊 Aktywne gierki: {final_stats['active_games_count']}")
        logger.info(f"🎯 Najbliższa gierka: {final_stats['next_game']}")
        logger.info("=" * 50)
        
        # Sprawdzenie czy wszystko OK
        if final_stats['upcoming_games_count'] < 4:
            logger.warning(f"⚠️  Tylko {final_stats['upcoming_games_count']} nadchodzących gierek (powinno być 4)")
        
    except Exception as e:
        logger.error(f"💥 KRYTYCZNY BŁĄD SCHEDULERA: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
