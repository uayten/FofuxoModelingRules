# Chapéu Estilizado para Games (top hat)

- **File:** `../laco/human/Laço.blend` (E1, the same file as the bow tie)
- **Objects:** `Chapéu` (hat), `Fita Azul` (blue ribbon, child), `Estrelas`
  (stars, child)
- **Concept:** `../laco/concept.png`, the hat on the dragon's head
- **Status:** measured; several E1 rules came from it. No dedicated interview.

## Contents

- [File and objects](#file-and-objects)
- [How it was made](#how-it-was-made)
- [Whys](#whys)
- [AI deductions](#ai-deductions)
- [Rules that came from it](#rules-that-came-from-it)
- [Only this model](#only-this-model)
- [Open questions](#open-questions)

## File and objects

| | `Chapéu` | `Fita Azul` | `Estrelas` |
|---|---|---|---|
| Stack | Subdivision 1/2 → Bevel (Weight, 5 segments) → Smooth by Angle | Shrinkwrap ×2 (off) → Subdivision 1/2 → Solidify 7.5 mm → Bevel (Weight, 2.7 mm, 2 segments) | Bevel (Weight, 6 mm, 4 segments) → Array (Geometry Nodes) |
| Cage | 58 vertices, 70 faces | 28 vertices, 14 faces | 22 vertices, 30 faces (one star) |
| Evaluated | 674 vertices, 672 faces | 392 vertices, 392 faces | 1256 vertices, 1360 faces |
| Size, evaluated (local) | 220.0 × 219.9 × 162.0 mm | 160.8 × 160.7 × 56.1 mm | 164.1 × 164.1 × 36.6 mm |
| Edge data | 42 bevel-weight edges, 56 creased | 28 bevel-weight edges | 15 bevel-weight edges |
| Transform | rotated -19.9° on X | parent `Chapéu` | parent `Chapéu` |
| Materials | Vermelho, Azul, Branco | Azul | Branco |

## How it was made

*To be told by the modeler.* Known from E1: the ribbon's base vertices were
extracted from the hat (D-029); the hat was resized later and two Shrinkwraps,
each limited to a vertex group, refit the ribbon (D-026); one star modeled
well, repeated by an Array (D-024).

## Whys

From the E1 interview:

- Localized Bevel goes after Subdivision (D-016).
- Thin strips round their rim with a Bevel after Solidify, not with
  Subdivision (D-027).
- Disabled modifiers may stay on purpose: the Shrinkwraps are kept to refit
  the ribbon if the hat changes again (D-006, D-026).

## AI deductions

| Deduction | Evidence | Status |
|---|---|---|
| The hat is modeled straight and posed by the object rotation | -19.9° on X, nothing applied | pending (matches D-014) |
| One mesh holds three materials instead of three objects | 3 material slots on `Chapéu` | pending: why not separate objects? |
| Crease and bevel weight split the work: crease keeps the silhouette, bevel weight rounds the brim edges | 56 creased and 42 bevel-weight edges | pending |

## Rules that came from it

D-006, D-014, D-016, D-024, D-026, D-027, D-029, D-030.

## Only this model

- The Shrinkwrap settings (`1.003`, `2.003`) and the vertex group names
  `ShrinkWrap` / `Shrwink2` (Coincidences).

## Open questions

- The order of the build and the starting primitive.
- The pending deductions above.
