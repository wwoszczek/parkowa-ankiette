"""
Player cards in the style of FUT (FIFA 14-17): every Google account gets a card
whose rating, stats and type come only from its history of played games since
signups moved to Google accounts. Nothing here is editable - stats measure
commitment (games, streaks, signup speed, guests brought), not football skill.

A small logistic regression, trained on the same history, estimates each
player's chance of turning up next week ("forma"); it drives the "W formie"
card. It is numpy-only and fits in well under a second on a few years of games.
"""

import math
from datetime import datetime
from statistics import median

import numpy as np
import streamlit as st

from src.constants import TIMEZONE
from src.database import SupabaseDB
from src.game_config import CARD_THRESHOLDS, CARDS_SINCE
from src.utils.datetime_utils import parse_game_time, parse_timestamp, signup_opening_for
from src.utils.team_utils import bench_for
from src.utils.teams_db import get_squads_between

# Stat keys in card order (Polish FUT abbreviations) with what they measure
STATS = {
    "TEM": "Tempo — jak szybko zapisujesz się po otwarciu zapisów",
    "STR": "Strzały — obecność w ostatnich 10 gierkach",
    "POD": "Podania — goście, których przyprowadzasz",
    "DRY": "Drybling — najdłuższa seria gierek z rzędu",
    "OBR": "Obrona — staż: od ilu gierek jesteś z nami",
    "FIZ": "Fizyczność — liczba rozegranych gierek",
}
TIER_NAMES = {
    "bronze": "Brązowa", "silver": "Srebrna", "gold": "Złota",
    "inform": "W formie", "toty": "TOTY", "legend": "Legenda", "guest": "Gość",
}
_RECENT = 10        # games that count as "recent form"
_MIN_TRAIN_GAME = 4  # model rows start once a few games of history exist


# ----- History -------------------------------------------------------------

def played_games(games: list, signups: list, squads: dict) -> list:
    """For each game (ascending), {email: signup row} of the accounts that
    played it - signed up with a Google account and not left on the bench."""
    by_game = {}
    for row in signups:
        by_game.setdefault(row["game_id"], []).append(row)
    played = []
    for game in games:
        rows = by_game.get(game["id"], [])
        benched = set()
        if game["id"] in squads:
            benched = set(bench_for([r["nickname"] for r in rows], squads[game["id"]]))
        played.append({
            r["user_email"].lower(): r
            for r in rows
            if r.get("user_email") and not r.get("is_guest") and r["nickname"] not in benched
        })
    return played


def _streaks(flags: list) -> tuple:
    """(active, best) runs of True in a list ordered oldest -> newest."""
    best = run = 0
    for flag in flags:
        run = run + 1 if flag else 0
        best = max(best, run)
    return run, best


# ----- Forma: next-game attendance model -------------------------------------

def _features(flags: list) -> list:
    """Model features from an account's attendance before some game (oldest ->
    newest): last game, form over 4 and 10 games, current streak, volume and
    tenure."""
    n = len(flags)
    first = flags.index(True) if True in flags else n
    active, _ = _streaks(flags)
    return [
        1.0 if flags and flags[-1] else 0.0,
        sum(flags[-4:]) / 4,
        sum(flags[-_RECENT:]) / _RECENT,
        min(active, 10) / 10,
        math.log1p(sum(flags)) / math.log1p(50),
        math.log1p(n - first) / math.log1p(50),
    ]


def _training_rows(history: dict, n_games: int):
    """(X, y, game index) over every game after the first few, for accounts
    that had already played before it."""
    X, y, t_index = [], [], []
    for flags in history.values():
        for t in range(_MIN_TRAIN_GAME, n_games):
            past = flags[:t]
            if True not in past:
                continue
            X.append(_features(past))
            y.append(1.0 if flags[t] else 0.0)
            t_index.append(t)
    return np.array(X), np.array(y), np.array(t_index)


def _fit(X, y, l2=0.01, steps=1500, lr=0.5):
    """Logistic regression by gradient descent on standardised features."""
    mean, std = X.mean(axis=0), X.std(axis=0) + 1e-9
    Z = (X - mean) / std
    w, b = np.zeros(Z.shape[1]), 0.0
    for _ in range(steps):
        p = 1 / (1 + np.exp(-(Z @ w + b)))
        w -= lr * (Z.T @ (p - y) / len(y) + l2 * w)
        b -= lr * float(np.mean(p - y))
    return {"w": w, "b": b, "mean": mean, "std": std}


def _predict(model, X):
    Z = (np.atleast_2d(X) - model["mean"]) / model["std"]
    return 1 / (1 + np.exp(-(Z @ model["w"] + model["b"])))


