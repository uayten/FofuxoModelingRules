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
| The bow is about 6% bigger than the concept | 126.1 vs 118.4 mm at the Empty's scale | pending: is the Empty at the model's scale? |
| `Laço Nó` is tilted -6° to follow the chest | rotation on X only | pending |
| The wing's loops radiate from the knot and follow the outline, not columns across the width: the Y-plane rim (8 vertices) runs from the center up to the top corner and around the tip; a ring (5 vertices) goes around the outer lobe | cage text in B1's frame (B1 round 4 self-critique) | pending |
| The whole X-plane column sits within 10% of the height (h 0 to 95 permille), with crease 1.0: the wing narrows almost to a point at the knot (D-037) | same | pending |
| The cage stays outside the surface everywhere, by a steady margin: the tip ring is 1.4 × deeper in the cage than in the result | same: v1 base d 1185, sub 797 | pending |
| The thin middle row (1.5 mm deep) runs from the knot to half the width; past it, the h 0 row is as deep as the lobes | v22 d 66, v3 d 93, v1 d 1185 (base) | pending |

## Rules that came from it

D-009, D-021, D-032, D-033, D-036, D-037, D-039, D-041, D-044, D-049, D-051,
D-054.

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
