# T2-B (opus): the dragon's horns

Run without the skill's techniques step (no `models/TECHNIQUES.md`, nothing
under `models/example/`). Nobody answered questions; every decision below is
mine, with its reason.

Saved by the judging session: the run's harness refused report files from a
subagent, so the run returned this text and it was written here unchanged,
with the tokens filled in from the session's usage.

## Contents

- [Delivery](#delivery)
- [What I read](#what-i-read)
- [Reading the concept](#reading-the-concept)
- [Plan](#plan)
- [Build](#build)
- [Look: measures and comparison](#look-measures-and-comparison)
- [Shape map](#shape-map)
- [Audit](#audit)
- [What I am unsure of](#what-i-am-unsure-of)
- [Tool notes](#tool-notes)
- [Cost](#cost)

## Delivery

1. File: `models/tasks/chifre/ai/T2-B-opus/T2-B.blend` (cage text in
   `T2-B.cage/Chifres.txt`, with the shape map in its `forms` section).
2. Parts:
   - `Chifres` → Mirror (X, `mirror_object` = `Dragão Corpo`, clip on, merge
     0.1 mm) > Subdivision (viewport 1, render 2). Parent `Dragão Corpo`,
     collection `Malha`, material `Dragão Chifres` (new), shade smooth.
3. Shape map: [below](#shape-map).
4. Measures: [below](#look-measures-and-comparison).
5. What the user can adjust: the cage (74 vertices per horn, rings listed in
   the shape map); Subdivision levels; Mirror (the horns stay symmetric
   across the body's X plane, so editing one edits both).
6. Audit: 0 ERROR, 1 WARN justified (density, see [Audit](#audit)).
7. Library gaps: `fofuxo_lib` does not exist (the skill marks it "Proposed
   API — not implemented yet"); Fofuxo Cage was used in its place, as the
   task asked. No auditor exists either; I ran the audit list by hand
   (read-only bpy).

## What I read

- `skill/fofuxo-modeling-rules/SKILL.md` (whole, first)
- `extension/fofuxo_cage/README.md`
- `models/FEEDBACK.md`
- `models/tasks/chifre/prompt.md`
- `extension/fofuxo_cage/parts.py` (lines 60-160: `start_part`, to see where
  the cylinder's origin and caps land)
- `extension/fofuxo_cage/mesh_io.py` (lines 70-150: how a Mirror with a
  `mirror_object` is handled; found by a grep for `mirror_object`)
- `extension/fofuxo_cage/__init__.py` (lines 1-34: the exported functions,
  looking for an auditor)
- My own run files: the cage text `T2-B.cage/Chifres.txt`, the view sheets
  `Chifres.png` and `Chifres.views.png`, and the concept saved out of the file.

Not read: `DECISIONS.md` (the skill's rules were enough to decide), ROADMAP,
judge, T2-A, laco, examples, git history.

## Reading the concept

Scene: `Concept` Image Empty (`EUA-Frente.png`, 1254 px, 0.7615 m wide,
centered at z 307.3 mm, at y +478 mm behind the body), so 1 px = 0.607 mm.
`Dragão Corpo` (2594 faces, Armature only, material `Dragão Base`),
`Dragaozinho` (armature). Names in Portuguese; Blender language pt_BR.

- **Silhouette (front)**: two cream horns, one on each side of the hat. Each
  is a crescent: the outer edge convex, widest at z ≈ 537-545 mm (|x| 156 mm);
  the inner edge concave; the rounded tip bends back in toward the head at
  (|x| 118, z ≈ 597). Visible width ≈ 60 mm at z 545, 37 mm at z 566, 22 mm
  at z 585. Measured row by row from the image (cream mask) on both horns.
  The concept's left horn is ≈ 4 px wider than the right one; the model is
  symmetric and sits between them.
- **Inner forms**: a faint band across the horn at about z 545-560 mm, the
  only mark in the shading. I read it as where the horn turns backward.
- **Hidden forms**: the hat brim hides the inner lower third of each horn;
  the inner edge keeps its concave curve behind the brim down to the head
  (≈ |x| 85, z 505). The base continues into the head.
- **Other views** (imagined): round section (depth ≈ width), tip swept back.
  A horn curving back would look just like this from the front, with its
  upper part foreshortened.
- **The body vs the concept**: the body's head is lower than the concept's
  at the horns' outer side. At |x| 138 mm the concept's head outline is at
  z ≈ 482; the body's surface is at z ≈ 451. Decision: keep the horn's shape
  and upper silhouette where the concept has them (tip, outer bulge) and let
  the base continue along the same curve down into the body. The horn's
  outer side therefore shows ≈ 20 mm more than in the concept.

## Plan

(The skill asks for approval of a plan with more than one part. This is one
part and nobody would answer, so the plan is written here and then built.)

| Part | Base | Stack | Cutters | Parametric |
|---|---|---|---|---|
| `Chifres` | cylinder, 8 vertices, modeled whole (D-061), grid-filled caps (D-062), 5 loop cuts → 7 rings | Mirror (X, across `Dragão Corpo`) > Subdivision 1 | none | no |

- Size: from the concept. Per horn ≈ 75 × 60 × 150 mm evaluated, including
  the buried base.
- Origin on the part (at the base ring's center), Mirror across the body (the
  skill's Provisional rule for a side part), rotation 0, scale 1.
- The horn is not symmetric in itself, so the cylinder is kept whole, not
  cut. The mesh is on -X (the image's left).
- Parent: `Dragão Corpo`, the object the horns sit on (D-011 grouping). No
  bone parenting (rig work is out of scope), so the horns do not follow the
  head's bone yet.
- Material: `Dragão Chifres` (exclusive to this asset → asset name, D-008),
  cream sampled from the concept (sRGB 240, 215, 180).

## Build

1. `start_part("Chifres", "cylinder", size=(60, 55, 130), vertices=8,
   at=(-110, -50, 487))` in `Malha`.
2. `mesh loopcut_slide v0-v1 number_cuts=5`: 7 rings.
3. Ring positions written in the cage text (whole permille). Each ring is a
   circle between an outer and an inner point read from the concept (the
   silhouette vertices lie in the front plane), inflated 10% for
   Subdivision's shrink. Ring centers go from y -52 (base) to -31 mm. The top
   cap ring is pulled up into a rounded point (v24 at z 606); the bottom cap
   is pushed down inside the head.
4. `move` ops: the outer side of R0-R3 out by 2-4 mm (the outer bulge was
   2-6 px inside the concept); R4-R6 and the cap back by 3-7 mm (the sweep);
   v21 out by 1% to clear a `cage_dips` warning.
5. `add MIRROR at first`, `set Mirror mirror_object "Dragão Corpo"`, `use_axis
   X`, `use_clip on`, `merge_threshold 0.1mm`.
6. Material, shade smooth, parent (bpy data, not mesh edits).

No modifier applied, no join, no export.

## Look: measures and comparison

Evaluated vertices (`evaluated_get(depsgraph).to_mesh()`), world mm:

| | model | concept |
|---|---|---|
| one horn, size x × y × z | 75.6 × 60.3 × 150.5 (incl. base buried 10-20 mm) | width only: ≈ 60 at z 545 |
| both horns, x span | -155.8 .. +155.8 | outer max -157.8 / +155.2 |
| tip | (±120, -22, 599.9) | (±118, ?, ≈ 597-599) |
| z range | 449.3 .. 599.9 | visible from ≈ 482 (head) to ≈ 599 |
| y range | -76.3 .. -16.0 | (no side view) |

- **Front**: outline compared row by row with the cream mask, every 8 px from
  z 599 to 478. The outer edge is within 0-3 px (≤ 2 mm) of the right horn
  and 3-6 px inside the wider left one; the visible inner edge is within
  0-4 px. Silhouette IoU above the brim (rows 140-235, both horns): **0.90**.
  An overlay of the result on the concept, plus a side-by-side check: the
  crescent, the bend of the tip and the widest point line up.
- **Side / top / 3/4** (the view sheet, `views` at yaw 30/150/-60, and my own
  render of horns + body from 6 angles): a fat round base tapering to a
  point, tip leaning back. The horns sit on the top-side of the head,
  slightly behind its middle (base center y -50 mm; head spans y -241 to
  +80). The top view shows a round-to-oval section.
- **Junction**: the base ring R0 and the bottom cap are inside the body,
  10-20 mm deep (checked with a BVH nearest-point test). Ring R1 is 3-10 mm
  above the surface, so the surface crosses into the head between R0 and R1
  with no gap.
- `sections` along h (oblique cuts, since the horn leans): n 1.45-1.95, depth
  ≈ width, so roughly round, as planned.

## Shape map

| Form | Status | Where |
|---|---|---|
| Front crescent: convex outer edge, widest at z ≈ 540 | done | outer column v12, v68, v67, v66, v65, v64, v13 |
| Concave inner edge, tip bent inward | done | inner column v4, v48 … v5; cap ring v16-v23 |
| Rounded tip at z ≈ 600 | done | v24 and the cap ring |
| Base continues behind the brim and into the head | done | ring R0 (v12 v10 v8 v6 v4 v2 v0 v14) and bottom cap, buried |
| Round section (depth ≈ width) | done (guessed) | every ring |
| Backward sweep of the upper half (side view) | partial, guessed | ring centers y -52 → -21; strength not checked against any side reference |
| Faint band across the horn at z ≈ 545-560 | partial | only as the start of the backward bend around R3-R4; no ridge or crease |
| Horn base where the concept puts it (z ≈ 482 on the outer side) | not done, on purpose | the body's head is ≈ 30 mm lower there; the base follows the body |

## Audit

By hand (no auditor exists), on `Chifres`:

- Stack: Mirror > Subdivision, canonical order, default names. Scale
  (1, 1, 1), rotation 0, origin at the base ring's center (-110, -50, 487 mm).
- Cage 74 v / 72 f per horn, all quads, 0 triangles, 0 n-gons, 0 loose
  vertices or edges. Closed: 0 open edges in the cage and in the evaluated
  mesh. Normals point outward (positive signed volume; sync reports no
  `inside_out`). Material set. Mesh data named `Chifres`.
- Sync validation: no issues on the last sync.
- **WARN density**: the evaluated mesh has 1.27 faces/cm², the body 0.37
  (edges about 1.8× shorter). The cage alone is 0.32/cm², close to the body.
  Kept because the skill gives small accessories Subdivision 1, and an
  8-sided cage without it is faceted. Both horns together are 576 evaluated
  faces (the body has 2594). For a leaner game mesh the modeler could set
  Subdivision viewport to 0. The horns would then read about 10% fatter,
  because the cage is inflated for Subdivision's shrink, and would need
  refitting.
- The bottom cap (12 faces per horn) is hidden in the head. It could be
  removed for a game mesh (D-022 allows an opening hidden inside the other
  part). I kept it closed so the part is a whole volume.

## What I am unsure of

- **Side view**: the concept is front only. The backward sweep (~30 mm) and
  the round section are my reading, not measured.
- **Base height**: I anchored the base on the body, which is lower than the
  concept's head, instead of shifting the whole horn down. The other choice
  keeps the concept's horn-to-head proportion but misses the concept's tip
  by ≈ 25 mm.
- **Y position**: base center at y -50 mm (the head's crown is ≈ -60, head
  center -63). In the concept the hat's brim covers the horns' front, so the
  horns are at or behind the brim's front edge; the exact depth is unknown.
- **Parent**: parented to `Dragão Corpo` for grouping. The body deforms with
  the armature, so the horns need a head-bone parent (rig work, not done).
- **Material name** `Dragão Chifres`: the belly and claws are also cream
  (from the body's texture). If the cream is meant to be shared, a generic
  name may fit the project better.
- The faint band on the horn may be only lighting.

## Tool notes

- `edit("Chifres", "move v21 w -1% d -1%")` returned `action: error` with no
  issue and no message. `move` takes one value for all its axes, so my line
  was wrong, but the error said nothing. Splitting it into two lines worked.
- With the Mirror's `mirror_object` set, the sub columns and `target` ops are
  unavailable (`sub unavailable: MIRROR`), as the README says. I shaped the
  horn before adding the Mirror.
- `views()` drew no other object (the horns had no parent at that time), so
  the "all together" check used my own projection of body + horns.
- These worked: the launcher, `instance()` (`role: ai`), `start_part`,
  `mesh loopcut_slide`, the text push, `sections`, `round_start` /
  `round_end`.

## Cost

Cost: 10.1 min, 11 syncs, 23 ops, 9 renders, 3 measures, 195,981 tokens (the
subagent's total, 68 tool calls).
