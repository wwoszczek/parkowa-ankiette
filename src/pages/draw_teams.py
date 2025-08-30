"""
Page for drawing team lineups
"""

import streamlit as st
from datetime import datetime
from src.database import SupabaseDB
from src.constants import TIMEZONE
from src.utils.datetime_utils import is_draw_time_allowed, parse_game_time
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.team_utils import draw_teams, is_valid_player_count
from src.utils.teams_db import save_teams, get_teams_for_game
from src.game_config import DRAW_NOT_AVAILABLE_MESSAGE, MANUAL_DRAW_MESSAGE


def display_teams(teams_dict: dict):
    """Displays team lineups in columns"""
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


def draw_page(db: SupabaseDB):
    """Team lineup drawing page"""
    st.header("🎲 Losowanie składów")
    
    # Check if draw time is allowed
    if not is_draw_time_allowed():
        st.warning(DRAW_NOT_AVAILABLE_MESSAGE)
        return
    
    # Get active games
    active_games = get_active_games(db)
    
    if not active_games:
        st.warning("Brak aktywnych gierek.")
        return
    
    for game in active_games:
        game_time = parse_game_time(game['start_time'])
        st.subheader(f"Gierka: {game_time.strftime('%d.%m.%Y %H:%M')}")
        
        signups = get_signups_for_game(db, game['id'])
        num_players = len(signups)
        
        st.info(f"Zapisanych graczy: {num_players}")
        
        if is_valid_player_count(num_players):
            if st.button(f"Wylosuj składy dla {num_players} graczy", key=f"draw_{game['id']}"):
                players = [signup['nickname'] for signup in signups]
                teams = draw_teams(players, num_players)
                
                if save_teams(db, game['id'], teams):
                    st.success("Składy wylosowane pomyślnie!")
        else:
            st.error(MANUAL_DRAW_MESSAGE)
        
        # Show current lineups if they exist
        teams = get_teams_for_game(db, game['id'])
        if teams:
            st.subheader("Wylosowane składy:")
            
            # Group by colors
            teams_dict = {}
            for team in teams:
                teams_dict[team['team_color']] = team['players']
            
            display_teams(teams_dict)
        
        st.divider()
