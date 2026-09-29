# Fofuxo Cage

A Blender extension that lets an AI and a human take turns editing the same
cage mesh (the base mesh under Subdivision):

- Read a cage as text: every vertex with its base position **and** where it
  lands after the modifier stack, grouped by edge loops, in permille of a
  fixed frame (e.g. the concept's size).
- Edit that text and push it back to the mesh, touching only vertex positions:
  line by line, with relative ops (`move L1 h +4%`, `scale L3 d 90%`), or by
  where a vertex should land after Subdivision (`target v22 w 945 d 440`).
- See the model on one image: front, top and side × cage, Subdivision and the
  concept with the model's outline over it, all on the frame's grid.
- Read a human's Blender edits back into the text, including loop cuts, and
  report them in percent of the frame (`v10 h+6.4%`).
- Read and change the modifier stack as text: every modifier's key settings
  and what it does to the mesh (`set Mirror merge_threshold 0.1mm`).
- Stop at a conflict instead of overwriting anyone's edit, and lock the
  object (or all of Blender's input) while the AI edits.
- Move the modeled part to the other side of a mirror plane (`flip`), e.g. to
  model on -Y, in front of its mirror copy.
- Change topology from the text: remove an edge loop (`dissolve sharp`, the
  loop the human marked) or cut a new one (`cut v25-v22`).
- Measure in numbers instead of images: outlines from a view, cuts across
  the model with their roundness and waist, the distance to a captured
  surface or to a reference file; fit a cage to a surface; take another
  object's topology and fit it (`rebuild`).
- Validate on every sync: quads under Subdivision, no loose geometry, no
  flipped faces, mirror planes respected, at most 255 vertices.

## Contents

- [Install](#install)
- [Use](#use)
- [Shape tools](#shape-tools)
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
| `modifiers` | the modifiers section of the text (settings and effect of each); only when the stack changed, or with `verbose=True` |
| `stack_changes` | modifier lines that changed since the last sync (a `set` op or a change in Blender) |

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

`flip(name, axis="d")` mirrors every base vertex across the plane of a
mirrored axis and rewinds the faces: the model looks the same, the values in
the text stay the same (they count from the plane) and the frame now measures
toward the other side. Model on -Y (D-055): a sync warns `modeled_behind`
when the base mesh sits on +Y, behind its mirror copy in the front view.

The text lives next to the .blend: `<file>.cage/<object>.txt`. The last synced
state is in `<file>.cage/.state/`. The object must be in Object Mode.

### Lock

```python
fofuxo_cage.lock("Laço")            # take control: leave Edit Mode, lock the object, block input
fofuxo_cage.lock("Laço", ui=False)  # only the object lock
fofuxo_cage.unlock()                # release everything
```

The AI locks before it edits and unlocks when it hands back. Taking control
leaves Edit Mode first: the human's edits are written into the mesh and the
next sync reports them as Blender edits.

While locked, the 3D View header and the status bar say which objects the AI
is editing. The human can always take over: Esc while the input is blocked,
or **Unlock** in the 3D View sidebar (Fofuxo tab). The next sync then warns
`human_took_over`: the AI stops and asks. A lock survives a save (the object's
selectability is kept in a custom property), and `unlock` restores it.

## Other views

```python
fofuxo_cage.views("Laço", [(45, 30), (45, -30), "back", "90,20"])
```

Renders the current mesh (no sync) from any camera: rows of cage and
subdivision panels, written to `<object>.views.png` (or
`<object>.<render_name>.png`). `focus=[13, 14]` labels only those vertices
(the rest are small gray dots), `ghost=True` fills only the base part and
draws the mirror copies as faint wire, `normals=True` adds a tick along the
result's normal at each vertex. A view is a preset (`front`, `back`, `left`,
`right`, `top`, `bottom`), a `"yaw,pitch"` string or a `(yaw, pitch)` pair in
degrees: yaw 0 looks from the front, 90 from the right; pitch > 0 looks from
above. The default is 3/4 from above, 3/4 from below and 3/4 from the back.

## Shape tools

Numbers cost fewer tokens than images and compare exactly. Every measure runs
on a dense copy of the result (Subdivision raised to 3 levels for the
measure, then restored), close to the limit surface.

```python
fofuxo_cage.capture("Laço", key="r3", path="wing_r3.npz")   # keep the current surface
fofuxo_cage.fit("Laço", "r3")                  # target ops that put the result on it, synced
fofuxo_cage.deviation("Laço", "r3")            # signed distance, mm: min, p5, median, p95, max
fofuxo_cage.profile("Laço", "top")             # half depth band by band along the width
fofuxo_cage.sections("Laço", "w", [150, 280, 560])   # cuts: exponent n, waist, image
fofuxo_cage.compare("Laço", "Laço", blend="models/tasks/laco/human/Laço.blend")
fofuxo_cage.rebuild("Laço Nó", "Laço Nó", "knot", blend=".../human/Laço.blend")
```

- `capture(name, key=None, path=None)`: the surface lives in memory for the
  session (a reload of the extension forgets it); `path` also saves a .npz
  that any later call accepts in place of the key.
- `fit(name, surface, mode="normal", vids=None, passes=3)`: per vertex, the
  point of the surface along the result's normal (`radial`: along the ray
  from the center, good for round parts; `nearest`), written as `target` ops
  and synced, `passes` times. Returns the deviation after.
- `profile(name, view)`: `top` (half depth along the width), `front` (half
  height along the width), `side` (half depth along the height). Each row:
  fraction of the extent, the largest value in mm, and the same near the
  middle plane (e.g. the depth at h 0 seen from the top).
- `sections(name, axis, at)`: cuts at frame values (permille). Per cut: the
  superellipse exponent n of the result's section (2 = ellipse, higher =
  boxier), its size, the waist (the depth where h is 0, and its ratio to the
  largest depth: how deep a pinch goes) and the base vertices within 3% of
  the plane. The image `<object>.sections.png` shows the result's section in
  orange, the cage's in dark, and those vertices labeled.
- `compare(name, ref, blend=None)`: sizes, the three profiles side by side
  and the deviation from the reference; `blend` borrows the object from a
  file for the call and removes it after.
- `rebuild(name, source, surface, blend=None)`: the mesh of `name` takes the
  topology of `source` (mirrored to this object's kept sides, scaled to the
  surface, UVs kept), the next sync pulls it, then `fit` runs. How B1's knot
  got the modeler's 10 vertices.

`models/example/laco/measures.json` keeps these measures for the modeler's
bow tie, so a session reads them instead of measuring again.

A sync also checks editability: `cage_dips` warns about a vertex that sits
inside the average of its neighbours while the surface over it bulges out
(dragging it moves the surface in a way that is hard to predict, D-043). A
concave cage under a groove is fine.

## View sheet

Written on every sync (`render=False` skips it), drawn on the CPU: no GPU, no
screen, no change to the scene, so it works the same from the MCP and in
background mode. About 0.7 s for the bow tie.

| | cage | subdivision | concept |
|---|---|---|---|
| **front** (w, h) | mirrored cage, base vertices with id numbers, poles ringed | shaded result, base cage wire | concept box + the result's outline in blue |
| **top** (w, d) | same | same | an Image Empty facing this view, if any |
| **side** (d, h) | same | same | same |

The object's parent, children and siblings (e.g. `Laço Nó` around `Laço`)
are drawn gray in the subdivision panels and join the outline.

Vertex labels:

- the id number only (`7` for `v7`), placed off the model when there is room,
  6 px apart from each other, never over a vertex dot;
- the dot, the leader line and the number share one color from a palette of
  ten, and vertices that share a face never share a color (the same vertex
  keeps its color in every panel);
- leaders avoid crossing each other, crossing a label and passing within
  5 px of another vertex; the placement gives those up one at a time only
  when there is no spot left, and a last pass swaps two crossing labels;
- vertices that land within 4 px share one label (`2 9 16`), with a dark
  leader;
- a vertex hidden behind the model (not counting its own mirror copy on the
  same pixel) is drawn hollow, with a dashed leader and a paler number.

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

modifiers
  Mirror (MIRROR)  -> v 154  f 152  size 135.1 x 39.1 x 75.7 mm
      use_axis XYZ  use_bisect_axis -  use_clip on  use_mirror_merge on  merge_threshold 0.1mm
  Subdivision (SUBSURF)  -> v 610  f 608  size 126.1 x 28.1 x 68.4 mm
      levels 1  render_levels 2  quality 3  use_limit_surface on  boundary_smooth ALL

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
- **modifiers**: written by the plugin, read-only. Per modifier, a line with
  its effect (vertices, faces and full size of the result up to that
  modifier, measured by evaluating the stack that far) and lines of settings:
  the ones that matter for its type plus every other one that differs from
  Blender's default. The names are Blender's property identifiers, ready for
  `set`. Lengths in mm, angles in degrees, booleans on/off, axis flags as
  letters.
- **faces**, **edges**: written by the plugin, read-only.
- **ops**: relative edits, applied in order and then cleared:
  - `move <targets> <axes> <+N%>`: move by N% of the frame (1% = 10 permille);
  - `scale <targets> <axes> <N%>`: scale around the targets' center;
  - `scale <targets> <axes> <N%> from 0`: scale from the mirror plane.

  Targets are ids (`v7`), loop labels (`L1`, `rest`) or `all`; axes are
  letters from `w`, `d`, `h`. Coordinates on a mirror plane stay on it. An op
  starts from the vertex's exact position, so it adds no rounding. A bad op
  writes nothing.

  To place the result instead of the cage:
  - `target <vid> <axis> <value> [<axis> <value> ...]`: where the vertex
    lands after the stack (its sub column), e.g. `target v22 w 945 d 440`.
    The sync solves the base after every other op: each step adds the
    remaining error to the base and evaluates again, until every target is
    within 0.25 permille (at most 40 steps; `target_not_reached` warns
    otherwise). Axes not named keep their base value; a vertex on a mirror
    plane cannot target the axis across it, and no base value comes closer
    to a mirror plane than 1.5 × the merge distance (a weld would reorder the
    evaluated vertices; keep the merge distance very small, D-054). Needs the sub columns (Mirror and Subdivision). Use
    it to match a measured shape: write the outline you want in sub values
    and let the tool find the cage.

  Ops that change the object instead of positions (D-052):
  - `add <type> [as <name>] [at <place>]`: a modifier of a Blender type
    (`SUBSURF`, `MIRROR`, `BEVEL`, `SOLIDIFY`, `WEIGHTED_NORMAL`...), with its
    default name (D-006) unless `as` names it, at the end unless placed;
  - `remove <modifier>`, `reorder <modifier> to <place>`;
  - `set <modifier> <property> <value>`, e.g. `set Subdivision render_levels 2`,
    `set Mirror merge_threshold 0.1mm`, `set Mirror use_axis XZ`,
    `set Mirror mirror_object Chest`. A length needs a unit (`mm`, `cm`, `m`)
    and an angle one (`deg`, `rad`): a bare number is refused, so a value in
    mm is never read as meters;
  - `apply <modifier>`: destructive; only in the cases the skill allows. New
    vertices (e.g. from a Mirror) get fresh ids;
  - `crease <edges> <value>`: edges as `vA-vB`, a loop label,
    `plane-x` / `plane-y` / `plane-z` (every edge on that mirror plane) or
    `sharp` (every edge marked sharp in Blender), e.g. `crease plane-x 1.0`
    to pinch where a part enters another;
  - `dissolve <edges>`: remove the edge loop those edges make; the faces on
    both sides merge and the loop's vertices go away. A loop that turns at a
    pole takes the pole's last spoke with it. `dissolve sharp` removes the
    loop the human marked sharp. Refused when it would leave anything but
    quads;
  - `cut <vA-vB> [N]`: cut N new loops (default 1) across the edge ring that
    holds edge vA-vB. New vertices get fresh ids; place them in a later sync
    (or with `target` ops, once their ids are known).

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

- Topology ops are `dissolve` and `cut` only; anything else comes from the
  human in Blender or from `rebuild`, and the next sync pulls it. A mesh
  rebuilt from scratch has lost its id attribute, so the pulled vertices take
  ids from their index.
- Mirror planes are the object's local planes; a Mirror with a mirror object
  or bisect is not supported.

## Tests

```bash
blender -b --factory-startup --python extension/fofuxo_cage/tests/test_roundtrip.py --python-exit-code 1
```

The test copies `models/example/laco/human/Laço.blend` to a temporary folder and never
touches the original. Read the last line (`ALL PASSED (N checks)`): Blender
exits 0 when the test file fails to parse, so the exit code alone can lie.

## Why

The bow tie test (T1) showed models fail at execution more than perception:
loops too far apart, flipped faces, cages that Subdivision shrinks out of
shape. This tool takes topology bookkeeping away from the AI and shows it the
subdivided result next to every vertex. See D-048 and D-049 in
`DECISIONS.md`.
