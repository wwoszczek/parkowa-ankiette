"""
Rate limiting and additional security measures
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from src.config import TIMEZONE


class RateLimiter:
    """Simple rate limiter using session state"""
    
    @staticmethod
    def check_signup_rate_limit(key: str = "signup_attempts", max_attempts: int = 3, window_minutes: int = 5) -> bool:
        """
        Check if user hasn't exceeded signup limit
        
        Args:
            key: key in session_state
            max_attempts: maximum number of attempts
            window_minutes: time window in minutes
            
        Returns:
            True if can continue, False if limit exceeded
        """
        now = datetime.now()
        
        if key not in st.session_state:
            st.session_state[key] = []
        
        # Remove old attempts (before window_minutes)
        cutoff = now - timedelta(minutes=window_minutes)
        st.session_state[key] = [
            attempt for attempt in st.session_state[key] 
            if attempt > cutoff
        ]
        
        # Check if can add new attempt
        if len(st.session_state[key]) >= max_attempts:
            return False
        
        # Add new attempt
        st.session_state[key].append(now)
        return True
    
    @staticmethod
    def get_remaining_cooldown(key: str = "signup_attempts", window_minutes: int = 5) -> int:
        """Return remaining cooldown time in seconds"""
        if key not in st.session_state or not st.session_state[key]:
            return 0
        
        oldest_attempt = min(st.session_state[key])
        cooldown_end = oldest_attempt + timedelta(minutes=window_minutes)
        now = datetime.now()
        
        if cooldown_end > now:
            return int((cooldown_end - now).total_seconds())
        return 0


def validate_nickname(nickname: str) -> tuple[bool, str]:
    """
    Validate nickname
    
    Returns:
        (is_valid, error_message)
    """
    if not nickname:
        return False, "Nickname nie może być pusty"
    
    if len(nickname) < 2:
        return False, "Nickname musi mieć co najmniej 2 znaki"
    
    if len(nickname) > 20:
        return False, "Nickname nie może być dłuższy niż 20 znaków"
    
    # Allowed characters: letters, digits, spaces, hyphens, underscores
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
    if not all(char in allowed_chars for char in nickname):
        return False, "Nickname zawiera niedozwolone znaki"
    
    # Forbidden words (can be extended)
    forbidden_words = ['admin', 'test', 'null', 'undefined', 'system']
    if nickname.lower() in forbidden_words:
        return False, "Ten nickname jest zarezerwowany"
    
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password
    
    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "Hasło nie może być puste"
    
    if len(password) < 3:
        return False, "Hasło musi mieć co najmniej 3 znaki"
    
    if len(password) > 50:
        return False, "Hasło nie może być dłuższe niż 50 znaków"
    
    return True, ""


def sanitize_input(text: str) -> str:
    """
    Sanitize user input
    
    Args:
        text: text to clean
        
    Returns:
        cleaned text
    """
    if not text:
        return ""
    
    # Remove whitespace from beginning and end
    text = text.strip()
    
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    return text


# Additional helper functions for security

def log_security_event(event_type: str, details: str):
    """
    Log security-related events
    
    Args:
        event_type: event type (rate_limit, invalid_input, etc.)
        details: event details
    """
    timestamp = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    
    # In production app, it's worth logging to external service
    print(f"[SECURITY] {timestamp} - {event_type}: {details}")
    
    # Optionally add to session_state for debugging
    if 'security_log' not in st.session_state:
        st.session_state['security_log'] = []
    
    st.session_state['security_log'].append({
        'timestamp': timestamp,
        'type': event_type,
        'details': details
    })
    
    # Limit log size
    if len(st.session_state['security_log']) > 50:
        st.session_state['security_log'] = st.session_state['security_log'][-50:]
