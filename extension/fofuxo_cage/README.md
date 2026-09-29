# Fofuxo Cage

A Blender extension that lets an AI and a human take turns editing the same
cage mesh (the base mesh under Subdivision):

- Read a cage as text: every vertex with its base position **and** where it
  lands after the modifier stack, grouped by edge loops, in permille of a
  fixed frame (e.g. the concept's size).
- Edit that text and push it back to the mesh, touching only vertex positions:
  line by line, or with relative ops (`move L1 h +4%`, `scale L3 d 90%`).
- See the model on one image: front, top and side × cage, Subdivision and the
  concept with the model's outline over it, all on the frame's grid.
- Read a human's Blender edits back into the text, including loop cuts, and
  report them in percent of the frame (`v10 h+6.4%`).
- Stop at a conflict instead of overwriting anyone's edit.
- Validate on every sync: quads under Subdivision, no loose geometry, no
  flipped faces, mirror planes respected, at most 255 vertices.

## Contents

- [Install](#install)
- [Use](#use)
- [View sheet](#view-sheet)
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

`sync(name, resolve=None, dry_run=False, render=True)` returns a report:

| key | meaning |
|---|---|
| `action` | `init`, `unchanged`, `pushed` (text → mesh), `pulled` (mesh → text), `conflict`, `error` |
| `text` | path of the cage text |
| `moved`, `deltas` | vertices the push moved, and by how much in percent of the frame |
| `ops` | the ops applied, with the vertex count of each |
| `blender_edits`, `blender_deltas` | vertices the human changed in Blender since the last sync, and by how much |
| `render` | path of the view sheet (`<object>.png` next to the text) |
| `issues` | validation results, `ERROR` or `WARN`, with the vertices involved |
| `frame`, `size`, `count` | the frame, base and evaluated sizes (mm) and counts |

`set_frame(name, w=None, d=None, h=None, concept=None)` resizes the frame to
full visible sizes in mm. With `concept={"image": ..., "box": [x0, x1, y0,
y1]}` (pixels, top-left origin) the frame takes the box's width and height and
the view sheet draws that box behind the model. The mesh does not move; only
the numbers in the text change. It syncs first and stops at a conflict.

To find a part's box in the concept:

```python
color = fofuxo_cage.sample("EUA-Frente.png", 560, 750)      # a pixel on the part
found = fofuxo_cage.find_box("EUA-Frente.png", color, tol=0.25, roi=[480, 760, 650, 850])
fofuxo_cage.set_frame("Laço", concept={"image": "EUA-Frente.png", "box": found["box"]})
```

The text lives next to the .blend: `<file>.cage/<object>.txt`. The last synced
state is in `<file>.cage/.state/`. The object must be in Object Mode.

## Other views

```python
fofuxo_cage.views("Laço", [(45, 30), (45, -30), "back", "90,20"])
```

Renders the current mesh (no sync) from any camera: rows of cage and
subdivision panels, written to `<object>.views.png` (or
`<object>.<render_name>.png`). A view is a preset (`front`, `back`, `left`,
`right`, `top`, `bottom`), a `"yaw,pitch"` string or a `(yaw, pitch)` pair in
degrees: yaw 0 looks from the front, 90 from the right; pitch > 0 looks from
above. The default is 3/4 from above, 3/4 from below and 3/4 from the back.

## View sheet

Written on every sync (`render=False` skips it), drawn on the CPU: no GPU, no
screen, no change to the scene, so it works the same from the MCP and in
background mode. About 0.7 s for the bow tie.

| | cage | subdivision | concept |
|---|---|---|---|
| **front** (w, h) | mirrored cage, base vertices with ids, poles in orange | shaded result, base cage wire | concept box + the result's outline in blue |
| **top** (w, d) | same | same | an Image Empty facing this view, if any |
| **side** (d, h) | same | same | same |

The object's parent, children and siblings (e.g. `Laço Nó` around `Laço`)
are drawn gray in the subdivision panels and join the outline. Vertex labels
never overlap each other or another vertex dot; a label placed away from its
vertex gets a leader line.

Every panel carries the frame grid: thin lines at a step that stays readable,
the mirror plane (0) in blue and the frame edge (1000) in orange, labeled in
permille. All panels share one scale.

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
- **ops**: relative edits, applied in order and then cleared:
  - `move <targets> <axes> <+N%>`: move by N% of the frame (1% = 10 permille);
  - `scale <targets> <axes> <N%>`: scale around the targets' center;
  - `scale <targets> <axes> <N%> from 0`: scale from the mirror plane.

  Targets are ids (`v7`), loop labels (`L1`, `rest`) or `all`; axes are
  letters from `w`, `d`, `h`. Coordinates on a mirror plane stay on it. An op
  starts from the vertex's exact position, so it adds no rounding. A bad op
  writes nothing.

  Ops that change the object instead of positions (D-052):
  - `add <type> [as <name>] [at <place>]`: a modifier of a Blender type
    (`SUBSURF`, `MIRROR`, `BEVEL`, `SOLIDIFY`, `WEIGHTED_NORMAL`...), with its
    default name (D-006) unless `as` names it, at the end unless placed;
  - `remove <modifier>`, `reorder <modifier> to <place>`;
  - `set <modifier> <property> <value>`, e.g. `set Subdivision render_levels 2`;
  - `apply <modifier>`: destructive; only in the cases the skill allows. New
    vertices (e.g. from a Mirror) get fresh ids;
  - `crease <edges> <value>`: edges as `vA-vB`, a loop label or
    `plane-x` / `plane-y` / `plane-z` (every edge on that mirror plane), e.g.
    `crease plane-x 1.0` to pinch where a part enters another.

  A place is `first`, `last`, a 1-based position, `before <modifier>` or
  `after <modifier>`; names with spaces go in quotes. The whole batch is
  checked against a simulated stack first, so a bad op changes nothing, and a
  batch may refer to a modifier it adds.
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

- No topology ops yet (insert or remove loops): topology changes come from the
  human in Blender.
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
