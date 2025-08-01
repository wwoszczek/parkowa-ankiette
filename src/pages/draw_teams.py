"""
Strona losowania składów drużyn
"""

import streamlit as st
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.datetime_utils import is_draw_time_allowed
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.team_utils import draw_teams, is_valid_player_count
from src.utils.teams_db import save_teams, get_teams_for_game
from src.game_config import DRAW_NOT_AVAILABLE_MESSAGE, MANUAL_DRAW_MESSAGE


def display_teams(teams_dict: dict):
    """Wyświetla składy drużyn w kolumnach"""
    if len(teams_dict) == 2:
        col1, col2 = st.columns(2)
        colors = list(teams_dict.keys())
        
        with col1:
            st.markdown(f"**Drużyna {colors[0].upper()}**")
            for i, player in enumerate(teams_dict[colors[0]], 1):
                st.write(f"{i}. {player}")
        
        with col2:
            st.markdown(f"**Drużyna {colors[1].upper()}**")
            for i, player in enumerate(teams_dict[colors[1]], 1):
                st.write(f"{i}. {player}")
    
    elif len(teams_dict) == 3:
        col1, col2, col3 = st.columns(3)
        colors = list(teams_dict.keys())
        
        with col1:
            st.markdown(f"**Drużyna {colors[0].upper()}**")
            for i, player in enumerate(teams_dict[colors[0]], 1):
                st.write(f"{i}. {player}")
        
        with col2:
            st.markdown(f"**Drużyna {colors[1].upper()}**")
            for i, player in enumerate(teams_dict[colors[1]], 1):
                st.write(f"{i}. {player}")
        
        with col3:
            st.markdown(f"**Drużyna {colors[2].upper()}**")
            for i, player in enumerate(teams_dict[colors[2]], 1):
                st.write(f"{i}. {player}")


def draw_page(supabase: Client):
    """Strona losowania składów"""
    st.header("🎲 Losowanie składów")
    
    # Sprawdź czy jest dozwolony czas na losowanie
    if not is_draw_time_allowed():
        st.warning(DRAW_NOT_AVAILABLE_MESSAGE)
        return
    
    # Pobierz aktywne gierki
    active_games = get_active_games(supabase)
    
    if not active_games:
        st.warning("Brak aktywnych gierek.")
        return
    
    for game in active_games:
        game_time = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE)
        st.subheader(f"Gierka: {game_time.strftime('%d.%m.%Y %H:%M')}")
        
        signups = get_signups_for_game(supabase, game['id'])
        num_players = len(signups)
        
        st.info(f"Zapisanych graczy: {num_players}")
        
        if is_valid_player_count(num_players):
            if st.button(f"Wylosuj składy dla {num_players} graczy", key=f"draw_{game['id']}"):
                players = [signup['nickname'] for signup in signups]
                teams = draw_teams(players, num_players)
                
                if save_teams(supabase, game['id'], teams):
                    st.success("Składy wylosowane pomyślnie!")
                    st.rerun()
        else:
            st.error(MANUAL_DRAW_MESSAGE)
        
        # Pokaż aktualne składy jeśli istnieją
        teams = get_teams_for_game(supabase, game['id'])
        if teams:
            st.subheader("Wylosowane składy:")
            
            # Grupuj według kolorów
            teams_dict = {}
            for team in teams:
                teams_dict[team['team_color']] = team['players']
            
            display_teams(teams_dict)
        
        st.divider()
