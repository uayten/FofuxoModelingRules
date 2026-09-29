# Fofuxo Cage

A Blender extension that lets an AI and a human take turns editing the same
cage mesh (the base mesh under Subdivision):

- Read a cage as text: every vertex with its base position **and** where it
  lands after the modifier stack, grouped by edge loops, in permille of a
  fixed frame (e.g. the concept's size).
- Edit that text and push it back to the mesh, touching only vertex positions.
- Read a human's Blender edits back into the text, including loop cuts.
- Stop at a conflict instead of overwriting anyone's edit.
- Validate on every sync: quads under Subdivision, no loose geometry, no
  flipped faces, mirror planes respected, at most 255 vertices.

## Contents

- [Install](#install)
- [Use](#use)
- [Text format](#text-format)
- [Round trip rules](#round-trip-rules)
- [Limits of v0.1](#limits-of-v01)
- [Tests](#tests)
- [Why](#why)

## Install

Preferences > Get Extensions > Repositories > **+** > Add Local Repository,
pointing at the `extension/` folder of this repository (module name
`fofuxo`). Then enable *Fofuxo Cage*. Code changes load on the next Blender
start (or by disabling and enabling the extension).

## Use

From the Blender MCP (`execute_blender_code`):

```python
import fofuxo_cage
result = fofuxo_cage.sync("Laço")
```

`sync(name, resolve=None, dry_run=False)` returns a report:

| key | meaning |
|---|---|
| `action` | `init`, `unchanged`, `pushed` (text → mesh), `pulled` (mesh → text), `conflict`, `error` |
| `text` | path of the cage text |
| `moved` | vertices the push moved |
| `blender_edits` | vertices the human changed in Blender since the last sync |
| `issues` | validation results, `ERROR` or `WARN`, with the vertices involved |
| `frame`, `size`, `count` | the frame, base and evaluated sizes (mm) and counts |

`set_frame(name, w=None, d=None, h=None)` resizes the frame to full visible
sizes in mm (e.g. the concept's bow tie: `w=118.4, h=62.5`). The mesh does not
move; only the numbers in the text change. It syncs first and stops at a
conflict.

The text lives next to the .blend: `<file>.cage/<object>.txt`. The last synced
state is in `<file>.cage/.state/`. The object must be in Object Mode.

## Text format

```
object   Laço
frame    w X- 59.2   d Y- 14.0   h Z+ 31.2   (mm)
stack    Mirror(XYZ) > Subdivision(1/2)
size     base 135.2 x 39.2 x 75.6   sub 126.1 x 28.1 x 68.4   (mm, w x d x h)
count    v 28  f 19   evaluated v 610 f 608

verts
# loop  id   base w     d     h | sub w     d     h | flags
L1      v0     1041     0     0 |  1003     0     0 | Y Z
        v7      758     0  1210 |   713     0  1075 | Y
        ...
L3      v10     652   857  1005 |   669   650   960 | pole3

faces
  f0   v25 v22 v2 v14
edges
  crease 1.0  v2-v14 v6-v11 ...
ops
forms
```

- **frame**: a fixed box the values are measured in. `w X- 59.2` means width
  is measured along X from the mirror plane toward -X, and 1000 = 59.2 mm. On
  an axis without Mirror it reads `X lo..hi` (0 = lo, 1000 = hi). The first
  sync frames the evaluated result; `set_frame` changes it. It never changes
  because a vertex moved, so values stay comparable across syncs.
- **base w d h**: the only thing to edit, in whole permille of the frame. On a
  mirrored axis there is no sign: 0 is on the plane, and a negative value
  means crossing it (refused). Past 1000 is fine (outside the frame). A line
  may be rewritten loosely (`v7 758 0 1100`); the sub columns can be dropped.
  1 permille is 0.06 mm on the bow tie's width.
- **sub w d h**: where the vertex lands after the stack. Read-only. Shown only
  while the stack is Mirror and Subdivision (base vertex *i* is evaluated
  vertex *i* there; checked exactly with the Catmull-Clark formula).
- **size**: in mm, for real-size checks (D-038).
- **loop**: vertices are grouped by edge loops, longest first; `rest` holds
  vertices on no loop. `L1` on the bow tie is the rim on the Y plane: the front
  silhouette.
- **flags**: the mirror planes the vertex lies on, and `poleN` when the vertex
  will have valence N ≠ 4 once mirrored.
- **faces**, **edges**: written by the plugin, read-only.
- **ops**: topology commands (not implemented yet).
- **forms**: free text kept verbatim across syncs: the shape map of D-043.

## Round trip rules

| text | mesh | sync does |
|---|---|---|
| changed | same | push the changed vertices only; the rest stay bit-identical |
| same | changed | pull: rewrite the text from the mesh, keeping `forms` |
| changed | changed | **conflict**: writes nothing, lists both sides |

After a conflict, the human decides: `resolve="mesh"` keeps the Blender edit and
saves the text edit to `<object>.rejected.txt`; `resolve="text"` applies the
text edit over it.

- A vertex on a mirror plane stays on it (its coordinate across the plane is
  kept at 0, with a warning).
- A vertex pushed across a mirror plane is refused and nothing is written.
- Vertex ids live in the `fofuxo_cage_id` point attribute. Vertices new since
  the last sync (a loop cut, an extrude) get fresh ids; old ids never move to a
  new vertex.
- Only vertex positions and that attribute are written. Modifiers, materials,
  parent, crease, seams, UVs and vertex groups are not touched. Each push adds
  an undo step.

## Limits of v0.1

- No ops yet: topology changes come from the human in Blender.
- No render yet (next phase).
- Mirror planes are the object's local planes; a Mirror with a mirror object
  or bisect is not supported.

## Tests

```bash
blender -b --factory-startup --python extension/fofuxo_cage/tests/test_roundtrip.py --python-exit-code 1
```

The test copies `models/example/laco/human/Laço.blend` to a temporary folder and never
touches the original.

## Why

The bow tie test (T1) showed models fail at execution more than perception:
loops too far apart, flipped faces, cages that Subdivision shrinks out of
shape. This tool takes topology bookkeeping away from the AI and shows it the
subdivided result next to every vertex. See D-048 and D-049 in
`DECISIONS.md`.
