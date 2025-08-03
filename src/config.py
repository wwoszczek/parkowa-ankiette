"""
Application configuration and Supabase initialization
"""

import streamlit as st
import pytz
from supabase import create_client, Client

# Timezone configuration
TIMEZONE = pytz.timezone('Europe/Warsaw')

@st.cache_resource
def init_supabase() -> Client:
    """Initialize Supabase client"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
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
