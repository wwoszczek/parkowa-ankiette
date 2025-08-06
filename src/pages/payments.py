"""
Payments management page for treasurer
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.database import NeonDB
from src.constants import TIMEZONE
from src.game_config import TREASURER_PASSWORD, BLIK_NUMBER
from src.utils.game_utils import get_past_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.datetime_utils import parse_game_time


def add_payment_column_if_not_exists(db: NeonDB):
    """Add paid column to signups table if it doesn't exist"""
    try:
        # Check if column exists
        result = db.execute_query("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'signups' AND column_name = 'paid'
        """)
        
        if not result:
            # Add column if it doesn't exist
            db.execute_query("ALTER TABLE signups ADD COLUMN paid BOOLEAN DEFAULT FALSE")
            st.success("Dodano kolumnę płatności do bazy danych")
    except Exception as e:
        st.error(f"Błąd przy dodawaniu kolumny płatności: {e}")


def get_payment_status_for_game(db: NeonDB, game_id: str):
    """Get payment status for all players in a game"""
    try:
        query = """
            SELECT nickname, paid
            FROM signups
            WHERE game_id = %s
            ORDER BY nickname
        """
        result = db.execute_query(query, (game_id,))
        return {row['nickname']: row['paid'] for row in result} if result else {}
    except Exception as e:
        st.error(f"Błąd pobierania statusu płatności: {e}")
        return {}


def update_payment_status(db: NeonDB, game_id: str, nickname: str, paid: bool):
    """Update payment status for a player"""
    try:
        query = """
            UPDATE signups 
            SET paid = %s 
            WHERE game_id = %s AND nickname = %s
        """
        db.execute_query(query, (paid, game_id, nickname))
        return True
    except Exception as e:
        st.error(f"Błąd aktualizacji statusu płatności: {e}")
        return False


def get_debtors_summary(db: NeonDB):
    """Get summary of players who haven't paid for past games"""
    try:
        query = """
            SELECT s.nickname, COUNT(*) as unpaid_games
            FROM signups s
            JOIN games g ON s.game_id = g.id
            WHERE s.paid = FALSE 
            AND g.start_time < CURRENT_TIMESTAMP
            AND g.active = FALSE
            GROUP BY s.nickname
            ORDER BY unpaid_games DESC, s.nickname
        """
        result = db.execute_query(query)
        return result if result else []
    except Exception as e:
        st.error(f"Błąd pobierania podsumowania dłużników: {e}")
        return []


def payments_page(db: NeonDB):
    """Main payments management page"""
    st.header("💰 Rozliczenia")
    
    # Payment info for everyone
    st.info(f"📱 **Numer do przelewów BLIK:** {BLIK_NUMBER}")
    st.markdown("---")
    
    # Password protection
    if 'treasurer_authenticated' not in st.session_state:
        st.session_state.treasurer_authenticated = False
    
    if not st.session_state.treasurer_authenticated:
        st.subheader("🔐 Logowanie skarbnika")
        password = st.text_input("Wprowadź hasło skarbnika:", type="password")
        
        if st.button("Zaloguj"):
            if password == TREASURER_PASSWORD:
                st.session_state.treasurer_authenticated = True
                st.success("Zalogowano pomyślnie!")
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło!")
        return
    
    # Logout button
    if st.button("🚪 Wyloguj", key="logout"):
        st.session_state.treasurer_authenticated = False
        st.rerun()
    
    # Add payment column if needed
    add_payment_column_if_not_exists(db)
    
    # Debtors summary
    st.subheader("📊 Szybki podgląd dłużników")
    debtors = get_debtors_summary(db)
    
    if debtors:
        df_debtors = pd.DataFrame(debtors, columns=["Gracz", "Niezapłacone gierki"])
        st.dataframe(df_debtors, use_container_width=True, hide_index=True)
    else:
        st.success("🎉 Wszyscy gracze mają uregulowane płatności!")
    
    st.markdown("---")
    
    # Past games management
    st.subheader("🕒 Zarządzanie płatnościami w historycznych gierkach")
    
    past_games = get_past_games(db)
    
    if not past_games:
        st.info("Brak zakończonych gierek do zarządzania płatnościami.")
        return
    
    # Limit to last 10 games for performance
    past_games = past_games[:10]
    
    # Game selection
    game_options = {}
    for game in past_games:
        game_time = parse_game_time(game['start_time'])
        game_time_local = game_time.astimezone(TIMEZONE)
        display_time = game_time_local.strftime('%d.%m.%Y %H:%M')
        game_options[display_time] = game['id']
    
    selected_display = st.selectbox(
        "Wybierz gierkę:",
        options=list(game_options.keys())
    )
    
    if selected_display:
        selected_game_id = game_options[selected_display]
        
        # Get signups for selected game
        signups = get_signups_for_game(db, selected_game_id)
        payment_status = get_payment_status_for_game(db, selected_game_id)
        
        if signups:
            st.subheader(f"💳 Płatności dla gierki {selected_display}")
            
            # Display payment checkboxes
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write("**Gracz**")
            with col2:
                st.write("**Zapłacił**")
            
            for signup in signups:
                nickname = signup['nickname']  # Access nickname using dictionary key
                current_paid = payment_status.get(nickname, False)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(nickname)
                
                with col2:
                    new_paid = st.checkbox(
                        "",
                        value=current_paid,
                        key=f"paid_{selected_game_id}_{nickname}"
                    )
                    
                    # Update if changed
                    if new_paid != current_paid:
                        if update_payment_status(db, selected_game_id, nickname, new_paid):
                            st.success(f"Zaktualizowano status płatności dla {nickname}")
                            payment_status[nickname] = new_paid
                            st.rerun()
        else:
            st.info("Brak zapisów dla wybranej gierki.")
