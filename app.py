import streamlit as st
from src.config import setup_page_config, init_database
from src.utils.datetime_utils import get_next_game_time
from src.pages.signup import signup_page
from src.pages.list_players import list_page
from src.pages.draw_teams import draw_page
from src.pages.history import history_page
# from src.pages.payments import payments_page


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_next_game_time():
    """Cache next game time to avoid recalculation"""
    return get_next_game_time()


def main():
    """Main application function"""
    # Page configuration
    setup_page_config()
    
    st.title("⚽ Parkowa - Cotygodniowe Gierki")
    
    # Next game information in header (cached)
    next_game_time = get_cached_next_game_time()
    st.info(f"📅 **Najbliższa gierka:** {next_game_time.strftime('%d.%m.%Y %H:%M')}")
    
    st.markdown("---")
    
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'signup'
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Zapisy", 
                    key="nav_signup",
                    use_container_width=True):
            st.session_state.current_page = 'signup'
    
    with col2:
        if st.button("📋 Lista", 
                    key="nav_list",
                    use_container_width=True):
            st.session_state.current_page = 'list'
    
    with col3:
        if st.button("🎲 Losowanie", 
                    key="nav_draw",
                    use_container_width=True):
            st.session_state.current_page = 'draw'
    
    with col4:
        if st.button("📚 Historia", 
                    key="nav_history",
                    use_container_width=True):
            st.session_state.current_page = 'history'
    
    # with col5:
    #     if st.button("💰 Rozliczenia", 
    #                 key="nav_payments",
    #                 use_container_width=True):
    #         st.session_state.current_page = 'payments'
    
    st.markdown("---")
    
    # Initialize Database (cached)
    db = init_database()
    if not db:
        st.error("Nie można połączyć się z bazą danych!")
        return

    # Display selected page
    if st.session_state.current_page == 'signup':
        signup_page(db)
    elif st.session_state.current_page == 'list':
        list_page(db)
    elif st.session_state.current_page == 'draw':
        draw_page(db)
    elif st.session_state.current_page == 'history':
        history_page(db)
    # elif st.session_state.current_page == 'payments':
    #     payments_page(db)


if __name__ == "__main__":
    main()
