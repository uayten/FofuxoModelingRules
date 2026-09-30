# Laço Estilizado para Games (bow tie)

- **File:** `human/Laço.blend` (E1: the dragon + "Roupa Estadunidense" outfit)
- **Objects:** `Laço` (wings), `Laço Nó` (knot, child of `Laço`)
- **Concept:** `concept.png`, the bow tie on the dragon's chest
- **Measures:** `measures.json`: profiles, sections (roundness, waist) and
  sizes of both objects, taken with Fofuxo Cage's shape tools
- **Status:** measured; rules from E1 (interview) and T1 (AI runs judged by the
  modeler). No dedicated interview on how the bow was built step by step.

## Contents

- [File and objects](#file-and-objects)
- [How it was made](#how-it-was-made)
- [Whys](#whys)
- [AI deductions](#ai-deductions)
- [What the modeler's edit of B1 teaches](#what-the-modelers-edit-of-b1-teaches)
- [Techniques](#techniques)
- [Rules that came from it](#rules-that-came-from-it)
- [Only this model](#only-this-model)
- [Open questions](#open-questions)

## File and objects

| | `Laço` | `Laço Nó` |
|---|---|---|
| Stack | Mirror XYZ (clip, merge 0.1 mm) → Subdivision 1/2 | Mirror XYZ (merge 1 mm) → Subdivision 1/2 |
| Cage per 1/8 | 28 vertices, 19 quads | 10 vertices, 5 quads |
| Evaluated | 610 vertices, 608 faces | 162 vertices, 160 faces |
| Size, evaluated | 126.1 × 28.1 × 68.4 mm | 29.7 × 26.0 × 35.1 mm |
| Transform | world-aligned | rotated -6° on X |

- The `Laço` cage is one patch with three corners on the mirror planes and a
  single valence-3 pole (v10). Its boundary on the Y plane is the front
  silhouette.
- Crease 1.0 on the edges of the X plane.
- The concept's bow tie measures 118.4 × 62.5 mm at this file's Image Empty
  scale (124.4 × 65.7 mm in `models/tasks/laco/start.blend`, whose Empty is
  scaled differently).

## How it was made

*To be told by the modeler.* Known from E1 and T1: 1/8 of the bow with Mirror
on every axis (D-009), the center vertices packed close so the wing narrows
into the knot (D-039), crease where Subdivision would pull the pinch (D-021).

## Whys

From the E1 interview and the T1 verdicts, in the modeler's words when kept:

- Shape comes first: matching the concept is "very, very, very important"
  (D-032).
- The wings keep converging behind the knot, crossing like an X; "it takes
  some imagination to understand the concept beyond what is strictly in the
  image" (D-037).
- From the top the wing converges in depth too: a figure eight (D-041).
- The shading shows a dent in the middle of each wing's outer edge and a fold
  where the wing enters the knot (D-036).

## AI deductions

| Deduction | Evidence | Status |
|---|---|---|
| The cage is bigger than the result on purpose: Subdivision pulls the wing 9 mm shorter and 11 mm thinner | cage 135.2 × 39.2 × 75.6 mm, evaluated 126.1 × 28.1 × 68.4 mm | pending |
| The Y-plane rim of the cage is drawn as the front silhouette | loop L1 lies on the Y plane from the knot to the tip | pending |
| The v10 pole exists to round the wing's top corner | only interior pole; sits where the rim turns | pending |
| The bow is about 6% bigger than the concept | 126.1 vs 118.4 mm at the Empty's scale (E1); 131.3 vs 124.1 mm in the modeler's edit of B1 | coincidence: not on purpose (D-056) |
| `Laço Nó` is tilted -6° to follow the chest | rotation on X only | pending |
| The wing's loops radiate from the knot and follow the outline, not columns across the width: the Y-plane rim (8 vertices) runs from the center up to the top corner and around the tip; a ring (5 vertices) goes around the outer lobe | cage text in B1's frame (B1 round 4 self-critique) | pending |
| The whole X-plane column sits within 10% of the height (h 0 to 95 permille), with crease 1.0: the wing narrows almost to a point at the knot (D-037) | same | pending |
| The cage stays outside the surface everywhere, by a steady margin: the tip ring is 1.4 × deeper in the cage than in the result | same: v1 base d 1185, sub 797 | pending |
| The thin middle row (1.5 mm deep) runs from the knot to half the width; past it, the h 0 row is as deep as the lobes | v22 d 66, v3 d 93, v1 d 1185 (base) | pending |

## What the modeler's edit of B1 teaches

`models/tasks/laco/human/B1-human-edit.blend`: the modeler took B1 after
round 5 and made it "igual ao concept (modelagem correta)". Read by id
against round 5 and measured against E1. Written so the AI can do it again
on another heart-shaped (or lobed) part.

**Topology: place loops for the silhouette, then count.**

- The loop the modeler had marked for removal (round 5) ran into the pole at
  the tip and gave the outline nothing. The edit adds a loop back in another
  place, ending with 28 vertices and 19 quads per 1/8, E1's count: the fault
  was where the loop ran, not how many there were.
- The new loop starts at the knot next to the pinch (v30 on the X plane at
  h 61, v31 at h 82: beside the slit row), climbs across the lobe (v22 h 609,
  v32 h 659) and leaves on the rim at the tip (v29, at the widest point of
  the upper tip bulge). A loop that ends on the silhouette adds a point to
  the outline; one that ends in a pole mid-surface does not.
- The heart's tip now has four rim points from the top corner to the dent:
  upper corner (v1, h 919), upper bulge (v29, h 628), lower bulge (v19,
  h 302), dent on the Z plane (v5, 977 against 1054: 7%). Round 5 had
  three and the tip read as a straight edge.
- The outer column moved in (w 880 → about 810) to leave room for the tip,
  and the lobe's edges were spread apart: close edges keep a turn sharp under
  Subdivision, spread edges round it (D-039, the other side).
- Each lobe's section now has the rim plus three rows before the waist row:
  upper (L4), middle (the new loop), lower near h 0 (the slit row, D-039).

**Volume: fuller lobes than the silhouette alone asks for.**

- Deeper: half depth 16.8 mm at 70% of the width (round 5 and E1: 14.3,
  14.4). The seams the modeler had marked "para dar um formato mais
  arredondado" were pulled toward -Y here (v15 +27%, v23 +14%, v27 +4%).
- Taller lobes at 30-80% of the width (+1.5 to +2.4 mm of half height) and a
  rounder tip (half height 26.0 mm at the tip against 27.4).
- Rounder sections toward the tip: n 3.35 at 70% (round 5: 3.8) and the
  waist fuller there (0.83 against 0.73): past the middle the two lobes
  merge; the pinch stays near the knot (0.35 at 20-30%).

**Size and place.**

- The whole bow is 131.3 × 33.7 × 69.8 mm, about 6% wider and 7% taller than
  the concept's red silhouette (124.1 × 65.3 mm), as E1 was. Not on purpose:
  the quickest way the modeler found to the shape they wanted (a
  coincidence). What it shows: the concept is a starting reference, and a 2D
  drawing of an organic object cannot be copied into 3D; the 3D has to work
  from every angle (D-056).
- `Laço` moved 1.3 mm in X and 0.4 mm in Z to center the bow on the
  concept's bow (the red's center, not the Image Empty's).
- The knot grew 11% in width (34.7 mm; round 5: 31.3; E1: 29.7), fuller at
  its front corners (half height 16.3 mm at 65% of its width against 14.0).
  Its height stayed at 36.2 mm (the concept's knot column: 35.1 mm). Why: in
  3D the wings cut into the knot in a way that did not look like the concept,
  so the knot grew to hide the junction (D-057). Only its front and back
  vertices moved out (v0, v1, v7); the side vertices on the mid plane (v5,
  v9) stayed, so seen from the top the knot's sides stay in where the wings
  pass: it hugs them.

**How to do it again.**

1. Draw the outline's turning points on the concept first (corners, bulges,
   dents); give each one a rim vertex, and let every loop across the part
   end on one of them.
2. Near a pinch, keep the row next to the thin row tight (D-039); let the
   next loop start there and fan out to a bulge on the rim.
3. Count last: the reference's count is a sanity check, not a target.
   Space the edges by the roundness wanted: close for a crisp turn, apart for
   a round one.
4. Make lobes fuller than the front view suggests: half depth at the lobe's
   widest point about a quarter of the part's full height (16.8 of 69.8 mm),
   sections n 3.1-3.5.

## Techniques

One block each: when to use it, how in cage words (and the Fofuxo Cage line
that does it), how to measure it, and where it comes from. Indexed in
`models/TECHNIQUES.md`; a session reads a block only when the concept shows
that form.

### Pinch into a knot

- **When:** a part enters another and the concept shows a fold or a
  narrowing there (the wing into the knot).
- **How:** the h 0 row stays within about 1.5 mm of the Y plane from the knot
  to half the width; the row next to it sits close to it (a tight loop);
  crease 1.0 on the X-plane column where the part enters (D-021). Tighten with
  `mesh edge_slide loop vA-vB factor=...`.
- **Measure:** `section w 0.15 waist` and `section w 0.3 waist` 0.28-0.32
  (E1), opening to 0.6 at 55% and 0.85 past 70%.
- **Source:** E1, B1 round 5. D-039 (Stated).

### Spacing sets how round a turn is

- **When:** a corner comes out too round or too sharp under Subdivision.
- **How:** edges close together keep a turn crisp; spread apart, they round
  it. `mesh edge_slide`, `mesh space_edge_loops_evenly ring vA-vB ring vB-vC`.
- **Measure:** the section's exponent n (higher = boxier) and `profile`.
- **Source:** B1 round 6 (the heart's lobe spread apart). D-039, the other
  side (Stated).

### Loops end on the outline's turning points

- **When:** a lobed or heart-shaped silhouette.
- **How:** mark the outline's corners, bulges and dents on the concept; give
  each a rim vertex; every loop across the part ends on one. Count last.
  B1's tip: upper corner, upper bulge, lower bulge, dent.
- **Measure:** the view sheet's outline over the concept; `profile front`.
- **Source:** the modeler's B1 edit. Item 25 (Provisional).

### Fuller lobes than the front view asks for

- **When:** round, soft parts seen from the front only.
- **How:** push the lobe out in depth: `mesh shrink_fatten faces ...
  value=0.6mm falloff=smooth radius=20%`, or pull its marked seams
  (`mesh translate seam d=+3% falloff=smooth radius=25%`).
- **Measure:** half depth at the lobe's widest point about a quarter of the
  part's full height (16.8 of 69.8 mm); sections n 3.1-3.5.
- **Source:** the modeler's B1 edit. AI deduction, pending.

### A round part with few vertices

- **When:** a knot, a button, a round section (D-051).
- **How:** 10 cage vertices per 1/8 with Subdivision; `mesh tosphere` or
  LoopTools relax on a closed loop off the mirror planes.
- **Measure:** sections n about 2.5.
- **Source:** E1's knot, B1 round 4. D-051 (Stated).

### The silhouette rim on the Y plane

- **When:** a mirrored part seen from the front.
- **How:** the longest loop (L1) lies on the Y plane and draws the front
  outline from the knot to the tip.
- **Measure:** the view sheet's outline over the concept; `profile front`.
- **Source:** E1. AI deduction, pending.

### The cage bigger than the result

- **When:** always with Subdivision: it pulls the surface in.
- **How:** place the result, not the cage: `target v22 w 945 d 440`, or
  `fit` to a captured surface.
- **Measure:** `editability`: offset median 2.7 mm on E1's wing (2.2 on the
  knot); the result 9 mm shorter and 11 mm thinner than the cage.
- **Source:** E1. AI deduction, pending.

### A lighter cage: remove a loop that carries no shape

- **When:** the cage has more loops than the reference, or a loop gives the
  outline nothing ("muito high poly").
- **How:** the modeler marks it; `dissolve sharp` (or `mesh dissolve_edges
  seam`); then `fit` to the surface captured before.
- **Measure:** `poly_budget` in the sync; `deviation` within 0.3 mm of before.
- **Source:** B1 round 5. D-045 (Stated).

### A covering part hides the junction

- **When:** one part sits over where two others meet (the knot over the
  wings).
- **How:** widen the covering part's front and back; keep its sides in where
  the other part passes, so it hugs it (`cage_dips` flags those vertices: on
  purpose).
- **Measure:** the covering part's width against the concept's (+11% on B1).
- **Source:** the modeler's B1 edit. D-057 (Provisional).

## Rules that came from it

D-009, D-021, D-032, D-033, D-036, D-037, D-039, D-041, D-044, D-049, D-051,
D-054, D-056, D-057 (Provisional).

## Only this model

- **Heart-shaped wings** (B1): two lobes joined by a thin middle row (1.5 mm
  deep at h 0 near the knot) and a deep tip dent (about 9% in the cage). "É só
  desse conceito, mas em uma quantidade considerável de desenhos os laços são
  em formato de coração. Na vida real eles não são assim." Reading hint: look
  for the heart in a drawn bow's shading and outline; do not model a real bow.
- **The pinch where the wing enters the knot** (B1 round 5, read from the
  cage and measured in sections). In words the AI can act on: *near the knot
  each cross-section of the wing is two round lobes that almost pinch apart
  at h 0. The depth at h 0 is only 0.28-0.32 of the lobe's depth from 15% to
  30% of the width, and opens to 0.6 at 55% and 0.85 past 70%. In the cage:
  the h 0 row stays within about 1.5 mm of the Y plane from the knot to half
  the width, and the row next to it sits close to that row, near h 0 (a
  tight loop, D-039), so Subdivision cannot round the waist away; the lobe's
  round outer side is carried by the rows above.* Sections of the lobes fit a
  superellipse of n 3.0-3.3. Numbers in `measures.json`.
- **Round knot** (B1): cross-sections fit a superellipse of exponent about 2.5
  with 10 cage vertices per 1/8. How round follows the concept (D-051).
- Mirror merge threshold 0.1 mm on `Laço` is the practice (D-054); 1 mm on
  `Laço Nó` is Blender's default, left as it came (Coincidences).
- Geometry Nodes Essentials: `Smooth by Angle` and `Array` elsewhere in the
  file come from Blender's bundled `geometry_nodes_essentials.blend`, packed
  into the file; the "had multiple instances" warning on open is harmless.

## Open questions

- The order of the build: which primitive, where the first loops went.
- The pending deductions above.
- Knot with 10 vertices per 1/8 and Subdivision (B1 round 4): same shape as
  B1's 19-vertex knot without Subdivision, within 0.8 mm. Which one would the
  modeler keep?
