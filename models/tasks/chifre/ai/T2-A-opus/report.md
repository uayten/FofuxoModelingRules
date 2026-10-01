# T2-A (opus): the dragon's horns

File: `models/tasks/chifre/ai/T2-A-opus/T2-A.blend` (a copy of `start.blend`;
`start.blend` was not touched). Cage text: `T2-A.cage/Chifres.txt`.

Saved by the judging session: the run's harness refused report files from a
subagent, so the run returned this text and it was written here unchanged,
with the tokens filled in from the session's usage.

## Plan
The skill asks to show the plan and wait. Nobody answers during the run, so
the plan is here and I carried on.

One part: `Chifres`, an 8-vertex cylinder modeled whole (D-061), the dragon's
left horn (+X) only. The right horn comes from a Mirror (X) with
`mirror_object` = `Dragão Corpo`, so the origin sits on the part.
- Built with `start_part("Chifres", "cylinder", size=(46, 46, 140),
  vertices=8, parent="Dragão Corpo")`.
- Bottom cap deleted: the base is an open border hidden inside the head.
- 4 loop cuts give 6 rings; the top cap (a grid) closes the tip with quads.
- Stack: Mirror (X, mirror object = the body, clip, merge 0.1 mm) >
  Subdivision 1/2.
- No cutters. Size taken from the concept, which is at the body's scale.

## What I read
- skill/fofuxo-modeling-rules/SKILL.md (whole)
- models/TECHNIQUES.md
- models/example/laco/EXAMPLE.md: the heading list and the Techniques
  section only (lines 146-236)
- extension/fofuxo_cage/README.md
- models/FEEDBACK.md
- extension/fofuxo_cage/parts.py, lines 60-160
- extension/fofuxo_cage/mesh_io.py, lines 75-143, and a search for
  `mirror_object` in the extension
- The concept image, saved out with bpy, plus crops and pixel measures

Not read: DECISIONS.md. Not opened: ROADMAP.md, judge/,
models/tasks/laco/, any .blend under models/example/, prompt.md, git
history. A listing of models/tasks/chifre/ showed that judge/ exists; I did
not look inside it.

## Reading the concept
The Concept empty is 0.7615 m wide, so 0.607 mm per pixel, facing -Y.
- **Silhouette** (world mm):
  - The inner edge is almost straight, at X ≈ 110.
  - The outer edge is a convex arc: 150 at Z 501, widest at 157 around
    Z 535-545, then 144 at Z 574 and 132 at Z 588.
  - The tip is rounded, at X ≈ 115-118, Z ≈ 597, over the inner edge: a
    crescent that hooks inward.
  - About 47 mm at the widest; about 110 mm visible, from Z ≈ 490 to the tip.
- **Inner forms:** a soft line across the horn at Z ≈ 556 (a segment); a
  round section.
- **Hidden forms:** the hat brim hides the inner side between Z ≈ 510 and
  550; the head hides everything below Z ≈ 490. The horn continues into the
  head.
- **Other views (my own reading):** round sections, and the tip sweeping
  back 2-3 cm.

## The object
`Chifres`: mesh `Chifres`, parent `Dragão Corpo`, collection `Malha`,
material `Dragão Chifre` (new, cream). Origin at world (129, -30, 460) mm.
Rotation 0, scale 1.
- Stack: Mirror (X, mirror_object Dragão Corpo, clip on, merge 0.1 mm) >
  Subdivision (1/2).
- Cage: 57 vertices, 52 faces, all quads (6 rings × 8 + a 9-vertex tip cap).
- Evaluated, both horns: 434 vertices, 416 faces.
- Crease 0.5 on the ring at Z ≈ 556 (`loop v27-v30`).
- Cage size 58.8 × 53.6 × 208 mm.

Rings, placed as results with `target` ops (world mm):

| ring | where | center X, Y, Z | rx / ry |
|---|---|---|---|
| R0 (open border) | 14 mm under the head surface, vertex by vertex (ray cast) | 129.5, -32, ≈ 405-461 | 19.5 / 20.5 |
| R1 | root | 130, -31, 493 | 20 / 21 |
| R2 | the bulge | 133, -28, 533 | 24.5 / 22 |
| R3 | the line (crease 0.5) | 131, -24, 556 | 23 / 20 |
| R4 | | 126.5, -19, 572 | 17 / 15.5 |
| R5 | | ≈ 117, -13, 586 | 10 / 9 |
| cap + tip | | ≈ 114-116, ≈ -7 to -10, 594-598 | 5 / 4.8 |

The upper rings are tilted perpendicular to the curve, which draws the
crescent and the backward sweep.

## Measures and comparison
All measures come from the evaluated vertices, never from `dimensions`.
- **One horn, world:** X 107.5..157.5, Y -52.5..-3.5, Z 405.4..598.5.
  Size 50.0 × 49.0 × 193.1 mm, including about 14 mm sunk into the head.
  Tip at (118.2, -9.3, 598.5). The -X horn is the exact mirror.
