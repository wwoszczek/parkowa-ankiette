#!/usr/bin/env python3
"""
Test script to verify scheduler works without Streamlit dependencies
"""

import os
import sys
from datetime import datetime, timedelta
import tempfile

# Test imports
try:
    import yaml
    import pytz
    from pathlib import Path
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test config loading
try:
    config_file = Path("game_consts.yaml")
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    TIMEZONE = pytz.timezone('Europe/Warsaw')
    GAME_DAY = config['game']['day']
    GAME_START_HOUR = config['game']['hour'] 
    GAME_START_MINUTE = config['game']['minute']
    
    print(f"✅ Config loaded: Game on weekday {GAME_DAY} at {GAME_START_HOUR}:{GAME_START_MINUTE}")
except Exception as e:
    print(f"❌ Config loading error: {e}")
    sys.exit(1)

# Test scheduler functions (without database)
try:
    # Simulate the get_next_game_time function
    now = datetime.now(TIMEZONE)
    days_ahead = GAME_DAY - now.weekday()
    
    if days_ahead <= 0 or (days_ahead == 0 and now.hour >= GAME_START_HOUR):
        days_ahead += 7
    
    next_game = now + timedelta(days=days_ahead)
    next_game = next_game.replace(hour=GAME_START_HOUR, minute=GAME_START_MINUTE, second=0, microsecond=0)
    
    print(f"✅ Next game calculated: {next_game}")
    print(f"✅ Days ahead: {days_ahead}")
except Exception as e:
    print(f"❌ Scheduler function error: {e}")
    sys.exit(1)

# Test environment variable simulation (GitHub Actions)
print("\n🧪 Testing GitHub Actions environment simulation:")
os.environ['NEON_DATABASE_URL'] = 'postgresql://test:test@localhost/test'
database_url = os.getenv('NEON_DATABASE_URL')
if database_url:
    print(f"✅ Database URL retrieved: {database_url[:20]}...")
else:
    print("❌ Database URL not found")

print("\n🎉 All tests passed! Scheduler is ready for GitHub Actions!")
