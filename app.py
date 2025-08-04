import streamlit as st
from src.config import setup_page_config, init_database
from src.utils.datetime_utils import get_next_game_time
from src.pages.signup import signup_page
from src.pages.list_players import list_page
from src.pages.draw_teams import draw_page
from src.pages.history import history_page


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_next_game_time():
    """Cache next game time to avoid recalculation"""
    return get_next_game_time()


def main():
    """Main application function"""
    # Page configuration
    setup_page_config()
    
    st.title("⚽ Parkowa Ankieta - Cotygodniowe Gierki")
    
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
        signup_active = st.session_state.current_page == 'signup'
        if st.button("📝 Zapisy", 
                    key="nav_signup",
                    use_container_width=True, 
                    type="primary" if signup_active else "secondary"):
            st.session_state.current_page = 'signup'
    
    with col2:
        list_active = st.session_state.current_page == 'list'
        if st.button("📋 Lista", 
                    key="nav_list",
                    use_container_width=True,
                    type="primary" if list_active else "secondary"):
            st.session_state.current_page = 'list'
    
    with col3:
        draw_active = st.session_state.current_page == 'draw'
        if st.button("🎲 Losowanie", 
                    key="nav_draw",
                    use_container_width=True,
                    type="primary" if draw_active else "secondary"):
            st.session_state.current_page = 'draw'
    
    with col4:
        history_active = st.session_state.current_page == 'history'
        if st.button("📚 Historia", 
                    key="nav_history",
                    use_container_width=True,
                    type="primary" if history_active else "secondary"):
            st.session_state.current_page = 'history'
    
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


if __name__ == "__main__":
    main()
