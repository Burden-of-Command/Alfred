#!/usr/bin/env python3
"""Build Alfred poker cards and duplex-ready SVG print sheets."""
from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path
from textwrap import wrap

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "game/game.json").read_text())
OUT = ROOT / "dist/cards"
SHEETS = ROOT / "dist/print-sheets"
BACKS = ROOT / "dist/card-backs"

PALETTE = {
    "scenario": ("#e9e0ca", "#202522", "#7b2638"),
    "priority": ("#24352f", "#f0e8d5", "#b7a35a"),
    "command": ("#17272d", "#f0e8d5", "#c49a45"),
    "crisis": ("#29231f", "#f0e8d5", "#a24b36"),
}

INTENT_LABELS = {
    "draw_fyrd": "DRAW THE FYRD",
    "join": "JOIN HOSTS",
    "raid": "RAID",
    "seek_base": "SEEK CAMP",
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def text_lines(text: str, width: int, limit: int) -> list[str]:
    return wrap(text, width=width, break_long_words=False)[:limit]


def tspans(items: list[str], x: int, gap: int) -> str:
    return "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else gap}">{html.escape(item)}</tspan>'
        for index, item in enumerate(items)
    )


def readiness_summary(card: dict) -> str:
    names = {
        "devon": "De", "somerset": "So", "dorset": "Do", "hampshire": "Ha",
        "wiltshire": "Wi", "berkshire": "Be", "kent": "Ke",
        "thames_valley": "Th", "london": "Lo", "mercia": "Me",
    }
    states = "XDR"
    return " ".join(f"{names[key]}{states[value]}" for key, value in card["readiness"].items())


def objective_summary(objective: dict) -> str:
    labels = {
        "wins": "battle wins", "min_ready": "Ready Wessex regions",
        "min_legitimacy": "Legitimacy", "min_obligation": "Obligation",
        "min_reform": "Reform", "active_burhs": "active Burhs",
        "max_bases": "fortified camps at most",
        "guthrum_max": "Guthrum Strength at most",
        "successful_negotiation": "successful negotiation",
        "london_clear": "London clear",
    }
    bits = []
    for key, value in objective.items():
        label = labels.get(key, key.replace("_", " "))
        if key.startswith("min_"):
            bits.append(f"{label} {value}+")
        elif key.startswith("max_") or key == "guthrum_max":
            bits.append(f"{label} {value}")
        elif value == 1 and key in {"successful_negotiation", "london_clear"}:
            bits.append(label)
        else:
            bits.append(f"{value} {label}")
    return "; ".join(bits)


