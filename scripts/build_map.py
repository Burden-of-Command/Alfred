#!/usr/bin/env python3
"""Build Alfred campaign mat, reference card, and prototype markers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"

POSITIONS = {
    "devon": (180, 540), "somerset": (390, 470), "dorset": (430, 680),
    "wiltshire": (640, 500), "hampshire": (690, 700), "berkshire": (820, 400),
    "kent": (1130, 680), "thames_valley": (1010, 330), "london": (1190, 360),
    "mercia": (760, 190),
}
NAMES = {
    "devon": ("EXETER", ""), "somerset": ("ATHELNEY", ""),
    "dorset": ("WAREHAM", ""), "wiltshire": ("WILTON", ""),
    "hampshire": ("WINCHESTER", ""),
    "berkshire": ("READING", ""), "kent": ("KENT", ""),
    "thames_valley": ("WALLINGFORD", ""),
    "london": ("LONDON", ""), "mercia": ("ENGLISH", "MERCIA"),
}
EDGES = [
    ("devon", "somerset"), ("devon", "dorset"), ("somerset", "dorset"),
    ("somerset", "wiltshire"), ("dorset", "wiltshire"), ("dorset", "hampshire"),
    ("wiltshire", "hampshire"), ("wiltshire", "berkshire"),
    ("hampshire", "berkshire"), ("hampshire", "kent"), ("berkshire", "thames_valley"),
    ("berkshire", "mercia"), ("kent", "london"), ("thames_valley", "london"),
    ("thames_valley", "mercia"), ("london", "mercia"),
]


def region(key: str) -> str:
    x, y = POSITIONS[key]
    burh = key in {"somerset", "hampshire", "berkshire", "kent", "london", "mercia"}
    shield = (
        f'<path d="M{x + 75} {y - 42}l18 8v20c0 16-9 27-18 33-9-6-18-17-18-33v-20Z" class="burh"/>'
        if burh else ""
    )
    states = "".join(
        f'<circle cx="{x - 48 + index * 48}" cy="{y + 52}" r="17" class="state"/>'
        f'<text x="{x - 48 + index * 48}" y="{y + 57}" text-anchor="middle" class="tiny">{label}</text>'
        for index, label in enumerate(("X", "D", "R"))
    )
    return f'''<path d="M{x-100} {y-55}Q{x} {y-80} {x+100} {y-55}L{x+92} {y+70}Q{x} {y+88} {x-92} {y+70}Z" class="region"/>
<text x="{x}" y="{y-20}" text-anchor="middle" class="place">{NAMES[key][0]}</text>
<text x="{x}" y="{y+2}" text-anchor="middle" class="tiny">{NAMES[key][1]}</text>
<text x="{x}" y="{y+25}" text-anchor="middle" class="small">FYRD / READINESS</text>{states}{shield}'''


def track(label: str, y: int, maximum: int = 7) -> str:
    cells = []
    for value in range(maximum + 1):
        x = 1080 + value * 58
        cells.append(
            f'<rect x="{x}" y="{y}" width="54" height="42" rx="4" class="track"/>'
            f'<text x="{x+27}" y="{y+28}" text-anchor="middle" class="n">{value}</text>'
        )
    return f'<text x="1050" y="{y+29}" text-anchor="end" class="label">{label}</text>' + "".join(cells)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    links = "".join(
        f'<path d="M{POSITIONS[a][0]} {POSITIONS[a][1]}L{POSITIONS[b][0]} {POSITIONS[b][1]}" class="road"/>'
        for a, b in EDGES
    )
    nodes = "".join(region(key) for key in POSITIONS)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="16.54in" height="11.69in" viewBox="0 0 1654 1169">
<style>
.title{{font:700 50px Georgia;fill:#19272b}} .sub{{font:18px Arial;letter-spacing:4px;fill:#7b2638}}
.place{{font:700 17px Georgia;fill:#19272b}} .small{{font:700 11px Arial;letter-spacing:2px;fill:#7b2638}}
.tiny{{font:12px Arial;fill:#19272b}} .label{{font:700 16px Arial;fill:#19272b}} .n{{font:15px Georgia;fill:#19272b}}
.region{{fill:#e9e0ca;stroke:#19272b;stroke-width:3}} .road{{stroke:#7e6a4b;stroke-width:7;opacity:.75}}
.river{{fill:none;stroke:#557e8a;stroke-width:18;opacity:.55}} .coast{{fill:#a7bec1;opacity:.42}}
.state,.track{{fill:#f3ead6;stroke:#7b2638;stroke-width:2}} .burh{{fill:#c49a45;stroke:#19272b;stroke-width:2}}
</style>
<rect width="1654" height="1169" fill="#d9cfb8"/>
<path d="M0 760Q250 700 410 780T800 800T1250 750T1654 700V1169H0Z" class="coast"/>
<path d="M1510 245Q1300 300 1190 360T1010 330T820 400" class="river"/>
<rect x="24" y="24" width="1606" height="1121" fill="none" stroke="#7b2638" stroke-width="4"/>
<text x="72" y="88" class="title">ALFRED</text>
<text x="74" y="126" class="sub">THE BURDEN OF WESSEX</text>
<text x="1582" y="88" text-anchor="end" class="small">THE BURDEN OF COMMAND SERIES · VOLUME II</text>
<g>{links}</g><g>{nodes}</g>
<text x="1320" y="255" class="small" fill="#315b67">THAMES / RIVER APPROACH</text>
<rect x="55" y="865" width="900" height="225" rx="12" fill="#eee5d1" stroke="#19272b" stroke-width="3"/>
<text x="85" y="910" class="label">DANISH HOST PURPOSES</text>
<text x="85" y="950" class="place">RAID</text><text x="245" y="950" class="small">WEALTH / READINESS</text>
<text x="85" y="990" class="place">SEEK CAMP</text><text x="245" y="990" class="small">BURH / ROYAL SEAT</text>
<text x="520" y="950" class="place">DRAW FYRD</text><text x="680" y="950" class="small">READY REGION</text>
<text x="520" y="990" class="place">JOIN</text><text x="680" y="990" class="small">STRONGEST ARMY</text>
<text x="85" y="1045" class="small">X EXHAUSTED · D DEPLETED · R READY · SHIELD = BURH SITE</text>
<g>{track("LEGITIMACY", 835)}{track("OBLIGATION", 885)}{track("WEALTH", 935)}{track("REFORM", 985, 6)}{track("SERVICE", 1035, 3)}</g>
<text x="72" y="1135" class="small">CALL THE FYRD. BEAR THE SERVICE. RELEASE THE LAND.</text>
<text x="1582" y="1135" text-anchor="end" class="tiny">PROTOTYPE 0.6</text>
</svg>'''
    (OUT / "Alfred-Campaign-Mat.svg").write_text(svg)

    aid = '''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="#17272d"/><rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="#c49a45" stroke-width="4"/>
<text x="55" y="90" fill="#f0e8d5" font-family="Georgia" font-size="42" font-weight="bold">ROUND</text>
<text x="55" y="140" fill="#c49a45" font-family="Arial" font-size="16" letter-spacing="2">INTELLIGENCE / COUNCIL / ORDERS / DESIGN / SERVICE</text>
<path d="M55 170H695" stroke="#c49a45"/>
<text x="55" y="225" fill="#c49a45" font-family="Arial" font-size="20" font-weight="bold">CHOOSE TWO DIFFERENT ORDERS</text>
<text x="55" y="278" fill="#f0e8d5" font-family="Georgia" font-size="22">
<tspan x="55">Muster: local + two adjacent Ready fyrds.</tspan><tspan x="55" dy="34">March: Alfred's force one connection.</tspan>
<tspan x="55" dy="34">Confront: Delay, Drive Off, Force, Blockade.</tspan><tspan x="55" dy="34">Fortify: 2 Wealth + Ready to activate Burh.</tspan>
<tspan x="55" dy="34">Negotiate: pay 1 Wealth and test terms.</tspan><tspan x="55" dy="34">Steward: release fyrds, then recover one.</tspan></text>
<path d="M55 510H695" stroke="#c49a45"/>
<text x="55" y="558" fill="#c49a45" font-family="Arial" font-size="20" font-weight="bold">SERVICE AND HARVEST</text>
<text x="55" y="606" fill="#f0e8d5" font-family="Georgia" font-size="21">
<tspan x="55">Ready musters → Depleted.</tspan><tspan x="55" dy="32">Emergency: Depleted → Exhausted,</tspan>
<tspan x="55" dy="28">and lose 1 Obligation.</tspan><tspan x="55" dy="40">At Service 3:</tspan>
<tspan x="55" dy="32">RELEASE all fyrds and reset Service; or</tspan><tspan x="55" dy="32">RETAIN: exhaust one home, -1 Obligation,</tspan>
<tspan x="55" dy="28">then set Service to 1.</tspan><tspan x="55" dy="40">HARVEST: release each fyrd or deplete home.</tspan>
<tspan x="55" dy="28">5 Ready = +2 Wealth; 3 Ready = +1.</tspan></text>
<text x="375" y="1000" text-anchor="middle" fill="#c49a45" font-family="Arial" font-size="13" letter-spacing="2">THE KINGDOM IS THE ARMY</text>
</svg>'''
    (OUT / "Alfred-Order-Reference.svg").write_text(aid)

    armies = [("G", "GUTHRUM", "#704132"), ("S", "SEABORNE", "#385766"),
              ("H", "HÆSTEN", "#563b55"), ("T", "THAMES", "#344b3d")]
    groups = []
    for index, (letter, name, color) in enumerate(armies):
        x = index * 180
        groups.append(f'''<g transform="translate({x} 0)"><rect x="8" y="8" width="164" height="164" rx="18" fill="{color}" stroke="#d6bd79" stroke-width="6"/>
<text x="90" y="91" text-anchor="middle" fill="#fff8e8" font-family="Georgia" font-size="72" font-weight="bold">{letter}</text>
<text x="90" y="137" text-anchor="middle" fill="#d6bd79" font-family="Arial" font-size="13" font-weight="bold" letter-spacing="2">{name}</text></g>''')
    (OUT / "Alfred-Army-Markers.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="7.2in" height="1.8in" viewBox="0 0 720 180">'
        '<rect width="720" height="180" fill="#e9e0ca"/>' + "".join(groups) + "</svg>"
    )
    print("Built campaign mat, order reference, and Danish Host markers.")


if __name__ == "__main__":
    main()
