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
    
    # Next game information in header
    next_game_time = get_next_game_time()
    st.info(f"📅 **Najbliższa gierka:** {next_game_time.strftime('%d.%m.%Y %H:%M')}")
    
    st.markdown("---")
    
    # Initialize Database
    db = init_database()
    if not db:
        st.error("Nie można połączyć się z bazą danych!")
        return

    # Navigation with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Zapisy", "📋 Lista", "🎲 Losowanie", "📚 Historia"])
    
    with tab1:
        signup_page(db)
    
    with tab2:
        list_page(db)
    
    with tab3:
        draw_page(db)
    
    with tab4:
        history_page(db)


if __name__ == "__main__":
    main()
