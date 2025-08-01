"""
Strona z listą zapisanych graczy
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import get_signups_for_game


def list_page(supabase: Client):
    """Strona z listą zapisanych"""
    st.header("📋 Lista zapisanych")
    
    # Pobierz aktywne gierki
    active_games = get_active_games(supabase)
    
    if not active_games:
        st.warning("Brak aktywnych gierek.")
        return
    
    for game in active_games:
        game_time = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE)
        st.subheader(f"Gierka: {game_time.strftime('%d.%m.%Y %H:%M')}")
        
        signups = get_signups_for_game(supabase, game['id'])
        
        if signups:
            df = pd.DataFrame([
                {
                    "Lp.": i+1,
                    "Nickname": signup['nickname'],
                    "Czas zapisu": datetime.fromisoformat(signup['timestamp'].replace('Z', '+00:00')).astimezone(TIMEZONE).strftime('%d.%m.%Y %H:%M:%S')
                }
                for i, signup in enumerate(signups)
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"Łącznie zapisanych: {len(signups)} osób")
        else:
            st.info("Brak zapisów na tę gierkę.")
        
        st.divider()
