"""
Signups page: join the upcoming game and see who is playing.
"""

import streamlit as st

from src.config import init_database
from src.game_config import MAX_GUESTS_PER_USER, SIGNUP_OPENING_MESSAGE
from src.ui import components as ui
from src.utils.auth import get_current_user, is_admin, login_panel, logout_control
from src.utils.datetime_utils import format_game_date, get_next_game_time, parse_game_time
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import (
    add_account_signup,
    add_guest_signup,
    get_account_signup,
    get_guests_added_by,
    get_signups_for_game,
    remove_signup,
)


def _select_game(games):
    if len(games) == 1:
        return games[0]
    labels = [format_game_date(parse_game_time(g["start_time"])) for g in games]
    idx = st.selectbox("Wybierz gierkę", range(len(games)), format_func=lambda i: labels[i])
    return games[idx]


def _finish(ok: bool, message: str):
    """Store the outcome and rerun so lists refresh immediately."""
    st.session_state["flash"] = ("ok" if ok else "err", message)
    st.rerun()


def _show_flash():
    flash = st.session_state.pop("flash", None)
    if flash:
        kind, message = flash
        (st.success if kind == "ok" else st.error)(message)


def _account_panel(db, game, user):
    ui.account_strip(user["name"])
    my_entry = get_account_signup(db, game["id"], user["email"])
    if my_entry:
        st.success(f"Jesteś na liście jako **{my_entry['nickname']}**.")
        if st.button("Wypisz się", key="remove_self", width="stretch"):
            ok, msg = remove_signup(db, my_entry["id"], user["email"])
            _finish(ok, msg)
    else:
        with st.form("signup_form"):
            default_nick = user["name"].split()[0] if user.get("name") else ""
            nickname = st.text_input("Twój nick na liście", value=default_nick, max_chars=20)
            if st.form_submit_button("Zapisz się", type="primary", width="stretch"):
                ok, msg = add_account_signup(db, game["id"], nickname, user["email"])
                _finish(ok, msg)
    logout_control()


def _guests_panel(db, game, user):
    ui.section("Twoi goście")
    guests = get_guests_added_by(db, game["id"], user["email"])

    for guest in guests:
        name_col, btn_col = st.columns([3, 2])
        name_col.markdown(f"**{guest['nickname']}**")
        if btn_col.button("Wypisz", key=f"remove_guest_{guest['id']}", width="stretch"):
            ok, msg = remove_signup(db, guest["id"], user["email"])
            _finish(ok, msg)

    remaining = MAX_GUESTS_PER_USER - len(guests)
    if remaining > 0:
        with st.form("guest_form", clear_on_submit=True):
            guest_name = st.text_input(
                "Imię/nick gościa", max_chars=20,
                placeholder="np. Maciek (kolega bez konta)",
            )
            if st.form_submit_button("Dodaj gościa", width="stretch"):
                ok, msg = add_guest_signup(db, game["id"], guest_name, user["email"])
                _finish(ok, msg)
        st.caption(f"Goście nie potrzebują konta — wypisać może ich tylko ten, kto ich dodał. "
                   f"Limit: {MAX_GUESTS_PER_USER} na osobę.")
    else:
        st.caption(f"Wykorzystany limit gości ({MAX_GUESTS_PER_USER}).")


def _admin_panel(db, game, signups, user):
    with st.expander("Zarządzanie listą (admin)"):
        if not signups:
            st.caption("Lista jest pusta.")
        for entry in signups:
            label = entry["nickname"] + (" · gość" if entry.get("is_guest") else "")
            name_col, btn_col = st.columns([4, 1])
            name_col.markdown(label)
            if btn_col.button("Usuń", key=f"remove_admin_{entry['id']}", width="stretch"):
                ok, msg = remove_signup(db, entry["id"], user["email"], admin=True)
                _finish(ok, msg)


def signup_page():
    db = init_database()
    if not db:
        return

    ui.page_header("Zapisy", "Dołącz do najbliższej gierki i zobacz, kto gra.")

    games = get_active_games(db)
    if not games:
        ui.hero(get_next_game_time(), chips=["zapisy wkrótce"])
        ui.empty_state("Zapisy są jeszcze zamknięte", SIGNUP_OPENING_MESSAGE)
        return

    game = _select_game(games)
    game_dt = parse_game_time(game["start_time"])
    signups = get_signups_for_game(db, game["id"])

    user = get_current_user()
    email = user["email"] if user else None

    ui.hero(game_dt, chips=[ui.pl_players(len(signups))])

    list_col, panel_col = st.columns([5, 4], gap="large")

    with list_col:
        ui.section("Lista graczy")
        ui.players_table(signups, current_email=email)

    with panel_col:
        ui.section("Twój zapis")
        _show_flash()
        if not user:
            login_panel()
        else:
            _account_panel(db, game, user)
            _guests_panel(db, game, user)

    if user and is_admin(user):
        _admin_panel(db, game, signups, user)
