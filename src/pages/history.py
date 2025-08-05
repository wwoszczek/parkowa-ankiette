"""
Game history page
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.database import NeonDB
from src.constants import TIMEZONE
from src.utils.game_utils import get_past_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.teams_db import get_teams_for_game
from src.utils.datetime_utils import parse_game_time, parse_timestamp


def display_history_teams(teams_dict: dict):
    """Displays team lineups in history"""
    if len(teams_dict) == 2:
        col1, col2 = st.columns(2)
        colors = list(teams_dict.keys())
        
        with col1:
            st.markdown(f"**{colors[0].upper()}**")
            for player in teams_dict[colors[0]]:
                st.write(f"• {player}")
        
        with col2:
            st.markdown(f"**{colors[1].upper()}**")
            for player in teams_dict[colors[1]]:
                st.write(f"• {player}")
    
    elif len(teams_dict) == 3:
        col1, col2, col3 = st.columns(3)
        colors = list(teams_dict.keys())
        
        with col1:
            st.markdown(f"**{colors[0].upper()}**")
            for player in teams_dict[colors[0]]:
                st.write(f"• {player}")
        
        with col2:
            st.markdown(f"**{colors[1].upper()}**")
            for player in teams_dict[colors[1]]:
                st.write(f"• {player}")
        
        with col3:
            st.markdown(f"**{colors[2].upper()}**")
            for player in teams_dict[colors[2]]:
                st.write(f"• {player}")


def history_page(db: NeonDB):
    """History page"""
    st.header("📚 Historia gierek")
    
    try:
        # Get all inactive games
        past_games = get_past_games(db)
        
        if not past_games:
            st.info("Brak gierek w historii.")
            return
        
        for game in past_games:
            game_time = parse_game_time(game['start_time'])
            
            with st.expander(f"Gierka z {game_time.strftime('%d.%m.%Y %H:%M')}"):
                # List of signups
                signups = get_signups_for_game(db, game['id'])
                
                if signups:
                    st.subheader("Lista zapisanych:")
                    df = pd.DataFrame([
                        {
                            "Lp.": i+1,
                            "Nickname": signup['nickname'],
                            "Czas zapisu": parse_timestamp(signup['timestamp']).strftime('%d.%m.%Y %H:%M:%S')
                        }
                        for i, signup in enumerate(signups)
                    ])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.info(f"Łącznie: {len(signups)} osób")
                else:
                    st.info("Brak zapisów.")
                
                # Team lineups
                teams = get_teams_for_game(db, game['id'])
                if teams:
                    st.subheader("Składy drużyn:")
                    
                    teams_dict = {}
                    for team in teams:
                        teams_dict[team['team_color']] = team['players']
                    
                    display_history_teams(teams_dict)
                else:
                    st.info("Brak informacji o składach drużyn.")
    
    except Exception as e:
        st.error(f"Błąd podczas pobierania historii: {e}")
