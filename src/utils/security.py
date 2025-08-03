"""
Rate limiting i dodatkowe zabezpieczenia
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from supabase import Client
from src.config import TIMEZONE


class RateLimiter:
    """Prosty rate limiter używający session state"""
    
    @staticmethod
    def check_signup_rate_limit(key: str = "signup_attempts", max_attempts: int = 3, window_minutes: int = 5) -> bool:
        """
        Sprawdza czy użytkownik nie przekroczył limitu zapisów
        
        Args:
            key: klucz w session_state
            max_attempts: max liczba prób
            window_minutes: okno czasowe w minutach
            
        Returns:
            True jeśli może kontynuować, False jeśli limit przekroczony
        """
        now = datetime.now()
        
        if key not in st.session_state:
            st.session_state[key] = []
        
        # Usuń stare próby (sprzed window_minutes)
        cutoff = now - timedelta(minutes=window_minutes)
        st.session_state[key] = [
            attempt for attempt in st.session_state[key] 
            if attempt > cutoff
        ]
        
        # Sprawdź czy można dodać nową próbę
        if len(st.session_state[key]) >= max_attempts:
            return False
        
        # Dodaj nową próbę
        st.session_state[key].append(now)
        return True
    
    @staticmethod
    def get_remaining_cooldown(key: str = "signup_attempts", window_minutes: int = 5) -> int:
        """Zwraca pozostały czas cooldown w sekundach"""
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
    Waliduje nickname
    
    Returns:
        (is_valid, error_message)
    """
    if not nickname:
        return False, "Nickname nie może być pusty"
    
    if len(nickname) < 2:
        return False, "Nickname musi mieć co najmniej 2 znaki"
    
    if len(nickname) > 20:
        return False, "Nickname nie może być dłuższy niż 20 znaków"
    
    # Dozwolone znaki: litery, cyfry, spacje, myślniki, podkreślenia
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
    if not all(char in allowed_chars for char in nickname):
        return False, "Nickname zawiera niedozwolone znaki"
    
    # Zabronione słowa (można rozszerzyć)
    forbidden_words = ['admin', 'test', 'null', 'undefined', 'system']
    if nickname.lower() in forbidden_words:
        return False, "Ten nickname jest zarezerwowany"
    
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Waliduje hasło
    
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
    Sanityzuje wejście użytkownika
    
    Args:
        text: tekst do oczyszczenia
        
    Returns:
        oczyszczony tekst
    """
    if not text:
        return ""
    
    # Usuń białe znaki z początku i końca
    text = text.strip()
    
    # Usuń wielokrotne spacje
    text = ' '.join(text.split())
    
    return text


# Dodatkowe funkcje pomocnicze dla security

def log_security_event(event_type: str, details: str):
    """
    Loguje wydarzenia związane z bezpieczeństwem
    
    Args:
        event_type: typ wydarzenia (rate_limit, invalid_input, etc.)
        details: szczegóły wydarzenia
    """
    timestamp = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    
    # W prawdziwej aplikacji warto to logować do zewnętrznego serwisu
    print(f"[SECURITY] {timestamp} - {event_type}: {details}")
    
    # Opcjonalnie można dodać do session_state dla debugowania
    if 'security_log' not in st.session_state:
        st.session_state['security_log'] = []
    
    st.session_state['security_log'].append({
        'timestamp': timestamp,
        'type': event_type,
        'details': details
    })
    
    # Ogranicz rozmiar logu
    if len(st.session_state['security_log']) > 50:
        st.session_state['security_log'] = st.session_state['security_log'][-50:]
