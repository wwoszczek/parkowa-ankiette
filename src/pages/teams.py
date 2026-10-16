"""
Teams page: squads for the upcoming game, set by hand in the squad builder.

First come, first served: the account that approves a game's squads owns them.
Everyone sees them; only the owner (or an admin) can edit or delete them, and
once deleted anyone can set new ones. Signups beyond the lineup limit wait on
the reserve bench and step into freed places in signup order.
"""

import streamlit as st

from src.config import init_database
from src.game_config import DRAW_OPENING_MESSAGE, SIGNUP_OPENING_MESSAGE
from src.ui import components as ui
from src.utils.auth import get_current_user, is_admin
from src.utils.datetime_utils import format_game_date, is_draw_time_allowed, parse_game_time
from src.utils.game_utils import get_active_games
from src.utils.signup_utils import get_signups_for_game, resolve_account_names
from src.utils.team_utils import (
    MAX_PLAYERS,
    TEAM_COUNTS,
    bench_for,
    capacity,
    default_team_count,
    fill_randomly,
    lineups_with_bench,
    split_bench,
    team_colors,
    team_targets,
)
from src.utils.teams_db import (
    delete_squads,
    get_teams_for_game,
    save_squads,
    squads_of,
    squads_owner,
)

BENCH_HINT = "Wejdą do gry w kolejności zapisów, jeśli ktoś z grających się wypisze"


def _finish(ok: bool, message: str):
    """Store the outcome and rerun the whole page so it shows the new state."""
    st.session_state["teams_flash"] = ("ok" if ok else "err", message)
    st.rerun()


def _show_flash():
    flash = st.session_state.pop("teams_flash", None)
    if flash:
        kind, message = flash
        (st.success if kind == "ok" else st.error)(message)


# ----- Builder state -------------------------------------------------------
# Kept in session state per game: {"count": team count, "teams": {color:
# [players]}, "random": players placed by the dice, "active": the team a click
# in the pool adds to}, plus "playing"/"targets" refreshed on every render for
# the callbacks below. Buttons stay clickable while a rerun is in flight, so a
# double click can replay a callback on a chip that already moved - the
# callbacks ignore such stale clicks.

def _new_state(players: list, saved: dict | None) -> dict:
    count = default_team_count(len(players))
    if saved and len(saved) in TEAM_COUNTS:
        count = len(saved)
    teams = {color: list((saved or {}).get(color, [])) for color in team_colors(count)}
    return {"count": count, "teams": teams, "random": set(), "active": next(iter(teams))}


def _sync(state: dict, players: list):
    """Fit the state to the current list: drop players who signed out and keep
    the bench (latest signups beyond the limit) out of the teams."""
    playing, _ = split_bench(players, state["count"])
    keep = set(playing)
    for color, names in state["teams"].items():
        state["teams"][color] = [p for p in names if p in keep]
    state["random"] &= {p for names in state["teams"].values() for p in names}
    state["playing"] = playing
    state["targets"] = dict(zip(state["teams"], team_targets(len(playing), state["count"])))


def _pool(state: dict) -> list:
    assigned = {p for names in state["teams"].values() for p in names}
    return [p for p in state["playing"] if p not in assigned]


def _pick(state: dict, player: str):
    """Pool -> active team. Once the team is full, move on to the next one
    that still has room."""
    if player not in _pool(state):
        return
    color = state["active"]
    state["teams"][color].append(player)
    state["random"].discard(player)
    if len(state["teams"][color]) >= state["targets"][color]:
        state["active"] = next(
            (c for c, names in state["teams"].items() if len(names) < state["targets"][c]),
            color,
        )


def _drop(state: dict, color: str, player: str):
    """Team -> pool."""
    if player not in state["teams"].get(color, []):
        return
    state["teams"][color].remove(player)
    state["random"].discard(player)


def _target(state: dict, color: str):
    if color in state["teams"]:
        state["active"] = color


def _fill(state: dict):
    """Dice the rest: everyone still in the pool, around the picked core."""
    pool = _pool(state)
    state["teams"] = fill_randomly(state["teams"], pool, list(state["targets"].values()))
    state["random"] |= set(pool)


def _reroll(state: dict):
    """Throw the dice again for the randomly placed players only."""
    state["teams"] = {
        color: [p for p in names if p not in state["random"]]
        for color, names in state["teams"].items()
    }
    state["random"] = set()
    _fill(state)


def _clear(state: dict):
    state["teams"] = {color: [] for color in state["teams"]}
    state["random"] = set()
    state["active"] = next(iter(state["teams"]))


def _set_count(state: dict, count: int):
    teams = state["teams"]
    state["count"] = count
    state["teams"] = {color: teams.get(color, []) for color in team_colors(count)}
    state["active"] = next(iter(state["teams"]))


def _close_builder(game_id: str):
    st.session_state.pop(f"sq_{game_id}", None)
    st.session_state.pop(f"sq_open_{game_id}", None)


