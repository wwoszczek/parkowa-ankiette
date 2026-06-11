"""
Reusable presentational components (HTML/CSS, no business logic).
"""

from html import escape

import streamlit as st

from src.utils.datetime_utils import (
    format_game_date,
    parse_timestamp,
    relative_day_label,
)

# Team colors as stored in the `teams.team_color` column (Polish adjectives).
TEAM_COLOR_HEX = {
    "biała": "#D8DCD4",
    "czerwona": "#C8333A",
    "czarna": "#1F1F1F",
}
_DEFAULT_TEAM_HEX = "#1E7A46"


def _render(html: str):
    st.markdown(html, unsafe_allow_html=True)


def pl_players(n: int) -> str:
    """Polish plural for 'gracz'."""
    if n == 1:
        return "1 gracz"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} gracze"
    return f"{n} graczy"


def page_header(title: str, subtitle: str = ""):
    sub = f'<p class="pk-sub">{escape(subtitle)}</p>' if subtitle else ""
    _render(f'<h1 class="pk-h1">{escape(title)}</h1>{sub}')


def section(title: str):
    _render(f'<div class="pk-section">{escape(title)}</div>')


def hero(game_dt, chips=()):
    """Highlight card with the upcoming game date."""
    chips_html = "".join(f'<span class="pk-chip">{escape(c)}</span>' for c in chips if c)
    chips_block = f'<div class="pk-hero-chips">{chips_html}</div>' if chips_html else ""
    _render(
        '<div class="pk-hero">'
        '<div class="pk-hero-label">Najbliższa gierka</div>'
        f'<div class="pk-hero-date">{escape(format_game_date(game_dt, with_time=False))}</div>'
        f'<div class="pk-hero-meta">{game_dt.strftime("%H:%M")} · {escape(relative_day_label(game_dt))}</div>'
        f"{chips_block}"
        "</div>"
    )


def empty_state(title: str, hint: str = ""):
    hint_html = f'<div class="pk-empty-hint">{escape(hint)}</div>' if hint else ""
    _render(
        f'<div class="pk-empty"><div class="pk-empty-title">{escape(title)}</div>{hint_html}</div>'
    )


def stat_chips(items):
    """items: iterable of (value, label) pairs."""
    chips = "".join(
        '<div class="pk-stat">'
        f'<div class="pk-stat-num">{escape(str(value))}</div>'
        f'<div class="pk-stat-label">{escape(label)}</div>'
        "</div>"
        for value, label in items
    )
    _render(f'<div class="pk-stats">{chips}</div>')


def players_table(signups, current_email: str | None = None):
    """Signup list as a styled table; highlights the current user's row."""
    if not signups:
        empty_state("Nikt się jeszcze nie zapisał", "Lista czeka na pierwszego śmiałka.")
        return

    # Map account e-mails to nicknames so guest rows can show who added them.
    adders = {
        s["user_email"].lower(): s["nickname"]
        for s in signups
        if s.get("user_email") and not s.get("is_guest")
    }
    me = current_email.lower() if current_email else None

    rows = []
    for i, s in enumerate(signups, start=1):
        badges = ""
        row_cls = ""
        if me and (s.get("user_email") or "").lower() == me and not s.get("is_guest"):
            badges += '<span class="pk-badge pk-badge-you">Ty</span>'
            row_cls = ' class="pk-row-me"'
        if s.get("is_guest"):
            adder = adders.get((s.get("added_by_email") or "").lower())
            label = f"gość · {adder}" if adder else "gość"
            badges += f'<span class="pk-badge pk-badge-guest">{escape(label)}</span>'
            if me and (s.get("added_by_email") or "").lower() == me:
                row_cls = ' class="pk-row-me"'
        signed_at = parse_timestamp(s["timestamp"]).strftime("%d.%m · %H:%M")
        rows.append(
            f"<tr{row_cls}>"
            f'<td class="pk-num">{i}</td>'
            f"<td>{escape(s['nickname'])}{badges}</td>"
            f'<td class="pk-time">{signed_at}</td>'
            "</tr>"
        )

    _render(
        '<div class="pk-card"><table class="pk-table">'
        "<thead><tr><th>#</th><th>Gracz</th><th>Zapis</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div>"
    )


def team_cards(teams: dict):
    """teams: {team_color: [players]} rendered as a responsive card grid."""
    cards = []
    for color, players in teams.items():
        hex_color = TEAM_COLOR_HEX.get(str(color).lower(), _DEFAULT_TEAM_HEX)
        items = "".join(f"<li>{escape(str(p))}</li>" for p in players)
        cards.append(
            f'<div class="pk-team" style="--team:{hex_color}">'
            f'<div class="pk-team-head"><span class="pk-team-dot"></span>Drużyna {escape(str(color))}</div>'
            f"<ol>{items}</ol>"
            "</div>"
        )
    _render(f'<div class="pk-teams">{"".join(cards)}</div>')


def account_strip(name: str):
    _render(f'<div class="pk-account">Zalogowano jako <b>{escape(name)}</b></div>')
