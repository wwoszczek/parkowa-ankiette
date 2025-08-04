"""
Application configuration and Neon PostgreSQL initialization
"""

import streamlit as st
import pytz
from src.database import get_db

# Timezone configuration
TIMEZONE = pytz.timezone('Europe/Warsaw')

@st.cache_resource
def init_database():
    """Initialize Neon database connection"""
    try:
        db = get_db()
        # Test connection
        db.execute_query("SELECT 1")
        return db
    except Exception as e:
        st.error(f"Błąd połączenia z bazą danych: {e}")
        return None

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Parkowa Ankieta - Gierki Piłkarskie",
        page_icon="⚽",
        layout="wide"
    )
