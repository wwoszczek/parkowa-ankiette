"""
Cards page: every player's FUT-style card, and "Twoja karta" - the signed-in
account's own card with the two things a player may set on it, a position
(decoration only) and a photo. Ratings and stats come only from played games.
"""

import streamlit as st

from src.config import init_database
from src.game_config import CARD_THRESHOLDS
from src.ui import components as ui
from src.ui import fut
from src.utils.auth import (
    card_login_ready,
    get_current_user,
    is_admin,
    is_dev_user,
    start_card_login,
)
from src.utils.card_profile import (
    MAX_UPLOAD_MB,
    PHOTO_TYPES,
    POSITIONS,
    load_profiles,
    profiles_ready,
    remove_photo,
    set_photo,
    set_position,
)
from src.utils.cards import STATS, TIER_NAMES, load_cards, rookie_card
from src.utils.signup_utils import account_base_nickname

# Best first: the order of the filter and of the tier counts
_TIERS = ["legend", "toty", "inform", "gold", "silver", "bronze"]
_TIER_PLURALS = {
    "legend": "Legendy", "toty": "TOTY", "inform": "W formie",
    "gold": "Złote", "silver": "Srebrne", "bronze": "Brązowe",
}
_TIER_HINTS = {
    "legend": "Najwyższa ocena i aktywna seria gierek z rzędu",
    "toty": "Drużyna roku: najwięcej gierek w ostatnich 52 tygodniach",
    "inform": "Seria gierek z rzędu i wysoka szansa, że zagrasz w następnej",
    "gold": "Ścisła czołówka zaangażowania",
    "silver": "Środek stawki — regularne granie podniesie kartę",
    "bronze": "Początek drogi — każda rozegrana gierka podnosi kartę",
}


# Feedback shows inside the editor that caused it ("me" or "admin"), in a
# slot that is always there - so the layout, and an open admin expander,
# stay put across the rerun.

def _flash_later(where: str, ok: bool, message: str):
    """From a widget callback: shown after the rerun Streamlit does anyway."""
    st.session_state["cards_flash"] = (where, "ok" if ok else "err", message)


def _finish(where: str, ok: bool, message: str):
    _flash_later(where, ok, message)
    st.rerun()


def _show_flash(where: str):
    slot = st.empty()
    flash = st.session_state.get("cards_flash")
    if flash and flash[0] == where:
        del st.session_state["cards_flash"]
        _, kind, message = flash
        (slot.success if kind == "ok" else slot.error)(message)


def _percent(chance) -> str:
    return "–" if chance is None else f"{round(chance * 100)}%"


# ----- Editing: position and photo ---------------------------------------------

def _save_position(db, email: str, widget: str, actor: str, admin: bool, key: str):
    _flash_later(key, *set_position(db, email, st.session_state.get(widget), actor, admin))


def _editor(db, email: str, profile: dict, actor: str, admin: bool, key: str):
    """Position picker and photo upload for one account's card."""
    _show_flash(key)
    if not profiles_ready(db):
        st.caption(
            ":material/info: Pozycja i zdjęcie na karcie będą dostępne po dodaniu tabeli "
            "player_cards w bazie" if admin else ":material/info: Pozycja i zdjęcie na karcie będą dostępne wkrótce"
        )
        return

    widget = f"cardpos-{key}-{email}"
    st.segmented_control(
        "Pozycja na karcie",
        list(POSITIONS),
        default=profile.get("position"),
        format_func=lambda code: code,
        key=widget,
        on_change=_save_position,
        args=(db, email, widget, actor, admin, key),
        help="Tylko ozdoba karty: " + ", ".join(f"{c} — {n.lower()}" for c, n in POSITIONS.items())
             + ". Nie wpływa na składy ani na ustawienie na boisku.",
    )

    with st.form(f"cardphoto-{key}", clear_on_submit=True, border=False):
        upload = st.file_uploader(
            f"Zdjęcie na kartę (JPG, PNG, WebP, do {MAX_UPLOAD_MB} MB)",
            type=PHOTO_TYPES,
            key=f"cardfile-{key}",
        )
        if st.form_submit_button("Zapisz zdjęcie", icon=":material/upload:", width="stretch"):
            if upload is None:
                _finish(key, False, "Najpierw wybierz zdjęcie")
            _finish(key, *set_photo(db, email, upload.getvalue(), actor, admin))
    if profile.get("photo") and st.button(
        "Usuń zdjęcie", key=f"remove_cardphoto-{key}", icon=":material/delete:", width="stretch"
    ):
        _finish(key, *remove_photo(db, email, actor, admin))
    st.caption(
        "Zdjęcie widzą wszyscy na tej stronie. Przycinamy je do kwadratu i zmniejszamy — "
        "najlepiej wygląda twarz na środku."
    )


