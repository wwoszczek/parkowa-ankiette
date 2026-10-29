"""
Player card distribution from the real database - read-only.

    python card_report.py            # names only
    python card_report.py --emails   # with the account e-mails

Uses the same connection as the app (SUPABASE_DATABASE_URL in .env). Prints
every card - type, rating, games, streaks, form - with the tier counts and the
form model's check, to tune the `cards:` thresholds in game_consts.yaml.
"""

import logging
import sys
from pathlib import Path

import streamlit  # noqa: F401 - creates its loggers, silenced below

sys.path.insert(0, str(Path(__file__).resolve().parent))
# No Streamlit runtime here: skip its "bare mode" warnings
for _name in list(logging.root.manager.loggerDict):
    if _name.startswith("streamlit"):
        logging.getLogger(_name).setLevel(logging.ERROR)

from src.database import get_db  # noqa: E402
from src.utils.cards import STATS, TIER_NAMES, load_cards  # noqa: E402

_TIERS = ["legend", "toty", "inform", "gold", "silver", "bronze"]


def main():
    data = load_cards(get_db())
    cards = sorted(data["cards"].values(), key=lambda c: (-c["ovr"], c["name"].lower()))
    if not cards:
        print("No cards: no played games with Google signups yet.")
        return

    since = data["since"].strftime("%d.%m.%Y") if data.get("since") else "?"
    print(f"{len(cards)} cards from {data['games']} games since {since}\n")
    print("  ".join(f"{TIER_NAMES[t]}: {sum(c['tier'] == t for c in cards)}" for t in _TIERS))
    check = data.get("model")
    if check:
        print(
            f"Form model on the last {check['test_rows']} of {check['rows']} rows: "
            f"AUC {check['auc']:.3f} (baseline {check['baseline_auc']:.3f}), accuracy {check['accuracy']:.1%}"
        )
    print()

    emails = "--emails" in sys.argv
    head = f"{'Player':<22} {'Card':<9} {'OVR':>3} {'Games':>5} {'Run':>4} {'Best':>4} {'L10':>4} {'Form':>5}  " \
        + " ".join(f"{k:>3}" for k in STATS) + ("  E-mail" if emails else "")
    print(head)
    print("-" * len(head))
    for c in cards:
        form = "-" if c["chance"] is None else f"{c['chance']:.0%}"
        print(
            f"{c['name'][:22]:<22} {TIER_NAMES[c['tier']]:<9} {c['ovr']:>3} {c['games']:>5} "
            f"{c['active_streak']:>4} {c['best_streak']:>4} {c['recent']:>4} {form:>5}  "
            + " ".join(f"{c['stats'][k]:>3}" for k in STATS)
            + (f"  {c['email']}" if emails else "")
        )


if __name__ == "__main__":
    main()
