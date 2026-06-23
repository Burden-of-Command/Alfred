#!/usr/bin/env python3
"""Coarse pressure test for ALFRED v0.6.

This is not a rules engine. It checks whether the scenario setups produce
plausible pressure across different high-level player priorities. The reported
core rate checks structured objectives only; Historical Mandates still require
human or full-rules testing.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "game/game.json").read_text())
SCENARIOS = DATA["scenarios"]
CRISES = DATA["crises"]
BY_GROUP = {
    group: [card for card in CRISES if card["group"] == group]
    for group in {card["group"] for card in CRISES}
}
WESSEX = [
    space["id"] for space in DATA["spaces"] if space["kind"] == "wessex"
]


@dataclass
class Result:
    survived: bool
    objective: bool
    score: int
    legitimacy: int
    obligation: int
    ready: int
    reform: int
    bases: int
    harvest_wealth: int
    retained_at_harvest: int


def clamp(value: int, low: int = 0, high: int = 7) -> int:
    return max(low, min(high, value))


def play(scenario: dict, style: str, rng: random.Random) -> Result:
    tracks = dict(scenario["tracks"])
    readiness = dict(scenario["readiness"])
    burhs = set(scenario["burhs"])
    armies = {
        army: {"space": setup[0], "strength": setup[1]}
        for army, setup in scenario["armies"].items()
    }
    bases: set[str] = set()
    wins = 0
    negotiated = False
    settled = False
    service = 0
    field_homes: set[str] = set()
    harvest_wealth = 0
    retained_at_harvest = 0
    priority_ranks = {
        "martial": ["P02", "P08", "P01", "P07", "P05", "P06", "P03", "P04"],
        "adaptive": ["P01", "P05", "P07", "P06", "P08", "P03", "P04", "P02"],
        "reform": ["P03", "P04", "P06", "P07", "P05", "P01", "P08", "P02"],
    }
    offers = rng.sample(DATA["priorities"], 2)
    priority = min(
        offers, key=lambda card: priority_ranks[style].index(card["id"])
    )["id"]
    priority_used = False

    for round_no, group in enumerate(scenario["groups"]):
        field_at_round_start = bool(field_homes)
        crisis = rng.choice(BY_GROUP[group])
        active = crisis["army"]
        if active not in armies:
            armies[active] = {
                "space": DATA["armies"][active]["entry"],
                "strength": 2,
            }

        # The strategic styles spend their two-order budget differently.
        lowest = min(tracks["legitimacy"], tracks["obligation"])
        military_bias = {"martial": 0.72, "adaptive": 0.57, "reform": 0.46}[style]
        fight = rng.random() < military_bias and armies[active]["strength"] >= 2

        # Council cards are independent of the two Basic Orders. Even a
        # military posture sometimes uses the KINGDOM half while campaigning.
        kingdom_bias = {"martial": 0.24, "adaptive": 0.43, "reform": 0.62}[style]
        if tracks["reform"] < 6 and rng.random() < kingdom_bias:
            if tracks["wealth"] > 0 and rng.random() < 0.65:
                tracks["wealth"] -= 1
            tracks["reform"] = clamp(tracks["reform"] + 1, 0, 6)
            if not priority_used and priority == "P04":
                tracks["obligation"] = clamp(tracks["obligation"] + 1)
                priority_used = True

        if fight:
            chosen: list[str] = []
            ready_regions = [
                region for region in WESSEX
                if readiness[region] == 2 and region not in field_homes
            ]
            if not field_homes:
                chosen = rng.sample(ready_regions, min(3, len(ready_regions)))
            elif len(field_homes) < 3 and ready_regions and rng.random() < 0.45:
                chosen = [rng.choice(ready_regions)]
            if chosen:
                for region in chosen:
                    readiness[region] = 1
                    field_homes.add(region)
                service = max(1, service)
            saxon = 2 + len(field_homes) + rng.randint(1, 6)
            if not priority_used and priority in {"P02", "P08", "P07"}:
                saxon += 2 if priority in {"P02", "P08"} else 1
                priority_used = True
            viking = armies[active]["strength"] + rng.randint(1, 6)
            if armies[active]["space"] in bases:
                viking += 1
            margin = saxon - viking
            if margin >= 1:
                wins += 1
                armies[active]["strength"] = max(
                    0, armies[active]["strength"] - (2 if margin >= 3 else 1)
                )
                bases.discard(armies[active]["space"])
                tracks["legitimacy"] = clamp(tracks["legitimacy"] + int(margin >= 3))
                negotiation_limit = 3 if scenario["id"] == "S03" else 2
                negotiation_chance = 0.68 if scenario["id"] == "S03" else 0.45
                if not priority_used and priority == "P05":
                    negotiation_chance += 0.25
                    priority_used = True
                if (
                    armies[active]["strength"] <= negotiation_limit
                    and rng.random() < negotiation_chance
                ):
                    negotiated = True
                    settled = settled or rng.random() < 0.35
            elif margin <= -3:
                tracks["legitimacy"] -= 1
                if field_homes:
                    lost_home = rng.choice(list(field_homes))
                    readiness[lost_home] = 0
                    field_homes.remove(lost_home)
        else:
            stewarded = False
            damaged = [
                region for region in WESSEX
                if readiness[region] < 2
                and region not in bases
                and region not in field_homes
            ]
            stewardship_bias = {"martial": 0.28, "adaptive": 0.58, "reform": 0.72}[style]
            if damaged and rng.random() < stewardship_bias:
                target = min(damaged, key=lambda region: readiness[region])
                readiness[target] += 1
                stewarded = True
                if readiness[target] == 2:
                    tracks["wealth"] += 1
                if not priority_used and priority == "P06":
                    others = [region for region in damaged if region != target]
                    if others:
                        readiness[min(others, key=lambda region: readiness[region])] += 1
                    priority_used = True
            political_bias = {"martial": 0.30, "adaptive": 0.56, "reform": 0.76}[style]
            if rng.random() < political_bias and lowest > 1:
                candidates = [
                    r for r in WESSEX
                    if r not in burhs and any(
                        s["id"] == r and s.get("burh") for s in DATA["spaces"]
                    )
                ]
                build_burh = (
                    candidates
                    and tracks["wealth"] >= (
                        1 if not priority_used and priority == "P03" else 2
                    )
                    and len(burhs) < scenario["objective"].get("active_burhs", 2)
                )
                if build_burh:
                    cost = 2
                    if not priority_used and priority == "P03":
                        cost = 1
                        priority_used = True
                    tracks["wealth"] -= cost
                    tracks["reform"] = clamp(tracks["reform"] + 1, 0, 6)
                    burhs.add(rng.choice(candidates))
                elif not stewarded:
                    tracks["wealth"] = clamp(tracks["wealth"] + 1)
            elif not stewarded:
                tracks["wealth"] = clamp(tracks["wealth"] + 1)
                tracks["obligation"] = clamp(tracks["obligation"] + int(service == 0))

        # Abstract the active Intent as pressure against an exposed region.
        exposed = [
            region for region in WESSEX
            if readiness[region] > 0 and region not in burhs
        ]
        pressure = (
            0.43
            + armies[active]["strength"] * 0.045
            + (scenario["difficulty"] - 1) * 0.045
        )
        if exposed and rng.random() < pressure:
            target = rng.choice(exposed)
            prevent_raid = (
                not priority_used
                and priority == "P01"
                and tracks["obligation"] > 2
            )
            if prevent_raid:
                tracks["obligation"] -= 1
                priority_used = True
            else:
                readiness[target] -= 1
            tracks["wealth"] -= 1
            if not prevent_raid and readiness[target] == 0:
                tracks["obligation"] -= 1
            if crisis["intent"] == "seek_base" and rng.random() < 0.55:
                bases.add(target)
        elif crisis["intent"] == "join":
            armies[active]["strength"] = min(6, armies[active]["strength"] + 1)

        if round_no + 1 in scenario.get("harvest_rounds", []):
            keep_chance = {"martial": 0.68, "adaptive": 0.42, "reform": 0.22}[style]
            for region in list(field_homes):
                if rng.random() < keep_chance:
                    readiness[region] = max(0, readiness[region] - 1)
                    retained_at_harvest += 1
                else:
                    field_homes.remove(region)
            if not field_homes:
                service = 0
            ready_at_harvest = sum(
                1 for region in WESSEX if readiness[region] == 2
            )
            yield_amount = 2 if ready_at_harvest >= 5 else int(ready_at_harvest >= 3)
            tracks["wealth"] += yield_amount
            harvest_wealth += yield_amount

        if field_homes and field_at_round_start:
            service += 1
            release_chance = {"martial": 0.42, "adaptive": 0.67, "reform": 0.82}[style]
            if service >= 3 and rng.random() >= release_chance:
                if field_homes:
                    readiness[rng.choice(list(field_homes))] = 0
                tracks["obligation"] -= 1
                service = 1
            elif service >= 3 or rng.random() < release_chance * 0.35:
                service = 0
                field_homes.clear()

        # Recover at most two safe regions; release improves which regions are
        # eligible, but recovery never becomes automatic mass healing.
        recoverable = [
            region for region, state in readiness.items()
            if state < 2 and region not in bases
        ]
        rng.shuffle(recoverable)
        recovery_limit = 1
        for region in recoverable[:recovery_limit]:
            if rng.random() < (0.62 if field_homes else 0.88):
                readiness[region] += 1

        tracks["legitimacy"] = clamp(tracks["legitimacy"])
        tracks["obligation"] = clamp(tracks["obligation"])
        tracks["wealth"] = clamp(tracks["wealth"])
        if tracks["legitimacy"] == 0 or tracks["obligation"] == 0:
            break

        # Later rounds broaden the war even if their named Army began inactive.
        if round_no >= 5 and rng.random() < 0.18:
            tracks["obligation"] -= 1

    ready = sum(1 for region in WESSEX if readiness[region] == 2)
    objective_spec = scenario["objective"]
    objective = (
        wins >= objective_spec.get("wins", 0)
        and ready >= objective_spec.get("min_ready", 0)
        and tracks["reform"] >= objective_spec.get("min_reform", 0)
        and tracks["legitimacy"] >= objective_spec.get("min_legitimacy", 0)
        and tracks["obligation"] >= objective_spec.get("min_obligation", 0)
        and len(bases) <= objective_spec.get("max_bases", 99)
        and (
            "guthrum_max" not in objective_spec
            or armies.get("guthrum", {"strength": 9})["strength"]
            <= objective_spec["guthrum_max"]
        )
        and (not objective_spec.get("successful_negotiation") or negotiated)
        and (not objective_spec.get("london_clear") or "london" not in bases)
        and len(burhs) >= objective_spec.get("active_burhs", 0)
    )
    survived = tracks["legitimacy"] > 0 and tracks["obligation"] > 0
    score = (
        tracks["legitimacy"] + tracks["obligation"] + tracks["wealth"]
        + ready + len(burhs) - len(bases) + int(settled)
    )
    return Result(
        survived, objective and survived, score, tracks["legitimacy"],
        tracks["obligation"], ready, tracks["reform"], len(bases),
        harvest_wealth, retained_at_harvest
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=871)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    print(f"ALFRED v{DATA['version']} coarse simulation ({args.games} games/style)")
    for scenario in SCENARIOS:
        print(f"\n{scenario['id']} {scenario['name']}")
        for style in ("martial", "adaptive", "reform"):
            results = [play(scenario, style, rng) for _ in range(args.games)]
            survival = sum(r.survived for r in results) / args.games
            core = sum(r.objective for r in results) / args.games
            scores = [r.score for r in results]
            print(
                f"  {style:8} survive {survival:5.1%}  "
                f"core {core:5.1%}  "
                f"score {statistics.mean(scores):4.1f}  "
                f"ready {statistics.mean(r.ready for r in results):3.1f}  "
                f"reform {statistics.mean(r.reform for r in results):3.1f}  "
                f"harvest {statistics.mean(r.harvest_wealth for r in results):3.1f}"
            )


if __name__ == "__main__":
    main()