# ----- Sections -------------------------------------------------------------------

def _facts(card: dict):
    tier = card["tier"]
    st.markdown(f"**{TIER_NAMES[tier]}** · {card['ovr']} OVR")
    if card["games"]:
        st.caption(_TIER_HINTS[tier])
    else:
        st.caption(
            "Nie masz jeszcze rozegranej gierki — zaczynasz od brązowej karty. "
            "Każda gierka podnosi ocenę, a seria gierek z rzędu najbardziej."
        )
    ui.stat_chips([
        (card["games"], "gierki"),
        (card["active_streak"], "z rzędu"),
        (_percent(card.get("chance")), "forma"),
    ])


def _your_card(db, data: dict, profiles: dict, user):
    ui.section("Twoja karta")
    if not user:
        if card_login_ready():
            st.caption(
                "Zaloguj się kontem Google, żeby zobaczyć swoją kartę, ustawić na niej "
                "pozycję i dodać zdjęcie."
            )
            if st.button("Pokaż moją kartę", key="gbtn_card", width="stretch"):
                start_card_login()
        else:
            st.caption(
                "Zapisz się albo wypisz kontem Google na stronie Zapisy — potem zobaczysz "
                "tu swoją kartę."
            )
        return

    email = user["email"].lower()
    card = data["cards"].get(email) or rookie_card(
        email, account_base_nickname(db, email, user["name"])
    )
    profile = profiles.get(email, {})
    card_col, info_col = st.columns([2, 3], gap="large")
    with card_col:
        fut.card(card, profile.get("photo"), profile.get("position"))
    with info_col:
        _facts(card)
        st.caption(f"Konto: {user['email']}")
        _editor(db, email, profile, user["email"], admin=False, key="me")
        if not is_dev_user() and card_login_ready():
            if st.button("To nie moja karta — zmień konto", key="card_switch",
                         type="tertiary", icon=":material/swap_horiz:"):
                start_card_login()


def _all_cards(data: dict, profiles: dict):
    cards = sorted(data["cards"].values(), key=lambda c: (-c["ovr"], c["name"].lower()))
    counts = {tier: sum(1 for c in cards if c["tier"] == tier) for tier in _TIERS}
    present = [tier for tier in _TIERS if counts[tier]]
    chosen = st.pills(
        "Rodzaj karty",
        present,
        format_func=lambda tier: f"{_TIER_PLURALS[tier]} · {counts[tier]}",
        key="cards_filter",
        label_visibility="collapsed",
    )
    shown = [c for c in cards if chosen is None or c["tier"] == chosen]
    fut.card_grid(
        (c, profiles.get(c["email"], {}).get("photo"), profiles.get(c["email"], {}).get("position"))
        for c in shown
    )


def _how_it_works(data: dict):
    t = CARD_THRESHOLDS
    since = data.get("since")
    with st.expander("Jak liczone są karty", icon=":material/help:"):
        st.markdown(
            "Karta liczy się wyłącznie z **rozegranych gierek** od "
            f"{since.strftime('%d.%m.%Y') if since else 'początku zapisów przez Google'} "
            "(wcześniejsze zapisy na hasło nie są brane pod uwagę). Gierka na ławce rezerwowych "
            "się nie liczy. Nikt — także admin — nie ustawia statystyk ręcznie; zmienić możesz "
            "tylko pozycję i zdjęcie.\n\n"
            "**Statystyki (30–99)** porównują Cię z resztą grupy:\n"
            + "".join(f"- **{key}** — {text.split(' — ', 1)[1]}\n" for key, text in STATS.items())
            + "\n**Ocena (OVR)** to Twoje miejsce w rankingu zaangażowania: liczba gierek (30%), "
            "ostatnie 10 gierek (20%), aktualna seria z rzędu (15%), staż (12%), najdłuższa seria "
            "(10%), szybkość zapisu (8%) i goście (5%). Ranking przekłada się na przedziały jak w FUT: "
            f"najmniej zaangażowane {round(t['bronze_share'] * 100)}% kart to brąz (50–64), "
            f"kolejne {round(t['silver_share'] * 100)}% srebro (65–74), reszta złoto (75–95). "
            f"Nowi gracze zaczynają od brązu: srebro wymaga co najmniej {t['silver_games']} rozegranych "
            f"gierek, złoto {t['gold_games']}.\n\n"
            "**Karty specjalne**\n"
            f"- **Legenda** — ocena co najmniej {t['legend']} i co najmniej {t['legend_streak']} "
            "gierki z rzędu aż do ostatniej\n"
            f"- **TOTY** — {t['toty_size']} złote karty z największą liczbą gierek w ostatnich 52 tygodniach\n"
            f"- **W formie** — srebrna lub złota karta, seria co najmniej {t['in_form_streak']} gierek "
            f"i co najmniej {round(t['in_form_chance'] * 100)}% szans na grę w następnej gierce "
            f"(najwyżej {t['in_form_max']} karty)\n\n"
            "**Forma** to przewidywana szansa, że zagrasz w następnej gierce. Liczy ją mały model "
            "uczenia maszynowego (regresja logistyczna) wytrenowany na historii obecności całej "
            "grupy: ostatnia gierka, obecność w ostatnich 4 i 10 gierkach, seria, liczba gierek i staż.\n\n"
            "Ocena mierzy zaangażowanie, nie umiejętności — dlatego nie wpływa na składy."
        )