# ----- Builder UI ----------------------------------------------------------

def _team_word(n: int) -> str:
    return "drużyny" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "drużyn"


@st.fragment
def _builder(db, game, players: list, user: dict, admin: bool,
             saved: dict | None = None, mine: bool = False, owner_name: str | None = None):
    """Tap-to-assign squad builder. Runs as a fragment, so a click reruns only
    the builder - no database round-trips until the squads are approved."""
    gid = game["id"]
    key = f"sq_{gid}"
    opening = key not in st.session_state
    if opening:
        st.session_state[key] = _new_state(players, saved)
    state = st.session_state[key]
    _sync(state, players)
    teams, targets = state["teams"], state["targets"]
    if opening:  # start on the first team that still has room
        state["active"] = next(
            (c for c, names in teams.items() if len(names) < targets[c]), state["active"]
        )
    pool = _pool(state)
    bench = players[len(state["playing"]):]

    if saved and mine:
        st.caption(f"Edytujesz swoje składy (konto: {user['email']})")
    elif saved and owner_name:
        st.caption(f"Edytujesz jako admin składy, które ustala **{owner_name}**")
    elif saved:
        st.caption("Edytujesz składy jako admin")
    else:
        st.caption(
            f"Ustalasz jako **{user['name']}** ({user['email']}). Kto pierwszy zatwierdzi "
            "składy, ten nimi zarządza — pozostali widzą podgląd."
        )

    if len(TEAM_COUNTS) > 1:
        ui.builder_label("Liczba drużyn")
        with st.container(horizontal=True, key=f"sqcounts-{gid}"):
            for count in TEAM_COUNTS:
                on = count == state["count"]
                st.button(
                    f"{count} {_team_word(count)} · do {capacity(count)} graczy",
                    key=f"sqcnt-{'on' if on else 'off'}-{count}-{gid}",
                    icon=":material/check:" if on else None,
                    on_click=_set_count,
                    args=(state, count),
                )

    if pool:
        ui.builder_label(f"Do rozdzielenia · {len(pool)}")
        st.caption("Wybierz drużynę i klikaj graczy — trafią do niej. Resztę możesz dolosować.")
        with st.container(horizontal=True, key=f"sqtargets-{gid}"):
            for color, names in teams.items():
                on = color == state["active"]
                st.button(
                    f"{color.capitalize()} · {len(names)}/{targets[color]}",
                    key=f"sqtgt-{'on' if on else 'off'}-{ui.color_slug(color)}-{gid}",
                    icon=":material/check:" if on else None,
                    on_click=_target,
                    args=(state, color),
                )
        with st.container(horizontal=True, key=f"sqpool-{gid}"):
            for player in pool:
                st.button(player, key=f"sqp-{gid}-{player}", on_click=_pick, args=(state, player))
    else:
        st.caption(":material/check_circle: Wszyscy grający są w drużynach")

    with st.container(horizontal=True, key=f"sqactions-{gid}"):
        st.button(
            "Dolosuj resztę", icon=":material/casino:", key=f"sqfill-{gid}",
            on_click=_fill, args=(state,), disabled=not pool,
        )
        if state["random"]:
            st.button(
                "Przelosuj dolosowanych", icon=":material/refresh:", key=f"sqreroll-{gid}",
                on_click=_reroll, args=(state,),
            )
        st.button(
            "Wyczyść", icon=":material/restart_alt:", key=f"sqclear-{gid}",
            on_click=_clear, args=(state,), disabled=len(pool) == len(state["playing"]),
        )

    for col, (color, names) in zip(st.columns(len(teams)), teams.items()):
        slug = ui.color_slug(color)
        with col, st.container(border=True, key=f"sqteam-{slug}-{gid}"):
            ui.builder_team_head(color, len(names), targets[color])
            if names:
                with st.container(horizontal=True, key=f"sqmembers-{slug}-{gid}"):
                    for player in names:
                        st.button(
                            player,
                            key=f"sqm-{slug}-{gid}-{player}",
                            icon=":material/casino:" if player in state["random"] else None,
                            on_click=_drop,
                            args=(state, color, player),
                        )
            else:
                st.caption("Pusto — wybierz tę drużynę i klikaj graczy")
    if state["random"]:
        st.caption(":material/casino: dolosowani · kliknięcie gracza w drużynie zdejmuje go z niej")

    ui.bench_card(bench, f"Zapisali się ponad limit {len(state['playing'])} graczy. {BENCH_HINT}")

    problems = []
    if pool:
        problems.append(f"Rozdziel jeszcze: {ui.pl_players(len(pool))}")
    if any(not names for names in teams.values()):
        problems.append("Każda drużyna musi mieć graczy")
    sizes = [len(names) for names in teams.values()]
    if not problems and max(sizes) - min(sizes) > 1:
        st.warning("Drużyny mają nierówną liczbę graczy: " + " / ".join(map(str, sizes)))

    if st.button(
        "Zatwierdź składy", type="primary", icon=":material/check:",
        key=f"sqsave-{gid}", disabled=bool(problems), width="stretch",
    ):
        fresh = [s["nickname"] for s in get_signups_for_game(db, gid)]
        if fresh != players:
            _finish(False, "Lista zapisanych zmieniła się w międzyczasie — sprawdź składy i zatwierdź ponownie")
        ok, message = save_squads(db, gid, teams, user["email"], admin)
        if ok:
            _close_builder(gid)
        _finish(ok, message)
    if problems:
        st.caption(" · ".join(problems))
    if st.button("Anuluj", key=f"sqcancel-{gid}", type="tertiary", width="stretch"):
        _close_builder(gid)
        st.rerun()


