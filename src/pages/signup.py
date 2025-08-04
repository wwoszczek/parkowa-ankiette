"""
Game signup page
"""

import streamlit as st
from datetime import datetime
from src.database import NeonDB
from src.config import TIMEZONE
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import add_signup, remove_signup
from src.utils.datetime_utils import parse_game_time
from src.utils.security import (
    RateLimiter, 
    validate_nickname, 
    validate_password, 
    sanitize_input,
    log_security_event
)
from src.game_config import SIGNUP_OPENING_MESSAGE


def signup_page(db: NeonDB):
    """Signup page"""
    st.header("⚽ Zapisy na gierkę")
    
    # Get active games
    active_games = get_active_games(db)
    
    if not active_games:
        st.warning(f"Brak aktywnych gierek. {SIGNUP_OPENING_MESSAGE}")
        return
    
    # Game selection
    game_options = []
    game_mapping = {}
    for game in active_games:
        game_time = parse_game_time(game['start_time'])
        display_name = game_time.strftime('%d.%m.%Y %H:%M')
        game_options.append(display_name)
        game_mapping[display_name] = game
    
    selected_game_str = st.selectbox("Wybierz gierkę:", game_options)
    if not selected_game_str:
        return
    
    selected_game = game_mapping[selected_game_str]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Zapisz się")
        
        # Check rate limiting
        if not RateLimiter.check_signup_rate_limit("signup_attempts", 3, 5):
            cooldown = RateLimiter.get_remaining_cooldown("signup_attempts", 5)
            st.error(f"⏰ Za dużo prób zapisu. Spróbuj ponownie za {cooldown} sekund.")
            log_security_event("rate_limit", f"signup attempts exceeded")
            return
        
        with st.form("signup_form"):
            nickname = st.text_input("Nickname:")
            password = st.text_input("Hasło:", type="password")
            submit = st.form_submit_button("Zapisz się")
            
            if submit:
                # Sanitization and validation
                nickname = sanitize_input(nickname)
                password = sanitize_input(password)
                
                # Nickname validation
                nickname_valid, nickname_error = validate_nickname(nickname)
                if not nickname_valid:
                    st.error(f"❌ Błąd nickname: {nickname_error}")
                    log_security_event("invalid_nickname", f"nickname: {nickname[:10]}...")
                    return
                
                # Password validation
                password_valid, password_error = validate_password(password)
                if not password_valid:
                    st.error(f"❌ Błąd hasła: {password_error}")
                    log_security_event("invalid_password", "password validation failed")
                    return
                
                # Signup attempt
                success, message = add_signup(db, selected_game['id'], nickname, password)
                if success:
                    st.success(message)
                    log_security_event("successful_signup", f"nickname: {nickname}")
                    st.rerun()
                else:
                    st.error(message)
                    log_security_event("failed_signup", f"nickname: {nickname}, error: {message[:50]}...")
    
    with col2:
        st.subheader("Wypisz się")
        
        # Check rate limiting (separate limit for signouts)
        if not RateLimiter.check_signup_rate_limit("signout_attempts", 5, 5):
            cooldown = RateLimiter.get_remaining_cooldown("signout_attempts", 5)
            st.error(f"⏰ Za dużo prób wypisu. Spróbuj ponownie za {cooldown} sekund.")
            log_security_event("rate_limit", f"signout attempts exceeded")
            return
        
        with st.form("signout_form"):
            nickname_out = st.text_input("Nickname:", key="signout_nick")
            password_out = st.text_input("Hasło:", type="password", key="signout_pass")
            submit_out = st.form_submit_button("Wypisz się")
            
            if submit_out:
                # Sanitization
                nickname_out = sanitize_input(nickname_out)
                password_out = sanitize_input(password_out)
                
                # Basic validation
                if not nickname_out or not password_out:
                    st.error("❌ Podaj nickname i hasło")
                    return
                
                # Signout attempt
                success, message = remove_signup(db, selected_game['id'], nickname_out, password_out)
                if success:
                    st.success(message)
                    log_security_event("successful_signout", f"nickname: {nickname_out}")
                    st.rerun()
                else:
                    st.error(message)
                    log_security_event("failed_signout", f"nickname: {nickname_out}, error: {message[:50]}...")
