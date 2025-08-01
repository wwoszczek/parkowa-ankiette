"""
Strona zapisów na gierki
"""

import streamlit as st
from datetime import datetime
from supabase import Client
from src.config import TIMEZONE
from src.utils.game_utils import deactivate_past_games, create_new_game_if_needed, get_active_games
from src.utils.signup_utils import add_signup, remove_signup
from src.game_config import SIGNUP_OPENING_MESSAGE


def signup_page(supabase: Client):
    """Strona zapisów"""
    st.header("⚽ Zapisy na gierkę")
    
    # Aktualizuj stan gierek
    deactivate_past_games(supabase)
    create_new_game_if_needed(supabase)
    
    # Pobierz aktywne gierki
    active_games = get_active_games(supabase)
    
    if not active_games:
        st.warning(f"Brak aktywnych gierek. {SIGNUP_OPENING_MESSAGE}")
        return
    
    # Wybór gierki
    game_options = []
    for game in active_games:
        game_time = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00')).astimezone(TIMEZONE)
        game_options.append(f"{game_time.strftime('%d.%m.%Y %H:%M')} - {game['id']}")
    
    selected_game_str = st.selectbox("Wybierz gierkę:", game_options)
    if not selected_game_str:
        return
    
    selected_game_id = selected_game_str.split(" - ")[1]
    selected_game = next(game for game in active_games if game['id'] == selected_game_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Zapisz się")
        with st.form("signup_form"):
            nickname = st.text_input("Nickname:")
            password = st.text_input("Hasło:", type="password")
            submit = st.form_submit_button("Zapisz się")
            
            if submit and nickname and password:
                success, message = add_signup(supabase, selected_game_id, nickname, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        st.subheader("Wypisz się")
        with st.form("signout_form"):
            nickname_out = st.text_input("Nickname:", key="signout_nick")
            password_out = st.text_input("Hasło:", type="password", key="signout_pass")
            submit_out = st.form_submit_button("Wypisz się")
            
            if submit_out and nickname_out and password_out:
                success, message = remove_signup(supabase, selected_game_id, nickname_out, password_out)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