# ----- Admin --------------------------------------------------------------------------

def _admin_cards(db, data: dict, profiles: dict, user: dict):
    with st.expander("Zdjęcia i pozycje graczy (admin)", icon=":material/photo_camera:"):
        cards = sorted(data["cards"].values(), key=lambda c: c["name"].lower())
        options = [c["email"] for c in cards] + [""]
        email = st.selectbox(
            "Konto",
            options,
            format_func=lambda e: f"{data['cards'][e]['name']} ({e})" if e else "Inne konto (wpisz e-mail)…",
            key="admin_card_account",
        )
        if not email:
            email = st.text_input("E-mail konta Google", key="admin_card_email").strip().lower()
            if not email:
                return
        card = data["cards"].get(email) or rookie_card(email, email.split("@")[0])
        profile = profiles.get(email, {})
        preview_col, edit_col = st.columns([2, 3], gap="large")
        with preview_col:
            fut.card(card, profile.get("photo"), profile.get("position"))
        with edit_col:
            _editor(db, email, profile, user["email"], admin=True, key="admin")


def _admin_calibration(data: dict):
    cards = sorted(data["cards"].values(), key=lambda c: -c["ovr"])
    with st.expander("Rozkład kart i model (admin)", icon=":material/query_stats:"):
        counts = [(sum(1 for c in cards if c["tier"] == tier), _TIER_PLURALS[tier]) for tier in _TIERS]
        ui.stat_chips(counts)
        check = data.get("model")
        if check:
            st.caption(
                f"Model formy, sprawdzony na ostatnich {check['test_rows']} obserwacjach "
                f"(z {check['rows']}): AUC {check['auc']:.2f} wobec {check['baseline_auc']:.2f} dla "
                f"prostej reguły „obecność w ostatnich 4 gierkach”, trafność {check['accuracy']:.0%}."
            )
        else:
            st.caption("Za mało historii, żeby wytrenować i sprawdzić model formy.")
        st.dataframe(
            [
                {
                    "Gracz": c["name"], "Karta": TIER_NAMES[c["tier"]], "OVR": c["ovr"],
                    "Gierki": c["games"], "Z rzędu": c["active_streak"], "Rekord serii": c["best_streak"],
                    "Ostatnie 10": c["recent"], "Forma": _percent(c.get("chance")),
                    **c["stats"], "E-mail": c["email"],
                }
                for c in cards
            ],
            hide_index=True,
        )
        st.caption("Progi kart są w sekcji cards w game_consts.yaml.")


def cards_page():
    db = init_database()
    if not db:
        return

    ui.page_header("Karty", "Karta każdego gracza rośnie z każdą rozegraną gierką")

    data = load_cards(db)
    profiles = load_profiles(db)
    user = get_current_user()
    admin = is_admin(user)

    _your_card(db, data, profiles, user)

    ui.section("Wszystkie karty")
    if not data["cards"]:
        ui.empty_state(
            "Kart jeszcze nie ma",
            "Pojawią się po pierwszej gierce rozegranej z zapisami przez Google",
        )
    else:
        _all_cards(data, profiles)
    _how_it_works(data)

    if admin:
        _admin_cards(db, data, profiles, user)
        _admin_calibration(data)
