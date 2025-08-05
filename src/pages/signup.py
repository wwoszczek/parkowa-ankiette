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


@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_game_options_cached(active_games):
    """Cache game options to avoid repeated processing"""
    game_options = []
    game_mapping = {}
    for game in active_games:
        game_time = parse_game_time(game['start_time'])
        display_name = game_time.strftime('%d.%m.%Y %H:%M')
        game_options.append(display_name)
        game_mapping[display_name] = game
    return game_options, game_mapping


def clear_signup_cache():
    """Clear signup-related cache to ensure fresh data"""
    get_game_options_cached.clear()
    # Also clear game cache from utils
    try:
        from src.utils.game_utils import get_active_games
        get_active_games.clear()
    except:
        pass


def signup_page(db: NeonDB):
    """Signup page"""
    st.header("⚽ Zapisy na gierkę")
    
    # Get active games
    active_games = get_active_games(db)
    
    if not active_games:
        st.warning(f"Brak aktywnych gierek. {SIGNUP_OPENING_MESSAGE}")
        return

    # Game selection (cached)
    game_options, game_mapping = get_game_options_cached(tuple(active_games))  # Convert to tuple for hashing
    
    selected_game_str = st.selectbox("Wybierz gierkę:", game_options)
    if not selected_game_str:
        return
    
    selected_game = game_mapping[selected_game_str]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Zapisz się")
        
        # Check rate limiting
        if not RateLimiter.check_signup_rate_limit("signup_attempts", 150, 250):
            cooldown = RateLimiter.get_remaining_cooldown("signup_attempts", 250)
            st.error(f"⏰ Za dużo prób zapisu. Spróbuj ponownie za {cooldown} sekund.")
            log_security_event("rate_limit", f"signup attempts exceeded")
            st.stop()  # Use st.stop() instead of return to prevent further processing
        
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
                    st.stop()
                
                # Password validation
                password_valid, password_error = validate_password(password)
                if not password_valid:
                    st.error(f"❌ Błąd hasła: {password_error}")
                    log_security_event("invalid_password", "password validation failed")
                    st.stop()
                
                # Signup attempt
                with st.spinner("Zapisuję..."):
                    success, message = add_signup(db, selected_game['id'], nickname, password)
                    
                if success:
                    st.success(f"✅ {message}")
                    log_security_event("successful_signup", f"nickname: {nickname}")
                    # Clear cache to ensure fresh data
                    clear_signup_cache()
                else:
                    st.error(f"❌ {message}")
                    log_security_event("failed_signup", f"nickname: {nickname}, error: {message[:50]}...")
    
    with col2:
        st.subheader("Wypisz się")
        
        # Check rate limiting (separate limit for signouts)
        if not RateLimiter.check_signup_rate_limit("signout_attempts", 250, 250):
            cooldown = RateLimiter.get_remaining_cooldown("signout_attempts", 250)
            st.error(f"⏰ Za dużo prób wypisu. Spróbuj ponownie za {cooldown} sekund.")
            log_security_event("rate_limit", f"signout attempts exceeded")
            st.stop()  # Use st.stop() instead of return to prevent further processing
        
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
                    st.stop()
                
                # Signout attempt
                with st.spinner("Wypisuję..."):
                    success, message = remove_signup(db, selected_game['id'], nickname_out, password_out)
                    
                if success:
                    st.success(f"✅ {message}")
                    log_security_event("successful_signout", f"nickname: {nickname_out}")
                    # Clear cache to ensure fresh data
                    clear_signup_cache()
                else:
                    st.error(f"❌ {message}")
                    log_security_event("failed_signout", f"nickname: {nickname_out}, error: {message[:50]}...")
