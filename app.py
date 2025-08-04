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
    
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'signup'
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Zapisy", use_container_width=True, 
                    type="primary" if st.session_state.current_page == 'signup' else "secondary"):
            st.session_state.current_page = 'signup'
    
    with col2:
        if st.button("📋 Lista", use_container_width=True,
                    type="primary" if st.session_state.current_page == 'list' else "secondary"):
            st.session_state.current_page = 'list'
    
    with col3:
        if st.button("🎲 Losowanie", use_container_width=True,
                    type="primary" if st.session_state.current_page == 'draw' else "secondary"):
            st.session_state.current_page = 'draw'
    
    with col4:
        if st.button("📚 Historia", use_container_width=True,
                    type="primary" if st.session_state.current_page == 'history' else "secondary"):
            st.session_state.current_page = 'history'
    
    st.markdown("---")
    
    # Initialize Database
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
