"""
Page for listing signed up players for each game
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.database import NeonDB
from src.config import TIMEZONE
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.datetime_utils import parse_game_time, parse_timestamp


def list_page(db: NeonDB):
    """Page with list of signed up players"""
    st.header("📋 Lista zapisanych")
    
    # Get active games
    active_games = get_active_games(db)
    
    if not active_games:
        st.warning("Brak aktywnych gierek.")
        return
    
    for game in active_games:
        game_time = parse_game_time(game['start_time'])
        st.subheader(f"Gierka: {game_time.strftime('%d.%m.%Y %H:%M')}")
        
        signups = get_signups_for_game(db, game['id'])
        
        if signups:
            df = pd.DataFrame([
                {
                    "Lp.": i+1,
                    "Nickname": signup['nickname'],
                    "Czas zapisu": parse_timestamp(signup['timestamp']).strftime('%d.%m.%Y %H:%M:%S')
                }
                for i, signup in enumerate(signups)
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"Łącznie zapisanych: {len(signups)} osób")
        else:
            st.info("Brak zapisów na tę gierkę.")
        
        st.divider()