# ----- Page sections -------------------------------------------------------

def _saved_view(db, game, signups, players, rows, user, admin, owner_name):
    gid = game["id"]
    owner = squads_owner(rows)
    mine = bool(user and owner and owner.lower() == user["email"].lower())
    lineups, bench = lineups_with_bench(squads_of(rows), players)

    if owner:
        ui.squad_owner(owner_name, is_you=mine)
    ui.team_cards(lineups)
    if any(slot.get("sub_for") for slots in lineups.values() for slot in slots):
        st.caption(
            ":material/swap_horiz: Ktoś się wypisał — zwolnione miejsce zajmuje pierwsza osoba z ławki"
        )
    ui.bench_card(bench, BENCH_HINT)

    if mine or admin:
        edit_col, delete_col = st.columns(2)
        if edit_col.button("Edytuj składy", icon=":material/edit:", key=f"sqedit_{gid}", width="stretch"):
            st.session_state.pop(f"sq_{gid}", None)  # start from the saved squads
            st.session_state[f"sq_open_{gid}"] = True
            st.rerun()
        with delete_col.popover("Usuń składy", icon=":material/delete:", width="stretch"):
            st.caption("Po usunięciu każdy będzie mógł ustalić składy od nowa.")
            if st.button("Tak, usuń składy", key=f"remove_squads_{gid}", width="stretch"):
                _finish(*delete_squads(db, gid, user["email"], admin))
        if admin and not mine:
            st.caption("Jako admin możesz edytować i usuwać składy ustalone przez innych")
    elif owner:
        st.caption(
            f"Składy może zmienić albo usunąć tylko {owner_name} lub admin — "
            "po usunięciu każdy może ustalić nowe."
        )


def _no_squads(db, game, players, user, admin):
    gid = game["id"]
    can_build = bool(user) and (is_draw_time_allowed() or admin)
    if can_build and players and st.session_state.get(f"sq_open_{gid}"):
        _builder(db, game, players, user, admin, None)
        return

    if not players:
        ui.empty_state("Lista jest pusta", "Składy będzie można ustalić, gdy ktoś się zapisze")
        return
    hint = (
        "Kto pierwszy ustali i zatwierdzi składy, ten nimi zarządza"
        if can_build else DRAW_OPENING_MESSAGE
    )
    ui.empty_state("Składów jeszcze nie ma", hint)
    ui.bench_card(
        bench_for(players, {}),
        f"Zapisali się ponad limit {MAX_PLAYERS} graczy. {BENCH_HINT}",
    )
    if not user:
        st.caption("Zaloguj się na stronie Zapisy, aby móc ustalić składy")
    elif can_build:
        st.caption(f"Na liście: {ui.pl_players(len(players))}")
        if st.button("Ustal składy", type="primary", icon=":material/groups:", key=f"sqopen_{gid}", width="stretch"):
            st.session_state[f"sq_open_{gid}"] = True
            st.rerun()


def teams_page():
    db = init_database()
    if not db:
        return

    ui.page_header("Składy", "Drużyny na najbliższą gierkę")

    games = get_active_games(db)
    if not games:
        ui.empty_state("Brak aktywnej gierki", SIGNUP_OPENING_MESSAGE)
        return

    user = get_current_user()
    admin = is_admin(user)
    _show_flash()

    for game in games:
        gid = game["id"]
        ui.section(format_game_date(parse_game_time(game["start_time"])))

        signups = get_signups_for_game(db, gid)
        players = [s["nickname"] for s in signups]
        rows = get_teams_for_game(db, gid)
        if not rows:
            _no_squads(db, game, players, user, admin)
            continue

        owner = squads_owner(rows)
        owner_name = (
            resolve_account_names(db, signups, [owner]).get(owner.lower()) if owner else None
        )
        mine = bool(user and owner and owner.lower() == user["email"].lower())
        if (mine or admin) and st.session_state.get(f"sq_open_{gid}"):
            _builder(db, game, players, user, admin, squads_of(rows), mine, owner_name)
        else:
            _saved_view(db, game, signups, players, rows, user, admin, owner_name)
