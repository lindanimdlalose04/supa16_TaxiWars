# Supa 16: Taxi Wars — v3.0 (full redesign)

Two taxi associations. One province. First to 25 points runs KZN.

## Run it
```
pip install pygame
python supa16.py
```
The `assets/` folder (houses, taxis, fonts, sounds) must sit next to
`supa16.py`. To regenerate the art from scratch:
`pip install pillow numpy && python gen_assets.py` (from the parent folder).

## Controls
- Click a highlighted town to drive there
- Hover any town for its name; hover a legal town to preview the road
- [H] help · [R] rematch · [M] mute · [T] (menu) blitz timer · [ESC] menu

## Rules
- Land on a house to collect the customers shown on its wall.
- Route claiming: the first taxi to drive a road owns it — the road
  tints your colour. Driving a rival's road pays them a 1-point toll.
- Regions: collect from the majority of a region's towns to claim it
  permanently for +5. The sidebar shows every region race.
- Hazards fire once, on the first taxi through, then the road is clear:
  Nkabi (-2), Super Nkabi (sent back along your trail, -1),
  Police (skip next turn). Eating a hazard still claims the route.
- Small fares (1-2) respawn in up to two empty towns every 4 rounds.
- Turn timer is OFF by default; toggle 30-second blitz turns with [T].

## What changed from v2 (design rationale)
- Click-to-move replaced number typing; node IDs deleted.
- Houses replaced circles: roof = region, wall number = value,
  collected towns shrink to small faded houses (the board declutters
  itself as it's played).
- Visual hierarchy inverted: thin quiet roads, loud customer values,
  one danger colour with shape-coded hazards, five colour families total.
- Route claiming + tolls is the new conflict engine: the road lattice
  becomes a live territory map (Risk-style map-as-scoreboard).
- Region bonus reworked from all-nodes (effectively never fired) to
  majority control (fires ~1.4x per game in simulation).
- Win target 20 -> 25 to fit the richer scoring; 300-game fuzz shows
  ~31-move average arcs with a 159/141 P1/P2 win split (no turn-order
  bias) and guaranteed termination.

## AI note
The engine keeps the same headless `GameEngine` interface
(`reset() / do_move() / get_state()`); `get_state()` now also exposes
`route_owner` and `region_claimed`. The old Q-table was trained on the
old rules and layout, so retrain before trusting the AI modes:
the state encoder should be extended with the new fields first.
