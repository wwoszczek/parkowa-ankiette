"""
Strona historii gierek
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.game_utils import get_past_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.teams_db import get_teams_for_game


def display_history_teams(teams_dict: dict):
    """Wyświetla składy drużyn w historii"""
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


def history_page(supabase: Client):
    """Strona historii"""
    st.header("📚 Historia gierek")
    
    try:
        # Pobierz wszystkie nieaktywne gierki
        past_games = get_past_games(supabase)
        
        if not past_games:
            st.info("Brak gierek w historii.")
            return
        
        for game in past_games:
            game_time = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE)
            
            with st.expander(f"Gierka z {game_time.strftime('%d.%m.%Y %H:%M')}"):
                # Lista zapisanych
                signups = get_signups_for_game(supabase, game['id'])
                
                if signups:
                    st.subheader("Lista zapisanych:")
                    df = pd.DataFrame([
                        {
                            "Lp.": i+1,
                            "Nickname": signup['nickname'],
                            "Czas zapisu": datetime.fromisoformat(signup['timestamp'].replace('Z', '+00:00')).astimezone(TIMEZONE).strftime('%d.%m.%Y %H:%M:%S')
                        }
                        for i, signup in enumerate(signups)
                    ])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.info(f"Łącznie: {len(signups)} osób")
                else:
                    st.info("Brak zapisów.")
                
                # Składy drużyn
                teams = get_teams_for_game(supabase, game['id'])
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
