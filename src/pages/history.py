"""
History page: archive of past games.
"""

import streamlit as st

from src.config import init_database
from src.ui import components as ui
from src.utils.datetime_utils import format_game_date, parse_game_time
from src.utils.game_utils import get_past_games
from src.utils.signup_utils import get_signups_for_game
from src.utils.teams_db import get_teams_for_game


def history_page():
    db = init_database()
    if not db:
        return

    ui.page_header("Historia", "Archiwum rozegranych gierek.")

    past_games = get_past_games(db)
    if not past_games:
        ui.empty_state(
            "Brak gierek w historii",
            "Pierwsza rozegrana gierka pojawi się tutaj automatycznie.",
        )
        return

    labels = [format_game_date(parse_game_time(g["start_time"])) for g in past_games]
    idx = st.selectbox("Gierka", range(len(past_games)), format_func=lambda i: labels[i])
    game = past_games[idx]

    signups = get_signups_for_game(db, game["id"])
    teams = get_teams_for_game(db, game["id"])

    ui.stat_chips([
        (len(signups), "zapisanych"),
        (len(teams) if teams else "—", "drużyny"),
    ])

    if teams:
        ui.section("Składy")
        ui.team_cards({t["team_color"]: t["players"] for t in teams})

    ui.section("Lista zapisanych")
    ui.players_table(signups)
