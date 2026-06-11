"""
Parkowa - weekly football games. Application entry point.
"""

import streamlit as st

from src.config import setup_page_config
from src.ui.styles import inject_styles
from src.pages.signup import signup_page
from src.pages.teams import teams_page
from src.pages.history import history_page


def main():
    setup_page_config()
    inject_styles()

    navigation = st.navigation(
        [
            # The default page is always served at the root URL.
            st.Page(signup_page, title="Zapisy", icon=":material/how_to_reg:", default=True),
            st.Page(teams_page, title="Składy", icon=":material/diversity_3:", url_path="sklady"),
            st.Page(history_page, title="Historia", icon=":material/history:", url_path="historia"),
        ],
        position="top",
    )
    navigation.run()


if __name__ == "__main__":
    main()
