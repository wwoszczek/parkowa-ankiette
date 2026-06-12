"""
Stats page: most active players, by season.
"""

import streamlit as st

from src.config import init_database
from src.ui import components as ui
from src.utils.stats_utils import list_seasons, season_stats


def stats_page():
    db = init_database()
    if not db:
        return

    ui.page_header("Statystyki", "Najaktywniejsi gracze w sezonie")

    seasons = list_seasons(db)
    if not seasons:
        ui.empty_state(
            "Brak danych",
            "Statystyki pojawią się po pierwszej rozegranej gierce",
        )
        return

    labels = [s["label"] for s in seasons]
    idx = st.selectbox("Sezon", range(len(seasons)), format_func=lambda i: labels[i])
    season = seasons[idx]

    overview, ranking = season_stats(db, season["start"], season["end"])

    ui.stat_chips([
        (overview["games"], "gierek"),
        (overview["players"], "graczy"),
        (overview["signups"], "zapisów"),
    ])

    if not ranking:
        ui.empty_state("Brak rozegranych gierek w tym sezonie", "")
        return

    ui.section("Podium")
    ui.podium(ranking[:3])

    if len(ranking) > 3:
        ui.section("Klasyfikacja")
        ui.ranking_list(ranking[3:], start_rank=4, max_count=ranking[0]["count"])
