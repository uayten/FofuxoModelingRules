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
- Give the AI a Blender of its own (a black screen, the MCP server) and the
  human a normal one with the model appended; read back what the human saves
  there (`review`, `absorb`).
- Move the modeled part to the other side of a mirror plane (`flip`), e.g. to
  model on -Y, in front of its mirror copy.
- Run Blender's own mesh operators from one line of text, on a selection by
  cage id: `mesh loopcut_slide ring v25-v22 number_cuts=2`, `mesh translate
  seam d=+3% falloff=smooth radius=25%` (proportional editing). Walk loops,
  rings and paths with Blender's selection tools; read the marks the human
  left (`sharp`, `seam`, `crease`). Every op is tried on a copy first and
  reported in numbers.
- Measure in numbers instead of images: outlines from a view, cuts across
  the model with their roundness and waist, the distance to a captured
  surface or to a reference file; fit a cage to a surface; take another
  object's topology and fit it (`rebuild`).
- Validate on every sync: quads under Subdivision, no loose geometry, no
  flipped faces, mirror planes respected, at most 255 vertices.

## Contents

- [Install](#install)
- [Use](#use)
- [Mesh op](#mesh-op)
- [Shape tools](#shape-tools)
  - [Task targets](#task-targets)
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

In its own Blender (below) the AI needs no lock. In a Blender the human is
using, the AI locks before it edits and unlocks when it hands back. Taking control
leaves Edit Mode first: the human's edits are written into the mesh and the
next sync reports them as Blender edits.

While locked, the 3D View header and the status bar say which objects the AI
is editing. The human can always take over: Esc while the input is blocked,
or **Unlock** in the 3D View sidebar (Fofuxo tab). The next sync then warns
`human_took_over`: the AI stops and asks. A lock survives a save (the object's
selectability is kept in a custom property), and `unlock` restores it.

### Two Blenders: the AI's and the human's review

The AI works in a Blender of its own (D-058). The launcher starts it:

```bash
python extension/fofuxo_cage/launcher.py models/tasks/laco/ai/B1-opus-cage/B1.blend
```

- Plain Python, no bpy: it starts Blender with `-- --fofuxo-ai`, waits for
  the MCP port (9876) and prints `{"started": true, "pid": ..., "listeners":
  [...]}`. If an AI instance is already running it starts nothing; open the
  file there instead.
- The AI's instance shows one black area with the notice "Fofuxo Cage:
  Blender exclusivo da AI" (Blender's focus mode: no top bar, no status
  bar), swallows every input event (the window's close button still works)
  and keeps its MCP server on. Saving writes the file's own layout, not the
  focus mode. `say(text)` adds a status line under the notice.
- A human's Blender with Fofuxo Cage looks every 3 s for a live AI instance
  and then stops its own MCP server, so the MCP always reaches the AI's
  (Blender's server binds with `SO_REUSEADDR`: on Windows two Blenders can
  hold the port and nothing tells which one answers). An older Blender
  needs `fofuxo_cage.release_mcp()`, or its MCP server stopped by hand.
- `instance()` says which Blender answers: `{"role": "ai" | "human", ...}`.

```python
fofuxo_cage.review(["Concept", "Laço", "Laço Nó"])   # default: every object in the scene
fofuxo_cage.absorb()                                  # what the human saved comes back
```

- `review(names)` saves the AI's file and opens a normal Blender that loads
  the human's startup file without its objects, appends those objects from
  the AI's file (the AI's lock left out, the units kept) and saves
  `<file>.cage/review.blend`. The human edits there and saves (Ctrl+S).
- While that Blender is open, `review()` again only writes
  `review.update.json`: the human's Blender shows it in the 3D View header,
  and **Load AI update** in the Fofuxo tab replaces those objects with the
  AI's saved version (mesh, modifiers, transform).
- `absorb()` does the same the other way: mesh, modifiers and transform of
  the reviewed objects come from `review.blend` into the AI's objects, and
  each one syncs, so the human's changes come back as `blender_edits` and
  `blender_deltas`. It only counts saves made after the review opened;
  nothing new returns `{"changed": false}`. References between the objects
  (a Mirror's object, a parent) and materials go to the AI's own datablocks;
  nothing loaded is left behind.

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

## Mesh op

```
mesh <operator> <selection> [key=value ...]
```

One line in the ops section (or `fofuxo_cage.edit(name, line)`, which writes
the line and syncs) runs one of Blender's mesh operators:

```python
fofuxo_cage.edit("Laço", "mesh translate seam d=+3% falloff=smooth radius=25%")
fofuxo_cage.edit("Laço", "mesh loopcut_slide ring v25-v22 number_cuts=2")
fofuxo_cage.select("Laço", "loop v25-v22")   # preview: the ids a selection names
print(fofuxo_cage.mesh_help())               # the operators and their parameters
```

**Selection** (shared with `crease` and `dissolve`; terms add up):

| term | selects |
|---|---|
| `v25` | a vertex |
| `v25-v22` | an edge |
| `L3` | the edges between the consecutive vertices of a loop label |
| `plane-x`, `plane-y`, `plane-z` | every edge on that mirror plane |
| `sharp`, `seam`, `crease` | every edge the human marked so (crease: weight above 0) |
| `loop vA-vB` | the edge loop through vA-vB (Blender's `select_edge_loop_multi`) |
| `ring vA-vB` | the edge ring through vA-vB (`select_edge_ring_multi`) |
| `path vA vB` | the shortest path of edges from vA to vB (`shortest_path_select`) |
| `faces vA vB vC vD` | every face whose vertices are all in the list |
| `all` | everything |

**Operators** (the whitelist; anything else is refused with the list):

| operator | Blender | parameters |
|---|---|---|
| `dissolve_edges` | `mesh.dissolve_edges` | `use_verts` (default on), `use_face_split` |
| `dissolve_verts` | `mesh.dissolve_verts` | `use_face_split`, `use_boundary_tear` |
| `delete_edgeloop` | `mesh.delete_edgeloop` | `use_face_split` |
| `loopcut_slide` | `mesh.loopcut_slide` across the ring of the first edge named | `number_cuts` (1), `smoothness` (0), `falloff`, `slide` (-1 to 1, 0 = halfway) |
| `subdivide_edgering` | `mesh.subdivide_edgering` on a selected ring | `number_cuts` (1), `smoothness` (0), `interpolation` |
| `vertices_smooth` | `mesh.vertices_smooth` | `factor` (0 to 1), `repeat`, `xaxis`, `yaxis`, `zaxis` |
| `translate` | `transform.translate` | `w`, `d`, `h`: the move, in % of that frame axis or mm, + away from the mirror plane; `falloff`, `radius` (% of the frame's largest axis, or mm), `connected`: proportional editing, on when either of the first two is given |

| `edge_slide` | `transform.edge_slide` | `factor` (-1 to 1, toward one neighbour loop or the other), `even`, `flipped`, `clamp` |
| `vert_slide` | `transform.vert_slide` | `factor` (-1 to 1 along the vertex's edge), `even`, `flipped`, `clamp` |
| `shrink_fatten` | `transform.shrink_fatten` | `value` (length, + outward along the normals), `even`; proportional editing |
| `push_pull` | `transform.push_pull` | `value` (length, + away from the selection's center); proportional editing |
| `tosphere` | `transform.tosphere` | `factor` (0 to 1); proportional editing |
| `looptools_circle` | LoopTools circle | `fit` (best, inside), `flatten`, `influence` (0 to 100), `radius` (length), `regular`, `lock_x/y/z`. A closed loop only: a loop that ends on a mirror plane is half a circle, and circling it breaks the plane (refused) or the shape |
| `looptools_relax` | LoopTools relax | `iterations` (1, 3, 5, 10, 25), `interpolation` (cubic, linear), `regular` |
| `looptools_space` | LoopTools space | `influence` (0 to 100), `interpolation`, `lock_x/y/z` |
| `symmetrize` | `mesh.symmetrize` | `direction` (negative_x ... positive_z), `threshold` (length): for a part modeled whole; on a mirrored half it crosses the plane and is refused |
| `symmetry_snap` | `mesh.symmetry_snap` | `direction`, `threshold`, `factor`, `use_center` |

The shaping ops are the ones that move a region the way a modeler would
(the round-5 lesson: moving single vertices bends the cage). `translate`
with `falloff` is the pull with falloff. `vertices_smooth_laplacian` was
tried and left out: on a cage of 28 vertices it moves nothing on a part of
the mesh and blows up the whole mesh at the strength that moves it.
Values: on/off, numbers, enum names in any case, lengths with a unit (`2mm`)
or in % of the frame.

**Running:** the object is locked for the op (which takes it out of the
human's Edit Mode, keeping the edits), enters Edit Mode alone, the selection
is set by id, the operator runs under a 3D View override (auto merge and
snapping off), and the object leaves Edit Mode. The human's active object,
selection, select mode and proportional settings come back after. Vertices
the operator made get fresh ids (each vertex carries a random tag through the
operator; one that comes back with an interpolated tag is new).

**Safety:** the whole batch first runs on a temporary copy of the object; an
op that fails there (Blender refuses, the selection is empty, or the result
breaks a rule: quads under Subdivision, no loose geometry, mirror planes)
refuses the batch and nothing is written. On the object itself the mesh is
copied before each op and restored if a check fails.

**Report:** one line per op: vertices added and removed with their ids,
faces before and after, `all quads`, how many vertices moved, how far the
surface moved (max and mean, mm, on a dense copy), how each view's outline
changed (the band that moved most, from `profile`: `top +0.6 mm at 0.60` is
at 60% of the width) and the largest moves in percent of the frame:

```
mesh shrink_fatten faces v14 v15 v26 v27 v20 v28 v22 v32 v33 value=0.6mm falloff=smooth radius=20%
  (+0 v, -0 v, faces 19 -> 19, all quads, moved 14 v, surface moved: max 0.57 mm, mean 0.23 mm,
  profile top +0.6 mm at 0.60, front +0.1 mm at 0.50, side +0.7 mm at 0.30; v22 d+3.6% ...)
```

When `edit()` is refused (an error or a conflict), the text goes back to
what it was before the call, so a refused line never runs with the next one.

**Aliases** kept from before the mesh op: `dissolve <selection>` is
`mesh dissolve_edges <selection>`; `cut <vA-vB> [N]` is `mesh loopcut_slide
vA-vB number_cuts=N`; `crease <selection> <value>` sets the crease weight of
the selected edges.

**LoopTools** is part of the toolset. `fofuxo_cage.ensure_looptools()`
enables it when it is on disk in any extension repository, and otherwise
installs it from extensions.blender.org (online access is turned on for the
install and restored after). It runs a few seconds after the extension loads
in a Blender with a window, and before any LoopTools op.

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

### Task targets

A task's `target.md` may hold a ` ```targets ` block: one line per measure
with its target, tolerance and why (`models/tasks/laco/target.md`).

```
# object   measure              target   tolerance  why
Laço       faces                19       +20%       the modeler's wing (D-045, D-046)
Laço       size w               124.4mm  6%         the concept's width (D-056)
Laço       section w 0.15 waist 0.32     0.06       the pinch into the knot (D-039)
Laço       profile top 0.75     14.5mm   1.5mm      the lobe's half depth from the top
"Laço Nó"  faces                5        +20%       the modeler's knot
```

- Measures: `faces`, `verts` (the base cage), `evaluated faces`,
  `size w|d|h` (the full result, mm), `section <axis> <fraction> n|waist`
  (a cut at a fraction of the part's half size from its mirror plane: the
  superellipse exponent, or the waist ratio), `profile top|front|side
  <fraction>` (mm). Tolerance: `5%`, `0.05` or `1mm` both ways, `+20%` only
  above, `-10%` only below.
- `fofuxo_cage.check_targets(names=None, path=None)` measures every line:
  `{"in": 14, "out": 1, "results": ["in  Laço faces = 19 (target 19 +20%) ...",
  "OUT Laço profile top 0.75 = 16.7mm (target 14.5 ±1.5mm) ..."]}`. The AI
  stops when every line is in; the modeler judges what the numbers miss.
- target.md is found by walking up from the .blend's folder. Every sync
  checks the count lines (the poly budget) and warns `poly_budget` past
  them: "muito high poly" is caught before the modeler sees it.

A sync also checks editability: `cage_dips` warns about a vertex that sits
inside the average of its neighbours while the surface over it bulges out
(dragging it moves the surface in a way that is hard to predict, D-043). A
concave cage under a groove is fine, and a dip can be on purpose: the
modeler's B1 knot dips at its sides where it hugs the wings (D-057). Read it
as a question, not an error.

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
  - `crease <selection> <value>`: the crease weight of the selected edges
    (the selection grammar of the [mesh op](#mesh-op)), e.g. `crease plane-x
    1.0` to pinch where a part enters another;
  - `mesh <operator> <selection> [key=value ...]`: one of Blender's mesh
    operators; see [Mesh op](#mesh-op). `dissolve <selection>` and
    `cut <vA-vB> [N]` are its aliases for removing and cutting loops.

  A place is `first`, `last`, a 1-based position, `before <modifier>` or
  `after <modifier>`; names with spaces go in quotes. The whole batch is
  checked against a simulated stack first and its mesh ops run on a copy, so
  a bad op changes nothing, and a batch may refer to a modifier it adds.
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
- A push writes only vertex positions and that attribute. Modifiers,
  materials, parent, crease, seams, UVs and vertex groups change only through
  an op that names them (`set`, `crease`, `mesh`...). Each push adds an undo
  step.

## Limits of v0.1

- Topology ops are the whitelist of the mesh op; anything else comes from
  the human in Blender or from `rebuild`, and the next sync pulls it. A mesh
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
