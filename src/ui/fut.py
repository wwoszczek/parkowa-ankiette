"""
FUT-style (FIFA 14-17) player cards and the squad pitch, as presentational HTML.
Original designs in that spirit - shield-shaped card, rating and position in
the corner, six stats - drawn with CSS and inline SVG, no game artwork. User
content is always escaped; photos arrive as data URIs.
"""

from functools import lru_cache
from html import escape

import streamlit as st

from src.ui import graphics
from src.utils.cards import STATS, TIER_NAMES

# Formation rows from the goal up, by team size (1-2-2-1 and 1-2-3-1)
FORMATIONS = {6: [1, 2, 2, 1], 7: [1, 2, 3, 1]}

# The card outline as fractions of width and height: rounded top corners
# into a gentle arch, straight sides, shoulders curving into a rounded point.
# "Q"/"C" are quadratic/cubic Bezier segments, "L" a straight line; the
# curves are sampled into a fine polygon for clip-path.
_SHAPE = [
    ("M", (0, 0.085)),
    ("C", (0, 0.045), (0.05, 0.034), (0.15, 0.026)),
    ("Q", (0.5, -0.012), (0.85, 0.026)),
    ("C", (0.95, 0.034), (1, 0.045), (1, 0.085)),
    ("L", (1, 0.835)),
    ("C", (1, 0.875), (0.93, 0.89), (0.80, 0.925)),
    ("L", (0.57, 0.983)),
    ("Q", (0.5, 1.002), (0.43, 0.983)),
    ("L", (0.20, 0.925)),
    ("C", (0.07, 0.89), (0, 0.875), (0, 0.835)),
]
_STEPS = 18  # samples per curve
# Card sizes in px, the inset of the inner panel and the frame line width
SIZES = {"full": (186, 300, 5, 1.5), "mini": (84, 116, 3, 1)}


def _bezier(points: list, t: float) -> tuple:
    while len(points) > 1:  # de Casteljau
        points = [((1 - t) * x1 + t * x2, (1 - t) * y1 + t * y2) for (x1, y1), (x2, y2) in zip(points, points[1:])]
    return points[0]


@lru_cache(maxsize=None)
def shape_points(width: int, height: int, inset: float = 0) -> tuple:
    """The outline in px, moved `inset` px inward: every point shifted along
    the inward normal of its neighbours, so the inner panel and the frame run
    parallel to the card edge all the way round."""
    def px(point):
        return point[0] * width, point[1] * height

    points = [px(_SHAPE[0][1])]
    for kind, *controls in _SHAPE[1:]:
        if kind == "L":
            points.append(px(controls[0]))
            continue
        curve = [points[-1]] + [px(c) for c in controls]
        points += [_bezier(curve, step / _STEPS) for step in range(1, _STEPS + 1)]
    if not inset:
        return tuple(points)

    def normal(a, b):  # inward for a clockwise outline (y grows downwards)
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = (dx * dx + dy * dy) ** 0.5
        return -dy / length, dx / length

    n = len(points)
    shifted = []
    for i, point in enumerate(points):
        before = normal(points[i - 1], point)
        after = normal(point, points[(i + 1) % n])
        nx, ny = before[0] + after[0], before[1] + after[1]
        length = (nx * nx + ny * ny) ** 0.5
        nx, ny = nx / length, ny / length
        scale = inset / max(0.3, nx * after[0] + ny * after[1])  # corners stay `inset` from both edges
        shifted.append((point[0] + nx * scale, point[1] + ny * scale))
    return tuple(shifted)


def _coords(points) -> str:
    return ", ".join(f"{x:.1f}px {y:.1f}px" for x, y in points)


def shape_css(width: int, height: int, inset: float = 0) -> str:
    """clip-path of the outline (moved `inset` px inward)."""
    return f"polygon({_coords(shape_points(width, height, inset))})"


def ring_css(width: int, height: int, inset: float, line: float) -> str:
    """clip-path of the frame line: the band between two inset outlines
    (the evenodd rule cuts the inner one out)."""
    outer = shape_points(width, height, inset)
    inner = shape_points(width, height, inset + line)
    return f"polygon(evenodd, {_coords(outer + outer[:1] + inner + inner[:1])})"


def _render(html: str):
    st.markdown(html, unsafe_allow_html=True)


def _silhouette() -> str:
    """Generic player placeholder: head and shoulders."""
    return (
        '<svg class="fc-silhouette" viewBox="0 0 100 100" aria-hidden="true">'
        '<circle cx="50" cy="36" r="19"/>'
        '<path d="M14 100 C16 72 32 60 50 60 C68 60 84 72 86 100 Z"/>'
        "</svg>"
    )


def _photo(photo_uri: str | None) -> str:
    if photo_uri:
        return f'<img class="fc-img" src="{photo_uri}" alt="">'
    return _silhouette()