- **Front:** I rasterized the evaluated triangles in the concept's pixel
  frame, with a depth test against the body, and compared them with the
  concept's cream pixels.
  - Overlap (IoU) 0.84 on both horns.
  - Per row, X in mm, model / concept:

| Z | inner | outer |
|---|---|---|
| 596 | 111.1 / 111.1 | 123.3 / 119.6 |
| 588 | 109.3 / 108.7 | 133.6 / 131.8 |
| 574 | 108.7 / 111.1 | 145.7 / 143.9 |
| 559 | 108.1 / 106.9 | 153.6 / 151.2 |
| 537 | 108.1 / (brim) | 156.7 / 155.5 |
| 516 | 109.3 / 106.9 | 153.0 / 153.6 |
| 501 | 109.9 / 111.7 | 151.2 / 148.8 |

  Most of the extra area on the model is the stem below Z 490.
- **Side and top** (views: right, top, 3/4 at yaw 30 and 45, back): the horn
  rises from the upper side of the head, a little behind its middle, sweeps
  back about 25 mm, and has round sections.
- **Sections** (Mirror off for the measure): n 1.7, 1.7, 1.45, 2.05, 2.7 from
  root to tip. An ellipse is 2.
- **The base stays inside the head:** the open border's evaluated vertices
  are 1.8-10.6 mm inside the body.

## Shape map

| form | status | where |
|---|---|---|
| Straight inner edge, convex outer edge, widest at Z ≈ 540 | done | R1-R4 |
| Tip hooking inward, rounded | done | R5, the cap |
| Segment line at Z ≈ 556 | partial: faint crease, no step | R3 |
| Round sections | done | every ring |
| Base continuing into the head | done | R0 |
| Backward sweep (my reading) | done, unconfirmed | R3 to the cap |
| Horn emerging where the concept shows it (Z ≈ 490) | not done: the body's head is lower there | R0-R1 |

## Decisions and what I am unsure of
1. **The body's head is lower than the concept's at the horns:** at X 150
   the body's surface is at Z 412-425, where the concept's head meets the
   horn at about 490.
   - With the horn where the concept draws it, 3-6 cm more stem shows on the
     outer side.
   - I tried moving it 10 mm in and 10 mm down (IoU 0.57) and reverted.
     Moved inward, it would run into a hat modeled from the concept (the band
     reaches X ≈ 95-100).
   - I kept the concept's silhouette and sank the base into the real head.
     If the modeler prefers the emergence point, move the object about 20 mm
     down on Z.
2. **The segment line** is a crease 0.5 (edge data). A real step would need
   two close loops, against "start lean".
3. **The backward sweep and the depth** come from no view in the concept.
   They are my reading.
4. **Name:** `Chifres`, plural for a Mirror pair (D-004), though E1 calls its
   mirrored horn `Chifre`.
5. **Parent:** the body object, not a bone. A bone parent is rig work
   (D-017).
6. **Material:** a new `Dragão Chifre`, because `Dragão Base` is a textured
   material.
7. **The concept is slightly asymmetric** (left horn reaches X -158.5, right
   155.5); the Mirror uses about the average.

## Techniques
- **The cage bigger than the result** (pending): every ring was placed as a
  result with `target` ops. Helped a lot. The cage is 8.8 mm wider and 14.9 mm
  taller than the result. `target` stops working once the Mirror has a mirror
  object, so I shaped first and made the last tweak with `move`.
- **A round part with few vertices** (D-051): 8 per ring, whole. Helped:
  n 1.5-2.7 with no extra loops.
- **Spacing sets how round a turn is:** the rings get closer toward the tip.
  Helped keep the hook tight.
- **Loops end on the outline's turning points** (Provisional): one ring per
  turning point (bulge, line, hook). Helped: within 2.5 mm with 6 rings.
- **A lighter cage** (D-045): not needed.
- The other blocks don't match a form in the concept.

## Audit
`fofuxo_lib.audit()` doesn't exist yet. I used the sync's checks and the
measures above: scale (1, 1, 1), rotation 0, nothing applied, no join, no
export, all quads, no loose geometry, mesh named after the object, material
set.
- 0 ERROR.
- `WARN open_edge` (v0-v14): the base border, on purpose, inside the head.
- `WARN cage_dips` (v17, v19, v21, v23): the diagonal vertices of the tip's
  grid cap.
- `WARN cage_dips` (v32, v36): R1's outer vertices, from the tilted root.
  Neither is meant as a hug.

## Tools
- No tool call failed.
- My own errors, both fixed:
  - `crease L3` hit a lengthwise loop: on a cylinder the L labels run along
    the part. Fixed with `crease loop v27-v30 0.5`.
  - One MCP call returned a string instead of a dict.
- `sections` with a mirror-object Mirror measures both horns as one shape. I
  turned `show_viewport` off for the measure.
- `target` and the sub columns are unavailable once the Mirror has a mirror
  object.
- A whole cylinder's frame is local and runs lo..hi. That is awkward for a
  part whose origin is not at its center, so I converted the targets in code.

Cost: 13.0 min, 23 syncs, 248 ops, 24 renders, 6 measures, 218,217 tokens
(the subagent's total, 75 tool calls).
