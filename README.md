# ALFRED: The Burden of Wessex

**Volume II of The Burden of Command Series**

A compact solo operational wargame about Alfred of Wessex, regional military
obligation, fortified places, and survival against mobile Viking armies,
c. 871-899.

You are Alfred. Your armies do not wait permanently on the map. They must be
called from the regions that sustain them, and every muster leaves somewhere
weaker. A victory won by exhausting Wessex may only prepare the next defeat.

Version 0.6 is a complete print-and-play prototype. It includes the operational
engine, canonical data, eight scenarios, a coarse simulation harness, key art,
cards, campaign mat, markers, and duplex print sheets.

## Core Proposition

The military strength of Wessex comes **from the map**.

Each region has a simple readiness state. Mustering its fyrd creates field
strength but depletes the region. Continued service, defeat, and emergency
levies can exhaust it. Alfred must decide where to draw men from, how long to
keep them in the field, and which region can survive being left vulnerable.

This is the volume's defining mechanism and the main distinction from
*IMPERATOR*, whose professional legions persist and move around the frontier.

## Player Experience

- See Danish hosts spreading across a compact geographic map.
- Assemble temporary armies from nearby and distant regions.
- Decide whether to intercept, shadow, negotiate, fortify, or risk battle.
- Protect settlements without trying to defend every place.
- Build a defensive system while surviving the immediate campaign.
- Experience defeat, recovery, reform, and political consolidation.
- Finish in roughly 45-75 minutes with little opposition bookkeeping.

## Series Identity

Every volume in **The Burden of Command** should contain:

- one historical ruler under simultaneous military and political pressure;
- a compact geographic map with meaningful force movement;
- an opposition system that creates plans without requiring the player to run
  a second side;
- difficult command decisions made before uncertain resolution;
- historical events that constrain rather than dictate play;
- several focused scenarios and one broader campaign;
- a restrained component count and a concise rules burden;
- an ending that judges how the ruler governed, not only what was conquered.

The series does **not** require identical military systems. Familiarity should
come from the design philosophy, presentation, and decision quality.

## Volume II Identity

| IMPERATOR | ALFRED |
| --- | --- |
| Permanent professional legions | Temporary regional fyrds |
| Frontier corridors | Rivers, roads, coasts, and defended regions |
| Barbarian coalition pressure | Mobile Viking armies seeking bases and wealth |
| Senate and imperial stability | Regional loyalty, obligation, and legitimacy |
| Devastated frontier settlements | Depleted regions and threatened burhs |
| Sustained campaigning | Muster, serve, disperse, and recover |

## Intended Physical Footprint

Target rather than final specification:

- 1 compact A3 or two-panel map;
- 48 cards: 8 Scenarios, 8 Royal Priorities, 16 Commands, and 16 Crises;
- 10 regional fyrd pieces, 2 Household pieces, and 1 Mercian allied piece;
- 4 Danish Host markers with strength indicators;
- 8-12 regional readiness markers;
- 8-12 burh, base, raid, or control markers;
- 2 standard six-sided dice;
- one concise rulebook and one reference card.

Generic cubes and dice should remain viable so the game can be produced
economically in small quantities.

## Working Documents

- [Rules](RULES.md)
- [Design Scope](docs/DESIGN_SCOPE.md)
- [Historical Framework](docs/HISTORICAL_FRAMEWORK.md)
- [Scenario Outline](docs/SCENARIO_OUTLINE.md)

## Repository

- `game/game.json` - canonical map, Viking doctrines, cards, and scenarios
- `game/simulate.py` - coarse strategy and pressure simulator
- `scripts/build_cards.py` - cards, backs, and duplex print sheets
- `scripts/build_map.py` - campaign mat, order reference, and Army markers
- `art/alfred-command-key-art.png` - Volume II key art
- `RULES.md` - complete version 0.6 prototype rules
- `PLAYTEST.md` - difficulty targets and test protocol
- `PLAYABILITY_AUDIT.md` - decision-density audit and subsystem gates
- `EVALUATION.md` - current multi-perspective quality estimate and evidence gap
- `HISTORICAL_NOTES.md` - history, uncertainty, and design boundaries
- `DESIGN_TARGET.md` - quality gates and series distinction
- `docs/` - design, historical, and scenario framework

## Test

```bash
python3 game/simulate.py --games 2000
python3 scripts/build_cards.py
python3 scripts/build_map.py
```

## Play in a Browser

From the repository root:

```bash
python3 -m http.server 8780
```

Then open [http://127.0.0.1:8780/web/](http://127.0.0.1:8780/web/).

The version 0.6 web beta implements scenario setup, Royal Priorities, the
Command hand, all six Basic Orders, map movement, battle purposes, Danish
Intents, negotiation, Service, Harvest, recovery, objectives, and legacy
scoring. The campaign log is intended to support playtest reporting.

## Status

Complete version 0.6 print-and-play prototype. Numeric balance remains
provisional until repeated human playtesting.
