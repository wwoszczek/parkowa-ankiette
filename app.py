import streamlit as st
from src.config import setup_page_config, init_database
from src.utils.datetime_utils import get_next_game_time
from src.pages.signup import signup_page
from src.pages.list_players import list_page
from src.pages.draw_teams import draw_page
from src.pages.history import history_page


def main():
    """Main application function"""
    # Page configuration
    setup_page_config()
    
    st.title("⚽ Parkowa Ankieta - Cotygodniowe Gierki")
    st.markdown("---")
    
    # Initialize Database
    db = init_database()
    if not db:
        st.error("Nie można połączyć się z bazą danych!")
        return

    # Navigation sidebar
    st.sidebar.title("Nawigacja")
    page = st.sidebar.radio(
        "Wybierz stronę:",
        ["Zapisy", "Lista", "Losowanie", "Historia"]
    )
    
    # Next game information
    next_game_time = get_next_game_time()
    st.sidebar.markdown("### 📅 Najbliższa gierka:")
    st.sidebar.info(f"{next_game_time.strftime('%d.%m.%Y %H:%M')}")
    
    st.sidebar.markdown("### 🤖 Automatyka:")
    st.sidebar.success("GitHub Actions\n(3x dziennie)")
    
    # Page routing
    if page == "Zapisy":
        signup_page(db)
    elif page == "Lista":
        list_page(db)
    elif page == "Losowanie":
        draw_page(db)
    elif page == "Historia":
        history_page(db)


if __name__ == "__main__":
    main()