def card_svg(kind: str, card: dict) -> str:
    bg, ink, accent = PALETTE[kind]
    if kind == "command":
        kicker = f'{card["id"]}  ROYAL COUNSEL / {card["tag"].upper()}'
        upper_label, lower_label = "COMMAND", "KINGDOM"
        upper, lower = card["command"], card["kingdom"]
        footer = "THE KINGDOM IS THE ARMY"
        width, limit, size, gap = 41, 7, 27, 34
    elif kind == "priority":
        kicker = f'{card["id"]}  ROYAL PRIORITY / {card["tag"].upper()}'
        upper_label, lower_label = "ROYAL RESOLVE", "LEGACY"
        upper, lower = card["resolve"], card["legacy"]
        footer = "ONE RESOLVE. ONE AMBITION. NO EXTRA PHASE."
        width, limit, size, gap = 41, 7, 27, 34
    elif kind == "crisis":
        army = DATA["armies"][card["army"]]["name"].upper()
        kicker = f'{card["id"]}  CRISIS / GROUP {card["group"]}'
        upper_label = "ARRIVAL"
        lower_label = f'{army}: {INTENT_LABELS[card["intent"]]}'
        upper, lower = card["arrival"], card["design"]
        footer = "READ THE PURPOSE. CHOOSE WHAT MAY BE LEFT WEAK."
        width, limit, size, gap = 41, 7, 27, 34
    else:
        kicker = f'{card["id"]}  SCENARIO / DIFFICULTY {card["difficulty"]}'
        upper_label, lower_label = card["years"], f'{card["rounds"]} ROUNDS'
        tracks = card["tracks"]
        armies = ", ".join(
            f'{DATA["armies"][key]["name"]} {value[1]} at '
            f'{next(space["name"] for space in DATA["spaces"] if space["id"] == value[0])}'
            for key, value in card["armies"].items()
        )
        upper = card["mandate"]["text"]
        lower = (
            f'Start: Legitimacy {tracks["legitimacy"]}, Obligation {tracks["obligation"]}, '
            f'Wealth {tracks["wealth"]}, Reform {tracks["reform"]}. '
            f'Harvest rounds: {", ".join(map(str, card.get("harvest_rounds", [])))}. '
            f'Readiness: {readiness_summary(card)}. Active Burhs: '
            f'{", ".join(card["burhs"]) or "none"}. Armies: {armies}. '
            f'Objective: {objective_summary(card["objective"])}.'
        )
        footer = "SURVIVE THE WAR. LEAVE A KINGDOM ABLE TO ANSWER."
        width, limit, size, gap = 51, 12, 19, 24

    title_size = 42 if len(card["name"]) < 23 else 34
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="{bg}"/>
<rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="{accent}" stroke-width="4"/>
<path d="M55 165H695M55 550H695M55 914H695" stroke="{accent}" stroke-width="2"/>
<path d="M30 80Q80 30 130 80T230 80M520 80Q570 30 620 80T720 80" fill="none" stroke="{accent}" stroke-width="2" opacity=".7"/>
<text x="55" y="78" fill="{accent}" font-family="Arial,sans-serif" font-size="18" font-weight="bold" letter-spacing="2">{html.escape(kicker)}</text>
<text x="55" y="137" fill="{ink}" font-family="Georgia,serif" font-size="{title_size}" font-weight="bold">{html.escape(card["name"])}</text>
<text x="55" y="215" fill="{accent}" font-family="Arial,sans-serif" font-size="20" font-weight="bold" letter-spacing="3">{html.escape(upper_label)}</text>
<text x="55" y="270" fill="{ink}" font-family="Georgia,serif" font-size="27">{tspans(text_lines(upper, 41, 7), 55, 34)}</text>
<text x="55" y="602" fill="{accent}" font-family="Arial,sans-serif" font-size="20" font-weight="bold" letter-spacing="3">{html.escape(lower_label)}</text>
<text x="55" y="657" fill="{ink}" font-family="Georgia,serif" font-size="{size}">{tspans(text_lines(lower, width, limit), 55, gap)}</text>
<text x="375" y="925" text-anchor="middle" fill="{accent}" font-family="Arial,sans-serif" font-size="13" font-weight="bold" letter-spacing="2">{footer}</text>
<path d="M320 965C320 925 430 925 430 965S320 1005 320 965M350 940C390 1000 405 925 375 992" fill="none" stroke="{accent}" stroke-width="4"/>
</svg>'''


def back_svg(kind: str) -> str:
    bg, ink, accent = PALETTE[kind]
    label = {
        "command": "ROYAL COUNSEL",
        "crisis": "DANISH PURPOSE",
        "priority": "ROYAL PRIORITY",
        "scenario": "HISTORICAL BURDEN",
    }[kind]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="{bg}"/>
<rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="{accent}" stroke-width="4"/>
<rect x="48" y="48" width="654" height="954" rx="20" fill="none" stroke="{accent}" stroke-width="1"/>
<path d="M155 505C155 365 300 300 375 410C450 300 595 365 595 505C595 645 450 710 375 600C300 710 155 645 155 505Z" fill="none" stroke="{accent}" stroke-width="5"/>
<path d="M235 505C235 430 315 390 375 455C435 390 515 430 515 505C515 580 435 620 375 555C315 620 235 580 235 505Z" fill="none" stroke="{accent}" stroke-width="3"/>
<text x="375" y="535" text-anchor="middle" fill="{ink}" font-family="Georgia,serif" font-size="102">A</text>
<text x="375" y="835" text-anchor="middle" fill="{ink}" font-family="Georgia,serif" font-size="38" font-weight="bold">ALFRED</text>
<text x="375" y="885" text-anchor="middle" fill="{accent}" font-family="Arial,sans-serif" font-size="18" font-weight="bold" letter-spacing="4">{label}</text>
<text x="375" y="945" text-anchor="middle" fill="{accent}" font-family="Arial,sans-serif" font-size="12" font-weight="bold" letter-spacing="2">THE BURDEN OF COMMAND SERIES · VOLUME II</text>
</svg>'''


def embedded(path: Path, x: int, y: int) -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<image href="data:image/svg+xml;base64,{data}" x="{x}" y="{y}" width="750" height="1050"/>'


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    BACKS.mkdir(parents=True, exist_ok=True)
    for folder in (OUT, SHEETS, BACKS):
        for path in folder.glob("*.svg"):
            path.unlink()
    back_paths = {}
    for kind in PALETTE:
        path = BACKS / f"{kind}-back.svg"
        path.write_text(back_svg(kind))
        back_paths[kind] = path

    cards = []
    for kind, source in (
        ("scenario", DATA["scenarios"]),
        ("priority", DATA["priorities"]),
        ("command", DATA["commands"]),
        ("crisis", DATA["crises"]),
    ):
        for card in source:
            path = OUT / f'{card["id"]}-{slug(card["name"])}.svg'
            path.write_text(card_svg(kind, card))
            cards.append((kind, path))

    for offset in range(0, len(cards), 9):
        chunk = cards[offset:offset + 9]
        fronts, backs = [], []
        for index, (kind, path) in enumerate(chunk):
            col, row = index % 3, index // 3
            fronts.append(embedded(path, col * 750, row * 1050))
            backs.append(embedded(back_paths[kind], (2 - col) * 750, row * 1050))
        number = offset // 9 + 1
        root = '<svg xmlns="http://www.w3.org/2000/svg" width="7.5in" height="10.5in" viewBox="0 0 2250 3150">'
        (SHEETS / f"sheet-{number}-front.svg").write_text(root + "".join(fronts) + "</svg>")
        (SHEETS / f"sheet-{number}-back.svg").write_text(root + "".join(backs) + "</svg>")
    print(f"Built {len(cards)} cards and {(len(cards) + 8) // 9} duplex sheet pairs.")


if __name__ == "__main__":
    main()
