"""
Signups page: join the upcoming game and see who is playing.
"""

import streamlit as st

from src.config import init_database
from src.game_config import MAX_GUESTS_PER_USER, SIGNUP_OPENING_MESSAGE
from src.ui import components as ui
from src.utils.auth import (
    auth_ready,
    claim_fresh_login,
    get_current_user,
    is_admin,
    is_dev_user,
    logout_control,
    start_action_login,
)
from src.utils.datetime_utils import format_game_date, get_next_game_time, parse_game_time
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import (
    account_display_name,
    add_account_signup,
    add_guest_signup,
    get_account_signup,
    get_guests_added_by,
    get_signups_for_game,
    remove_signup,
    resolve_adder_names,
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


def _perform(db, game, user, action):
    """Run the requested account action, returning (ok, message)."""
    if action == "signup":
        return add_account_signup(db, game["id"], user["email"], user["name"])
    # action == "signout"
    entry = get_account_signup(db, game["id"], user["email"])
    if not entry:
        return False, f"Nie jesteś obecnie zapisany na tę gierkę (konto: {user['email']})"
    return remove_signup(db, entry["id"], user["email"])


def _act(db, game, user, action):
    """Every real click goes through the Google account chooser, so the player
    picks WHICH account performs the action (switching accounts just works).
    Only the dev_user fake acts directly - it has no OAuth flow."""
    if is_dev_user():
        _finish(*_perform(db, game, user, action))
        return
    start_action_login(action)


def _complete_oauth_action(db, game, user):
    """Finish the action that triggered the account chooser. The provider name
    stored in the identity cookie ("google" = signup, "wypis" = signout)
    carries the intent across the redirect; claim_fresh_login() returns it
    exactly once and only for a seconds-old login, so a days-old cookie or a
    page reload never replays an action."""
    action = claim_fresh_login()
    if action:
        _finish(*_perform(db, game, user, action))


def _signup_panel(db, game, user):
    """Just two always-visible buttons - the Google session stays invisible.
    Each action gives explicit feedback (already signed up / not signed up)."""
    if not is_dev_user() and not auth_ready():
        st.info(
            "Zapisy wymagają logowania Google, które nie jest jeszcze w pełni "
            "skonfigurowane (sekcje [auth.google] i [auth.wypis] w secrets — patrz README)"
        )
        return

    if st.button("Zapisz się kontem Google", key="gbtn_signup", width="stretch"):
        _act(db, game, user, "signup")
    if st.button("Wypisz się kontem Google", key="gbtn_signout", width="stretch"):
        _act(db, game, user, "signout")


def _guests_panel(db, game, user):
    ui.section("Twoi goście")
    # Same name the list uses for this account (dedup-aware), so the "gość · X"
    # badge and this note always agree - even when not currently signed up.
    adder = account_display_name(db, game["id"], user["email"], user["name"])
    st.caption(f"Goście zostaną przypisani do konta **{adder}** ({user['email']})")
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
                   f"Limit: {MAX_GUESTS_PER_USER} na osobę")
    else:
        st.caption(f"Wykorzystany limit gości ({MAX_GUESTS_PER_USER})")


def _admin_panel(db, game, signups, user):
    with st.expander("Zarządzanie listą (admin)"):
        if not signups:
            st.caption("Lista jest pusta")
        for entry in signups:
            label = entry["nickname"] + (" · gość" if entry.get("is_guest") else "")
            name_col, btn_col = st.columns([4, 1])
            name_col.markdown(label)
            if btn_col.button("Usuń", key=f"remove_admin_{entry['id']}", width="stretch"):
                ok, msg = remove_signup(db, entry["id"], user["email"], admin=True)
                _finish(ok, msg)
        # The session is invisible elsewhere by design; admins get the escape hatch.
        logout_control()


def signup_page():
    db = init_database()
    if not db:
        return

    ui.brand_header("Dołącz do najbliższej gierki i zobacz, kto gra")

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
        adder_names = resolve_adder_names(db, signups)
        if user:
            # The current viewer's own guests use the same dedup-aware name as
            # the guests panel, even if the viewer is not signed up.
            adder_names[user["email"].lower()] = account_display_name(
                db, game["id"], user["email"], user["name"]
            )
        ui.players_table(signups, current_email=email, adder_names=adder_names)

    with panel_col:
        ui.section("Twój zapis")
        if user:
            _complete_oauth_action(db, game, user)
        _show_flash()
        _signup_panel(db, game, user)
        if user:
            _guests_panel(db, game, user)

    if user and is_admin(user):
        _admin_panel(db, game, signups, user)
