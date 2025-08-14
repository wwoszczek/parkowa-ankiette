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
        
        # Execute all updates
        with db.connection.cursor() as cur:
            cur.executemany(query, updates)
            db.connection.commit()
        
        return True
    except Exception as e:
        st.error(f"Błąd aktualizacji płatności: {e}")
        db.connection.rollback()
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
    
    # Add payment column if needed
    # add_payment_column_if_not_exists(db)
    
    # Debtors summary - on demand
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📊 Podgląd dłużników")
    with col2:
        if st.button("🔍 Podgląd dłużników", key="show_debtors"):
            with st.spinner("Ładowanie danych o dłużnikach..."):
                debtors = get_debtors_summary(db)
                
                if debtors:
                    df_debtors = pd.DataFrame(debtors)
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
            
            payment_changes = {}
            
            for signup in signups:
                nickname = signup['nickname']
                current_paid = payment_status.get(nickname, False)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(nickname)
                
                with col2:
                    new_paid = st.checkbox(
                        f"Płatność dla {nickname}" if nickname else "Płatność",
                        value=current_paid,
                        key=f"paid_{selected_game_id}_{nickname}",
                        label_visibility="hidden"
                    )
                    
                    # Track changes
                    if new_paid != current_paid:
                        payment_changes[nickname] = new_paid
            
            # Update button
            if payment_changes:
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("💾 Aktualizuj płatności", type="primary", use_container_width=True):
                        with st.spinner("Zapisywanie zmian..."):
                            if batch_update_payments(db, selected_game_id, payment_changes):
                                st.success(f"✅ Zaktualizowano płatności dla {len(payment_changes)} graczy")
                                st.rerun()
                            else:
                                st.error("❌ Błąd podczas aktualizacji płatności")
                
                # Show pending changes
                st.info(f"📝 Oczekuje {len(payment_changes)} zmian do zapisania")
        else:
            st.info("Brak zapisów dla wybranej gierki.")