def _auc(y, p):
    """Probability that a random attendee scores above a random absentee."""
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg):
        return None
    return float(np.mean([(neg < s).mean() + 0.5 * (neg == s).mean() for s in pos]))


def form_model(history: dict, n_games: int) -> dict:
    """Train on all history, report a time-split check (fit on the first 75%
    of games, score the rest) against a "same as the last 4 games" baseline,
    and predict each account's chance of playing the next game."""
    X, y, t_index = _training_rows(history, n_games)
    if len(y) < 50 or len(set(y)) < 2:
        return {"chances": {}, "check": None}
    split = int(n_games * 0.75)
    train, test = t_index < split, t_index >= split
    check = None
    if train.sum() >= 50 and test.sum() >= 20 and len(set(y[train])) == 2:
        p = _predict(_fit(X[train], y[train]), X[test])
        baseline = X[test][:, 1]
        check = {
            "rows": int(len(y)), "test_rows": int(test.sum()),
            "auc": _auc(y[test], p), "baseline_auc": _auc(y[test], baseline),
            "accuracy": float(((p >= 0.5) == (y[test] == 1)).mean()),
        }
    model = _fit(X, y)
    chances = {
        email: float(_predict(model, _features(flags))[0])
        for email, flags in history.items() if True in flags
    }
    return {"chances": chances, "check": check}


# ----- Cards -----------------------------------------------------------------

def _scale(value: float) -> int:
    """0..1 -> a card stat (30..99)."""
    return int(round(30 + 69 * max(0.0, min(1.0, value))))


def _rank_shares(values: dict) -> dict:
    """Each key's position among all values, 0 (lowest) .. 1 (highest); ties
    share the middle of their places."""
    ordered = sorted(values.values())
    n = len(ordered)
    if n < 2:
        return {key: 1.0 for key in values}
    shares = {}
    for key, value in values.items():
        below = sum(1 for v in ordered if v < value)
        equal = sum(1 for v in ordered if v == value)
        shares[key] = (below + (equal - 1) / 2) / (n - 1)
    return shares


def _ovr(share: float, t: dict) -> int:
    """Commitment rank (0..1) -> rating on FUT bands: the lowest
    `bronze_share` lands in bronze (50-64), the next `silver_share` in silver
    (65-74), the rest in gold (75-95)."""
    low, mid = t["bronze_share"], t["bronze_share"] + t["silver_share"]
    if share < low:
        return int(50 + 14 * share / low)
    if share < mid:
        return int(65 + 9.99 * (share - low) / (mid - low))
    return int(round(75 + 20 * (share - mid) / (1 - mid)))


