"""
Payments management page for treasurer
"""

import streamlit as st
import pandas as pd
from src.database import NeonDB
from src.constants import TIMEZONE
from src.game_config import TREASURER_PASSWORD, BLIK_NUMBER
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


def batch_update_payments(db: NeonDB, game_id: str, payment_updates: dict):
    """Update payment status for multiple players in a single transaction"""
    try:
        query = """
            UPDATE signups 
            SET paid = %s 
            WHERE game_id = %s AND nickname = %s
        """
        
        # Prepare all updates
        updates = []
        for nickname, paid in payment_updates.items():
            updates.append((paid, game_id, nickname))
        
        # Execute all updates using NeonDB's execute_many method
        affected_rows = db.execute_many(query, updates)
        
        if affected_rows > 0:
            return True
        else:
            st.warning("Nie zaktualizowano żadnych rekordów")
            return False
        
    except Exception as e:
        st.error(f"Błąd aktualizacji płatności: {e}")
        return False


def get_past_inactive_games(db: NeonDB):
    """Get inactive games that already ended (start_time < now)"""
    try:
        query = """
            SELECT id, start_time
            FROM games 
            WHERE active = FALSE 
            AND start_time < CURRENT_TIMESTAMP
            ORDER BY start_time DESC
        """
        result = db.execute_query(query)
        return result if result else []
    except Exception as e:
        st.error(f"Błąd pobierania zakończonych gierek: {e}")
        return []


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
            ORDER BY unpaid_games DESC
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
    
    # Past games management - MOVED UP
    st.subheader("🕒 Zarządzanie płatnościami")
    
    past_games = get_past_inactive_games(db)
    
    if not past_games:
        st.info("Brak zakończonych gierek do zarządzania płatnościami.")
        return
    
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
        
        if signups:
            st.subheader(f"💳 Płatności dla gierki {selected_display}")
            
            # Create form to prevent UI reloading on checkbox changes
            with st.form(key=f"payments_form_{selected_game_id}"):
                # Get current payment status
                payment_status = get_payment_status_for_game(db, selected_game_id)
                
                # Simple list with checkboxes
                st.write("**Zaznacz graczy, którzy zapłacili:**")
                
                payment_updates = {}
                for signup in signups:
                    nickname = signup['nickname']
                    current_paid = payment_status.get(nickname, False)
                    
                    new_paid = st.checkbox(
                        f"{nickname}",
                        value=current_paid,
                        key=f"payment_{nickname}"
                    )
                    
                    # Track changes
                    if new_paid != current_paid:
                        payment_updates[nickname] = new_paid
                
                # Submit button
                submitted = st.form_submit_button("💾 Zapisz zmiany", type="primary", use_container_width=True)
                
                if submitted:
                    if payment_updates:
                        with st.spinner("Zapisywanie zmian..."):
                            if batch_update_payments(db, selected_game_id, payment_updates):
                                st.success(f"✅ Zaktualizowano płatności dla {len(payment_updates)} graczy")
                                st.rerun()
                            else:
                                st.error("❌ Błąd podczas aktualizacji płatności")
                    else:
                        st.info("Brak zmian do zapisania")
        else:
            st.info("Brak zapisów dla wybranej gierki.")
    
    st.markdown("---")
    
    # Debtors summary - MOVED TO BOTTOM
    st.subheader("📊 Podgląd dłużników")
    
    if st.button("🔍 Pokaż dłużników", key="show_debtors"):
        with st.spinner("Ładowanie danych o dłużnikach..."):
            debtors = get_debtors_summary(db)
            
            if debtors:
                df_debtors = pd.DataFrame(debtors)
                st.dataframe(df_debtors, use_container_width=True, hide_index=True)
            else:
                st.success("🎉 Wszyscy gracze mają uregulowane płatności!")
