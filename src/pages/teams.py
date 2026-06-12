"""
Teams page: drawn lineups for the upcoming game.
"""

import streamlit as st

from src.config import init_database
from src.game_config import (
    ALLOWED_PLAYER_COUNTS,
    DRAW_OPENING_MESSAGE,
    MANUAL_DRAW_MESSAGE,
    SIGNUP_OPENING_MESSAGE,
)
from src.ui import components as ui
from src.utils.auth import get_current_user, is_admin
from src.utils.datetime_utils import format_game_date, is_draw_time_allowed, parse_game_time
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.team_utils import draw_teams, is_valid_player_count
from src.utils.teams_db import get_teams_for_game, save_teams


def _draw_controls(db, game, signups, teams_exist, user, admin):
    n = len(signups)
    st.caption(f"Na liście: {ui.pl_players(n)}")

    if not user:
        st.caption("Zaloguj się na stronie Zapisy, aby móc wylosować składy")
        return
    if not (is_draw_time_allowed() or admin):
        st.caption(DRAW_OPENING_MESSAGE)
        return
    if not is_valid_player_count(n):
        counts = ", ".join(str(c) for c in ALLOWED_PLAYER_COUNTS)
        st.warning(
            f"{MANUAL_DRAW_MESSAGE}\n\n"
            f"Automatyczne losowanie działa dla {counts} graczy"
        )
        return

    label = "Losuj ponownie" if teams_exist else "Wylosuj składy"
    if st.button(label, key=f"draw_{game['id']}", type="primary"):
        players = [s["nickname"] for s in signups]
        teams = draw_teams(players, n)
        if teams and save_teams(db, game["id"], teams):
            st.rerun()


def teams_page():
    db = init_database()
    if not db:
        return

    ui.page_header("Składy", "Wylosowane drużyny na najbliższą gierkę")

    games = get_active_games(db)
    if not games:
        ui.empty_state("Brak aktywnej gierki", SIGNUP_OPENING_MESSAGE)
        return

    user = get_current_user()
    admin = is_admin(user)

    for game in games:
        game_dt = parse_game_time(game["start_time"])
        ui.section(format_game_date(game_dt))

        signups = get_signups_for_game(db, game["id"])
        teams = get_teams_for_game(db, game["id"])

        if teams:
            ui.team_cards({t["team_color"]: t["players"] for t in teams})
        else:
            ui.empty_state("Składów jeszcze nie ma", DRAW_OPENING_MESSAGE)

        _draw_controls(db, game, signups, bool(teams), user, admin)
