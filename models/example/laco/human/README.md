# E1: dragon + "Roupa Estadunidense" outfit

The modeler's file. Focus: the bow tie (`Laço`, `Laço Nó`), the reference
answer for `models/tasks/laco/`.

## Bow tie, measured

| | `Laço` | `Laço Nó` (child of `Laço`) |
|---|---|---|
| Stack | Mirror XYZ (clip, merge 0.1 mm) → Subdivision 1/2 | Mirror XYZ (merge 1 mm) → Subdivision 1/2 |
| Cage per 1/8 | 28 vertices, 19 quads | 10 vertices, 5 quads |
| Evaluated | 610 vertices, 608 faces | 162 vertices, 160 faces |
| Size, evaluated | 126.1 × 28.1 × 68.4 mm | 29.7 × 26.0 × 35.1 mm |

- The `Laço` cage is one patch with three corners on the mirror planes and a
  single valence-3 pole (v10). Its boundary on the Y plane is the front
  silhouette (D-049).
- Crease 1.0 on the edges of the X plane holds the pinch into the knot.
- Subdivision pulls the wing 9 mm shorter and 11 mm thinner than the cage
  (D-033).
- The concept's bow tie measures 118.4 × 62.5 mm at this file's Image Empty
  scale (124.4 × 65.7 mm in `models/tasks/laco/start.blend`, whose Empty is scaled
  differently).

## Geometry Nodes Essentials (harmless warning)

`Smooth by Angle` (on `Chapéu`), `Array` (on `Estrelas`) and its dependency
`Randomize Transforms` come from Blender's bundled
`geometry_nodes_essentials.blend`. Blender 5 links them with their data
packed into this file, so they work even though the library paths do not
resolve. The file holds four entries for that same library (saved from
folders of different depths), hence the "had multiple instances" warning on
open.
