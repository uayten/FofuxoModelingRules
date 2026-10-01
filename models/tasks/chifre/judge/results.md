# T2 results

The blind copies (`blind/modelo-1..4.blend`) were removed after the
verdicts: they were copies of the runs' files; the keys stay.

## Verdict (the modeler, blind, 2026-09-30)

"o modelo 1 ficou melhor, mas ambos estão muito ruins, o claude tentou fazer
por cima da referência sem levar em consideração o corpo do dragãozinho que
já existe no arquivo."

Key (`blind/key.b64`): modelo 1 = **T2-B** (without the techniques),
modelo 2 = T2-A (with them). The question of item 9 gets a no for now: the
library did not carry to the horn, and both runs failed on something no
technique covers: the part was traced over the concept instead of built on
the body (D-063).

## Runs

| | T2-A (with techniques) | T2-B (without) |
|---|---|---|
| Report | [report.md](../ai/T2-A-opus/report.md) | [report.md](../ai/T2-B-opus/report.md) |
| Time | 13.0 min | 10.1 min |
| Tokens (subagent total) | 218,217 | 195,981 |
| Syncs / ops / renders / measures | 23 / 248 / 24 / 6 | 11 / 23 / 9 / 3 |
| Object, stack | `Chifres`, Mirror X across the body > Subdivision 1/2 | the same |
| Cage | 57 v, 52 quads, open base | 74 v, 72 quads, closed |
| Poles (valence 3) | 12, 6 cage dips | 8, no dips |
| Side modeled | +x | -x |

E1's horn: 57 v, 52 quads, open base, 12 valence-3 poles, no dips.

## Targets (`judge/target.md`, one horn, world mm; w compared on the +x side)

| measure | E1 | T2-A | T2-B |
|---|---|---|---|
| faces | 52 | 52 in | 72 out |
| verts | 57 | 57 in | 74 out |
| world size w | 88.6 | 50.4 | 75.7 |
| world size d | 91.0 | 49.0 | 60.4 |
| world size h | 124.3 | 194.2 | 150.6 |
| base w | 88.4 | 129.5 | 100.6 |
| base d | -74.0 | -32.0 | -51.7 |
| base h | 472.6 | 441.2 | 466.7 in |
| tip w | 117.5 | 114.0 in | 120.5 in |
| tip d | -74.0 | -7.7 | -21.6 |
| tip h | 567.2 | 598.6 | 599.7 |
| in | 11/11 | 3/11 | 2/11 |

T2-B's base is the middle of its part buried in the body (its cage is
closed); T2-A's and E1's, the middle of the open border.

## What the numbers say

- **Both followed the concept, not the body.** Both tips sit at the
  concept's height (about 599 mm), about 32 mm above E1's. The body's head is
  lower than the concept's where the horns sit, and both runs said so in
  their reports. The modeler put the horn on the body, lower.
- **Both invented a backward sweep.** The concept is front only. E1's tip is
  straight above its base in depth (d -74 for both); A sweeps back 24 mm, B
  30 mm, and both sit farther back on the head (base d -32 and -52).
- **Both are thinner than E1's.** E1: 89 × 91 mm at the box, a wide base.
  A is 50 × 49, B 76 × 60.
- **A matches E1's counts exactly** (57 v, 52 quads, 12 valence-3 poles),
  from a different build (an 8-vertex cylinder with 6 rings and a grid cap;
  E1 is a cube extruded with its loops rotated).

## Second pair: T2-C and T2-D (D-063 in the skill, tools fixed)

**Verdict (the modeler, blind, 2026-10-01):** "o modelo 4 ficou melhor, mas
ainda está fino na base, a AI não está sabendo interpretar o concept no
sentido do que funciona ou não funciona na tradução do 2D para o 3D." Key:
modelo 3 = T2-C (with the techniques), modelo 4 = **T2-D** (without). Twice
now the run without the library was preferred. Lesson: D-064.

Outside the head, 15 mm bands (w × d, mm):

| z | E1 | T2-D |
|---|---|---|
| 477-507 | 59-80 × 75-79 | 42-64 × 49-51 |
| 522-537 | 49 × 49 | 55 × 45 |
| 552-567 | 25 × 25 | 32-43 × 32-39 |

Blind copies `blind/modelo-3.blend` and `modelo-4.blend`; which is which in
`blind/key2.b64`. Both runs also kept off `DECISIONS.md` (D-063 there quotes
E1's numbers).

| | T2-C (with techniques) | T2-D (without) |
|---|---|---|
| Report | [report.md](../ai/T2-C-opus/report.md) | [report.md](../ai/T2-D-opus/report.md) |
| Time / tokens | 10.8 min / 211,055 | 5.1 min / 182,780 |
| Syncs / ops / renders / measures | 28 / 11 / 18 / 7 | 13 / 9 / 2 / 11 |
| Stack | Mirror across the body only (no Subdivision, for density) | Mirror across the body > Subdivision 1/2 |
| Cage | 128 v, 126 quads (12 sides), closed | 57 v, 52 quads (8 sides), open base |
| Poles (valence 3) | 8 | 12 |
| Moved down onto the body (D-063) | 15 mm | 19 mm |

| measure | E1 | T2-C | T2-D |
|---|---|---|---|
| faces | 52 | 126 | 52 in |
| verts | 57 | 128 | 57 in |
| world size w | 88.6 | 69.2 | 71.3 |
| world size d | 91.0 | 64.9 | 58.0 |
| world size h | 124.3 | 142.3 | 131.9 in |
| base w | 88.4 | 108.4 | 108.0 |
| base d | -74.0 | -28.6 | -32.0 |
| base h | 472.6 | 451.7 | 455.0 |
| tip w | 117.5 | 118.4 in | 116.9 in |
| tip d | -74.0 | -3.5 | -1.3 |
| tip h | 567.2 | 583.5 | 577.8 |
| in | 11/11 | 1/11 | 4/11 |

What moved with D-063: both read the body against the concept first and
lowered the horn onto the head; the tips came down from about 599 to 584 and
578 (E1 567). What did not: every run so far puts the horn on the top of the
head (base d about -30) with its tip swept back to d about 0, where E1's
stands farther forward (base and tip at d -74) and upright in depth; and
every run's horn is thinner than E1's (box 58-71 mm against 89 × 91).

## Tools, found by the runs

- `target` ops and the sub columns stop working once a Mirror has a
  `mirror_object`; `sections` then measures both horns as one (both runs
  shaped before adding the Mirror).
- `edit(..., "move v21 w -1% d -1%")` returned `action: error` with no
  message (the line was wrong: `move` takes one value).
- On a whole cylinder the `L` labels run along the part; `crease L3` hit a
  lengthwise loop.
- `views()` draws no other object unless the part is parented.
- A subagent's harness refused to write `report.md`; the judging session
  saved both from the returned text.
- Fixed before T2-C/D: the first four above (one side measured, rings as
  L labels and drawn as rings, the body drawn, the `move` message).
- Found by T2-C/D, still open:
  - no op places or turns a ring along a bent axis: both runs wrote the
    cage's base lines from Python;
  - `sections` cuts across a frame axis, so a leaning horn is cut at a slant
    (n and the waist read wrong); a cut square to the part's own axis is
    missing;
  - `start_part` leaves the part in the Scene Collection, not beside the
    body;
  - `add MIRROR` takes Blender's merge 1 mm, not the 0.1 mm of D-054;
  - the concept panel cannot show the concept moved onto the body (D-063),
    so both compared by their own rasterizing.
