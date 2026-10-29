"""
Parkowa - weekly football games. Application entry point.
"""

import streamlit as st

from src.config import setup_page_config
from src.ui.styles import inject_styles
from src.pages.signup import signup_page
from src.pages.teams import teams_page
from src.pages.history import history_page
from src.pages.stats import stats_page
from src.pages.cards import cards_page
from src.utils.auth import claim_card_login


def main():
    setup_page_config()
    inject_styles()

    cards = st.Page(cards_page, title="Karty", icon=":material/style:", url_path="cards")
    navigation = st.navigation(
        [
            # The default page is always served at the root URL.
            st.Page(signup_page, title="Zapisy", icon=":material/how_to_reg:", default=True),
            st.Page(teams_page, title="Składy", icon=":material/diversity_3:", url_path="teams"),
            cards,
            st.Page(history_page, title="Historia", icon=":material/history:", url_path="history"),
            st.Page(stats_page, title="Statystyki", icon=":material/leaderboard:", url_path="stats"),
        ],
        position="top",
    )
    # Google always returns to the root URL: a login started on the cards
    # page ("Pokaż moją kartę") goes straight back there.
    if claim_card_login():
        st.switch_page(cards)
    navigation.run()


if __name__ == "__main__":
    main()
