import streamlit as st
from src.config import setup_page_config, init_supabase
from src.utils.datetime_utils import get_next_game_time
from src.pages.signup import signup_page
from src.pages.list_players import list_page
from src.pages.draw_teams import draw_page
from src.pages.history import history_page


def main():
    """Główna funkcja aplikacji"""
    # Konfiguracja strony
    setup_page_config()
    
    st.title("⚽ Parkowa Ankieta - Cotygodniowe Gierki")
    st.markdown("---")
    
    # Inicjalizacja Supabase
    supabase = init_supabase()
    if not supabase:
        st.error("Nie można połączyć się z bazą danych!")
        return
    
    # Sidebar nawigacji
    st.sidebar.title("Nawigacja")
    page = st.sidebar.radio(
        "Wybierz stronę:",
        ["Zapisy", "Lista", "Losowanie", "Historia"]
    )
    
    # Informacja o najbliższej gierce
    next_game_time = get_next_game_time()
    st.sidebar.markdown("### 📅 Najbliższa gierka:")
    st.sidebar.info(f"{next_game_time.strftime('%d.%m.%Y %H:%M')}")
    
    # Routing stron
    if page == "Zapisy":
        signup_page(supabase)
    elif page == "Lista":
        list_page(supabase)
    elif page == "Losowanie":
        draw_page(supabase)
    elif page == "Historia":
        history_page(supabase)


if __name__ == "__main__":
    main()
