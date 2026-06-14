"""
Inline SVG graphics (self-contained, no external requests - safe on free tier).
"""

from html import escape


def _is_light(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150


def ball(size: int = 24, color: str = "currentColor", opacity: float = 1.0) -> str:
    """Minimal soccer ball mark: outer circle, central pentagon and seams."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" fill="none" '
        f'stroke="{color}" stroke-width="3" stroke-linejoin="round" '
        f'opacity="{opacity}" aria-hidden="true">'
        '<circle cx="60" cy="60" r="50"/>'
        '<polygon points="60,44 75.2,55.1 69.4,72.9 50.6,72.9 44.8,55.1" '
        f'fill="{color}" fill-opacity="0.18"/>'
        '<line x1="60" y1="44" x2="60" y2="12"/>'
        '<line x1="75.2" y1="55.1" x2="105" y2="46"/>'
        '<line x1="69.4" y1="72.9" x2="88" y2="98"/>'
        '<line x1="50.6" y1="72.9" x2="32" y2="98"/>'
        '<line x1="44.8" y1="55.1" x2="15" y2="46"/>'
        "</svg>"
    )


def jersey(hex_color: str, number=None, size: int = 26) -> str:
    """A football shirt silhouette in the team color, optional number printed on it."""
    text_color = "#1F1F1F" if _is_light(hex_color) else "#FFFFFF"
    stroke = "#9AA597" if _is_light(hex_color) else "rgba(0,0,0,0.12)"
    label = (
        f'<text x="24" y="32" text-anchor="middle" font-size="15" '
        f'font-weight="800" font-family="Manrope, sans-serif" '
        f'fill="{text_color}">{escape(str(number))}</text>'
        if number is not None
        else ""
    )
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 48 48" '
        f'aria-hidden="true" class="pk-jersey-svg">'
        '<path d="M18 7 C18 11 21 13 24 13 C27 13 30 11 30 7 L34 8 L44 17 '
        "L38 25 L34 22 L34 42 L14 42 L14 22 L10 25 L4 17 L14 8 Z\" "
        f'fill="{hex_color}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="round"/>'
        f"{label}"
        "</svg>"
    )


# Faint pitch motif for the hero card: the halfway line with the centre
# circle and spot sitting on it. Opacity sits on the group (not on individual
# strokes) so overlapping shapes composite evenly instead of stacking up
# brighter at intersections.
HERO_DECO = (
    '<svg class="pk-hero-deco" viewBox="0 0 220 220" fill="none" aria-hidden="true">'
    '<g stroke="#FFFFFF" stroke-width="3" opacity="0.22">'
    '<line x1="110" y1="0" x2="110" y2="220"/>'
    '<circle cx="110" cy="110" r="62"/>'
    '<circle cx="110" cy="110" r="6" fill="#FFFFFF" stroke="none"/>'
    "</g>"
    "</svg>"
)


def empty_illustration() -> str:
    """Line-art ball resting on a short pitch line, for empty states."""
    return (
        '<svg class="pk-empty-illust" viewBox="0 0 160 120" fill="none" '
        'aria-hidden="true">'
        '<line x1="20" y1="96" x2="140" y2="96" stroke="#CBD4BF" '
        'stroke-width="3" stroke-linecap="round"/>'
        '<ellipse cx="80" cy="100" rx="34" ry="6" fill="#E4EADC"/>'
        '<g stroke="#B4C0A4" stroke-width="3" stroke-linejoin="round" fill="none">'
        '<circle cx="80" cy="60" r="30"/>'
        '<polygon points="80 50 89 57 86 67 74 67 71 57" '
        'fill="#EAF0E2" stroke="#B4C0A4"/>'
        '<line x1="80" y1="50" x2="80" y2="32"/>'
        '<line x1="89" y1="57" x2="107" y2="52"/>'
        '<line x1="86" y1="67" x2="97" y2="83"/>'
        '<line x1="74" y1="67" x2="63" y2="83"/>'
        '<line x1="71" y1="57" x2="53" y2="52"/>'
        "</g>"
        "</svg>"
    )