def build_cards(games: list, signups: list, squads: dict) -> dict:
    """Cards for every account with history. games: [{id, start_time}] in play
    order; signups: rows of those games ordered by signup time; squads:
    {game_id: {color: [names]}}. Returns {"cards": {email: card}, "model",
    "games"}.

    Everything is relative to the real distribution: stats compare a player
    with the group (or its maxima), and the rating is the player's rank in
    overall commitment mapped onto FUT bands."""
    played = played_games(games, signups, squads)
    n = len(played)
    emails = {email for game in played for email in game}
    history = {email: [email in game for game in played] for email in emails}
    model = form_model(history, n)
    t = CARD_THRESHOLDS

    guests = {}
    names = {}
    for row in signups:  # ordered by time, so the latest nickname wins
        if row.get("is_guest") and row.get("added_by_email"):
            adder = row["added_by_email"].lower()
            guests[adder] = guests.get(adder, 0) + 1
        elif row.get("user_email"):
            names[row["user_email"].lower()] = row["nickname"]

    starts = {g["id"]: parse_game_time(g["start_time"]) for g in games}
    raw = {}
    for email, flags in history.items():
        speeds = [
            max(0.0, (parse_timestamp(game[email]["timestamp"]) - signup_opening_for(starts[game[email]["game_id"]])).total_seconds() / 60)
            for game in played if email in game
        ]
        active, best = _streaks(flags)
        raw[email] = {
            "games": sum(flags), "recent": sum(flags[-_RECENT:]),
            "active": active, "best": best, "tenure": n - flags.index(True),
            "speed": median(speeds), "guests": guests.get(email, 0),
            "year": sum(flags[-52:]),
        }
    if not raw:
        return {"cards": {}, "model": model["check"], "games": n}

    # Stats: 0..1 parts scaled to the group, then 30..99
    most_games = max(r["games"] for r in raw.values())
    best_streak = max(r["best"] for r in raw.values())
    most_active = max(r["active"] for r in raw.values())
    most_guests = max(max(r["guests"] for r in raw.values()), 3)
    faster = _rank_shares({e: -r["speed"] for e, r in raw.items()})
    parts = {
        email: {
            "FIZ": math.log1p(r["games"]) / math.log1p(most_games),
            "STR": r["recent"] / _RECENT,
            "OBR": r["tenure"] / n,
            "DRY": r["best"] / best_streak,
            "TEM": faster[email],
            "POD": r["guests"] / most_guests,
            # Not shown as a stat: the current run, rewarded in the rating
            "streak": r["active"] / max(most_active, 1),
        }
        for email, r in raw.items()
    }
    weights = {"FIZ": 0.30, "STR": 0.20, "streak": 0.15, "OBR": 0.12, "DRY": 0.10, "TEM": 0.08, "POD": 0.05}
    score = {email: sum(w * p[key] for key, w in weights.items()) for email, p in parts.items()}
    rank = _rank_shares(score)

    cards = {}
    for email, r in raw.items():
        # The rank is relative; experience gates keep a newcomer bronze even
        # while the history is short and a couple of games rank high
        cap = 64 if r["games"] < t["silver_games"] else 74 if r["games"] < t["gold_games"] else 95
        ovr = min(_ovr(rank[email], t), cap)
        cards[email] = {
            "email": email, "name": names.get(email, email.split("@")[0]),
            "ovr": ovr, "stats": {key: _scale(parts[email][key]) for key in STATS},
            "chance": model["chances"].get(email),
            "games": r["games"], "active_streak": r["active"], "best_streak": r["best"],
            "recent": r["recent"],
            "tier": "gold" if ovr >= 75 else "silver" if ovr >= 65 else "bronze",
        }

    # Special cards: legends first, then the year's six, then the in-form few
    for card in cards.values():
        if card["ovr"] >= t["legend"] and card["active_streak"] >= t["legend_streak"]:
            card["tier"] = "legend"
    year = sorted(
        (c for c in cards.values() if c["tier"] == "gold"),
        key=lambda c: (-raw[c["email"]]["year"], -c["ovr"]),
    )
    for card in year[:t["toty_size"]]:
        card["tier"] = "toty"
    in_form = sorted(
        (c for c in cards.values()
         # New players start bronze: in-form needs a silver or gold card
         if c["tier"] in ("silver", "gold") and c["active_streak"] >= t["in_form_streak"]
         and (c["chance"] or 0) >= t["in_form_chance"]),
        key=lambda c: (-(c["chance"] or 0), -c["active_streak"]),
    )
    for card in in_form[:t["in_form_max"]]:
        card["tier"] = "inform"
    return {"cards": cards, "model": model["check"], "games": n}


def rookie_card(email: str, name: str) -> dict:
    """Card of an account without any played game yet: bronze, base stats."""
    return {
        "email": email.lower(), "name": name, "ovr": 45, "tier": "bronze",
        "stats": {key: 30 for key in STATS}, "chance": None,
        "games": 0, "active_streak": 0, "best_streak": 0, "recent": 0,
    }


# ----- Loading ---------------------------------------------------------------

def _since(db: SupabaseDB):
    """First game the cards count: configured, or the first game with a signup
    from a Google account (the password era before it is left out)."""
    if CARDS_SINCE:
        return TIMEZONE.localize(datetime(CARDS_SINCE.year, CARDS_SINCE.month, CARDS_SINCE.day))
    rows = db.execute_query(
        "SELECT MIN(g.start_time) AS first FROM games g JOIN signups s ON s.game_id = g.id "
        "WHERE s.user_email IS NOT NULL AND s.is_guest = FALSE"
    )
    return rows[0]["first"] if rows and rows[0]["first"] else None


@st.cache_data(ttl=600, show_spinner=False)
def load_cards(_db: SupabaseDB) -> dict:
    """All cards (recomputed at most every 10 minutes), plus "since": the
    first game counted."""
    since = _since(_db)
    if since is None:
        return {"cards": {}, "model": None, "games": 0, "since": None}
    now = datetime.now(TIMEZONE)
    games = _db.execute_query(
        "SELECT id, start_time FROM games WHERE start_time >= %s AND start_time < %s ORDER BY start_time",
        (since, now)
    ) or []
    if not games:
        return {"cards": {}, "model": None, "games": 0, "since": None}
    signups = _db.execute_query(
        "SELECT s.game_id, s.nickname, s.user_email, s.is_guest, s.added_by_email, s.timestamp "
        "FROM signups s JOIN games g ON g.id = s.game_id "
        "WHERE g.start_time >= %s AND g.start_time < %s ORDER BY s.timestamp",
        (since, now)
    ) or []
    result = build_cards(games, signups, get_squads_between(_db, since, now))
    result["since"] = parse_game_time(games[0]["start_time"])
    return result
