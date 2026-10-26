"""
Squad building: team layouts from game_consts.yaml, the reserve bench and
random filling of the slots the squad setter leaves open.
"""

import random

from src.game_config import TEAM_CONFIGS

# Team counts the builder offers (e.g. [2, 3]).
TEAM_COUNTS = sorted({config["teams"] for config in TEAM_CONFIGS.values()})
# The biggest game there can be (e.g. 18 for 3 x 6). Until squads are saved,
# only signups beyond it are shown as reserves - below it more players are
# still welcome, as they can make a bigger format.
MAX_PLAYERS = max(TEAM_CONFIGS)
# Display order of shirt colours: as listed in the lineup with the most teams.
_COLOR_ORDER = [
    color
    for players in sorted(TEAM_CONFIGS, key=lambda n: -TEAM_CONFIGS[n]["teams"])
    for color in TEAM_CONFIGS[players]["colors"]
]


def team_colors(team_count: int) -> list:
    """Shirt colours of a game with this many teams (from the smallest
    configured lineup with that team count)."""
    for players in sorted(TEAM_CONFIGS):
        if TEAM_CONFIGS[players]["teams"] == team_count:
            return list(TEAM_CONFIGS[players]["colors"])
    return []


def _lineups(team_count: int) -> list:
    return [n for n, config in TEAM_CONFIGS.items() if config["teams"] == team_count]


def minimum(team_count: int) -> int:
    """Fewest players a game with this many teams needs: its smallest
    configured lineup."""
    return min(_lineups(team_count))


def capacity(team_count: int) -> int:
    """Most players a game with this many teams takes: its largest configured
    lineup. Later signups wait on the bench."""
    return max(_lineups(team_count))


def default_team_count(players_count: int) -> int:
    """The most teams there are enough players for (e.g. 15-17 players: two
    teams and a bench, as three teams need 18); the smallest format when there
    are too few even for that."""
    enough = [k for k in TEAM_COUNTS if minimum(k) <= players_count]
    return max(enough) if enough else min(TEAM_COUNTS)


def split_bench(players: list, team_count: int):
    """(playing, bench): the first `capacity` signups play, the latest ones
    wait on the bench."""
    limit = capacity(team_count)
    return players[:limit], players[limit:]


def team_targets(players_count: int, team_count: int) -> list:
    """Target size of each team: the configured split when there is one,
    otherwise as even as possible (earlier teams take the extra player)."""
    config = TEAM_CONFIGS.get(players_count)
    if config and config["teams"] == team_count:
        return list(config["players_per_team"])
    base, extra = divmod(players_count, team_count)
    return [base + (1 if i < extra else 0) for i in range(team_count)]


def fill_randomly(teams: dict, pool: list, targets: list) -> dict:
    """Shuffle `pool` into `teams` ({color: [players]}), each time topping up
    the team furthest below its target (ties broken at random). Players already
    in the teams stay where they are."""
    teams = {color: list(players) for color, players in teams.items()}
    target = dict(zip(teams, targets))
    rest = list(pool)
    random.shuffle(rest)
    for player in rest:
        colors = list(teams)
        random.shuffle(colors)
        color = max(colors, key=lambda c: target[c] - len(teams[c]))
        teams[color].append(player)
    return teams


def sort_teams(teams: dict) -> dict:
    """Teams in the configured shirt-colour order (unknown colours last)."""
    def rank(color):
        return _COLOR_ORDER.index(color) if color in _COLOR_ORDER else len(_COLOR_ORDER)
    return {color: teams[color] for color in sorted(teams, key=rank)}


def lineups_with_bench(teams: dict, players: list):
    """Saved squads checked against the current signup list.

    teams: {color: [names]} as saved; players: nicknames on the list now, in
    signup order. Everyone on the list but in no team is a reserve, queued by
    signup time. A saved player who left the list frees their slot for the
    first reserve. Returns ({color: [slot]}, bench): a slot is {"name"} for a
    player on the pitch, plus "sub_for" when they took over a freed slot, or
    {"name", "out": True} for a freed slot no reserve could fill; bench holds
    the remaining reserves in order.
    """
    on_list = set(players)
    assigned = {name for names in teams.values() for name in names}
    reserves = [p for p in players if p not in assigned]
    lineups = {}
    for color, names in teams.items():
        slots = []
        for name in names:
            if name in on_list:
                slots.append({"name": name})
            elif reserves:
                slots.append({"name": reserves.pop(0), "sub_for": name})
            else:
                slots.append({"name": name, "out": True})
        lineups[color] = slots
    return lineups, reserves


def bench_for(players: list, teams: dict) -> list:
    """Reserves of a game in queue order: per the saved squads when there are
    any, otherwise everyone beyond the biggest game (MAX_PLAYERS)."""
    if teams:
        return lineups_with_bench(teams, players)[1]
    return players[MAX_PLAYERS:]