def _short_name(name: str) -> str:
    """Name on a mini card: whole when it fits, else the surname as in FUT -
    unless the last word is just an initial or a number ("Janek K", "Wojtek 2")."""
    words = name.split()
    if len(name) <= 9 or len(words) < 2 or len(words[-1]) < 3:
        return name
    return words[-1]


def card_html(card: dict, photo_uri: str | None = None, position: str | None = None,
              mini: bool = False, note: str = "", dim: bool = False) -> str:
    """One card. `card` comes from utils.cards (or a guest stand-in with tier
    "guest"); `note` is a small tag under a mini card (e.g. "z ławki"), `dim`
    greys it out (a freed place nobody took)."""
    tier = card.get("tier", "bronze")
    ovr = card.get("ovr")
    ovr_html = "–" if ovr is None else str(ovr)
    pos_html = f'<div class="fc-pos">{escape(position)}</div>' if position else ""
    name = escape(str(card.get("name", "")))
    if mini:
        note_html = f'<div class="fc-note">{escape(note)}</div>' if note else ""
        return (
            f'<div class="fc-wrap fc-wrap-mini{" fc-out" if dim else ""}" title="{name}">'
            f'<div class="fc fc-mini fc-{tier}"><div class="fc-frame"></div>'
            f'<div class="fc-meta"><div class="fc-ovr">{ovr_html}</div>{pos_html}</div>'
            f'<div class="fc-photo">{_photo(photo_uri)}</div>'
            f'<div class="fc-name">{escape(_short_name(str(card.get("name", ""))))}</div>'
            "</div>"
            f"{note_html}"
            "</div>"
        )
    stats = card.get("stats") or {}
    cells = [
        f'<div class="fc-stat" title="{escape(STATS[key])}"><b>{stats.get(key, "–")}</b><span>{key}</span></div>'
        for key in STATS
    ]
    return (
        '<div class="fc-wrap">'
        f'<div class="fc fc-{tier}" title="Karta: {TIER_NAMES.get(tier, tier)}"><div class="fc-frame"></div>'
        '<div class="fc-top">'
        '<div class="fc-meta">'
        f'<div class="fc-ovr">{ovr_html}</div>{pos_html}'
        f'<div class="fc-club">{graphics.ball(20, "currentColor")}</div>'
        "</div>"
        f'<div class="fc-photo">{_photo(photo_uri)}</div>'
        "</div>"
        f'<div class="fc-name{_name_size(name)}">{name}</div>'
        '<div class="fc-stats">'
        f'<div class="fc-col">{"".join(cells[:3])}</div>'
        '<div class="fc-sep"></div>'
        f'<div class="fc-col">{"".join(cells[3:])}</div>'
        "</div>"
        "</div>"
        "</div>"
    )


def _name_size(name: str) -> str:
    length = len(name)
    return " fc-name-xlong" if length > 14 else " fc-name-long" if length > 12 else ""


def card(card: dict, photo_uri: str | None = None, position: str | None = None):
    """One big card, centred in its column."""
    _render(f'<div class="fc-solo">{card_html(card, photo_uri, position)}</div>')


def card_grid(items):
    """items: iterable of (card, photo_uri, position)."""
    cells = "".join(f'<div class="fc-cell">{card_html(c, uri, pos)}</div>' for c, uri, pos in items)
    _render(f'<div class="fc-grid">{cells}</div>')


def _rows(size: int) -> list:
    """Formation rows from the goal up: fixed for 6 and 7, otherwise a keeper
    and the rest spread over defence, midfield and attack."""
    if size in FORMATIONS:
        return FORMATIONS[size]
    if size <= 1:
        return [size]
    rest = size - 1
    rows = [1, rest // 3, rest // 3, rest // 3]
    for i in range(rest % 3):
        rows[2 - i] += 1  # midfield first, then defence
    return [r for r in rows if r]


def pitch_html(color: str, team_hex: str, minis: list) -> str:
    """A team on half a pitch, keeper at the bottom. minis: card HTML (mini) in
    lineup order - the first plays in goal, then defence, midfield, attack.
    Positions on the cards are decoration only and never move anyone."""
    rows, i = [], 0
    for count in _rows(len(minis)):
        rows.append(f'<div class="fc-row">{"".join(minis[i:i + count])}</div>')
        i += count
    return (
        f'<div class="fc-squad" style="--team:{team_hex}">'
        '<div class="fc-squad-head">'
        f'<span class="fc-team-jersey">{graphics.jersey(team_hex, None, 28)}</span>'
        f"<span>Drużyna {escape(color)}</span>"
        "</div>"
        '<div class="fc-pitch">'
        '<div class="fc-lines"></div>'
        f'{"".join(reversed(rows))}'
        "</div>"
        "</div>"
    )


def squads_pitch(teams_html: list):
    _render(f'<div class="fc-squads">{"".join(teams_html)}</div>')
