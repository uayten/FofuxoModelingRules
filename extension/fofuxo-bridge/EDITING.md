# Editing the cage like a modeler — proposal (2026-10-21)

Written after the first junction of the window vine (`models/tasks/arabesco-janela/`).
The goal is the modeler's: the AI should do what a human does in Edit Mode,
not approximate it.

## What the modeler did at the junction

In four minutes, in the real file: three knife cuts along the line where the
two plates cross, two loop cuts to open a row, translate and vertex/edge slides
to bring the borders together, one merge, `mark_sharp` on the edges that must
stay hard. Result: 1 connected mesh, 0 non-manifold edges, 2 creased triangles
(D-080).

## What the AI can do today

- `edit(name, "...")` runs one line on a selection: `vN`, `vA-vB`, `loop`,
  `ring`, `path`, `region`, predicates like `h>500`.
- Ops: translate, extrude, merge, delete, `bridge_edge_loops`, knife? (no),
  loop cut? (no), `remove_doubles`, bevel, slide, `loops_tools`.
- `select()` previews a selection, `views()` renders the labeled cage and the
  subdivided result.

## What is missing, and why the two automated attempts failed

1. **Where to cut.** The AI cannot ask "where do these two islands cross?".
   Without that line, a cut is guessed. Attempt 1 (`mesh.intersect`) cut both
   surfaces but did not weld the cut, leaving 18 non-manifold edges.
2. **Which loop to bridge.** `bridge_edge_loops` takes edges. Given every
   border edge ("select all"), it bridged the whole outline: 86 triangles,
   12 non-manifold edges. The two junction loops must be named by id.
3. **A knife path between two ids.** Blender's knife is interactive; the
   scriptable equivalent is a walk along the surface between two vertices.

## Proposal: five small additions to the bridge

Each one takes stable ids and returns numbers, so a step can be checked before
the next one.

| New call | What it gives |
|---|---|
| `topology_report(name, ids)` | islands, border loops (loop id + its edge ids), where two islands intersect (edge/face pairs), nearest id pairs with distance in mm |
| `cut_between(name, id_a, id_b)` | one knife cut along the surface path between two ids |
| `bridge_loops(name, loop_a, loop_b, segments=0)` | bridge exactly two loops, named by id, never "all borders" |
| `weld(name, id_a, id_b)` / `weld_region(name, ids_a, ids_b, threshold)` | merge two vertices, or the closest pairs between two sets, keeping the direction the modeler chose |
| `delete_faces(name, ids)` | delete by face id, not by a predicate that can catch the wrong faces |

With those, the junction becomes a sequence the AI can actually run and check:

1. `topology_report` → the intersection line and the two border loops;
2. `cut_between` along the intersection, on both islands;
3. `delete_faces` for what is now hidden;
4. `bridge_loops(loop_a, loop_b)`;
5. `views(crop, focus)` to show the modeler the junction;
6. `weld` only where the counts do not match.

## Two bugs fixed first (2026-10-21)

- `replace_from` (used by `absorb`): an object the human created by
  `MESH_OT_separate` was not carried into the AI file; the separated geometry
  was lost from the working file. It now brings new objects in (repairing their
  ids and materials) and drops the ones the human deleted.
- `join` duplicated stable ids, so `catalog_edit` could not measure the
  correction ("stable ids missing or duplicated"). `review()` now repairs ids
  before writing the human's file, and `join_meshes(names, into)` joins and
  repairs in one call.

## Order of work

1. `topology_report` (read-only, no risk, unlocks the rest).
2. `bridge_loops` and `delete_faces` by id.
3. `cut_between`.
4. `weld` / `weld_region`.

## Status
- 2026-10-21: `topology_report` implemented in `topology.py` and exported as `llm_modeling_bridge.topology_report`. First run on `Plane.001` (the joined leaf): 2 islands, 1 crossing with 9 face pairs, nearest vertices 1.02 mm apart (ids 87 and 125), one 50-edge border loop of 1044 mm.
- Next: `bridge_loops` and `delete_faces` by id, then `cut_between`, then `weld`.

### Status 2026-10-21 (later)
- Implemented and tested on a synthetic pair of quads (`tests/test_surgery.py`,
  10 checks): `bridge_loops` (4 faces), `cut_between` (splits a face),
  `delete_faces` (one face by ids), `weld` (one pair).
- `weld_region` is implemented but not yet exercised on a real junction.
- The first real target: the leaf `Plane.019` joined into `Plane.001` at `arabescos.bak-04.blend` — 2 islands, 9 crossing face pairs, nearest 1.02 mm (ids 87/125).

### Status 2026-10-21 (review)
- `cut_between` used `bmesh.ops.connect_verts`, which only links two vertices of
  one face; it now uses `connect_vert_pair` (Blender's J) and walks across
  faces, returning the new vertices' ids in `new_ids`. It refuses two islands.
- `topology_report` truncated every id list to 12, so its loops could not be
  passed to `bridge_loops`; the lists are now whole, open runs come out whole
  (`closed: false`), and each crossing names the vertex ids of the faces that
  pass through each other (`ids_a`, `ids_b`).
- `bridge_loops` refuses a list with a gap between consecutive ids instead of
  bridging part of it, and takes two open runs as well as two closed loops.
- `weld_region` refuses one set passed twice, pairs closest first and welds
  with `weld_verts`.
- Every call returns `non_manifold`, `boundary` and `wire` edge counts, and
  repairs ids against the last sync state, so sync does not renumber them.
- The "cut is not shared" diagnosis was wrong: `mesh.intersect` with
  `separate_mode="NONE"` merges the cut line (1 component); its 18 edges with
  4 faces are the crossing, removed by deleting the flaps.
- `intersect(name, island_id)` runs Edit Mode's Intersect (Knife) with
  `SELECT_UNSELECT` and Merge on one island against the rest. On `Plane.001`
  with the leaf `Plane.019` (id 125): 112 v / 69 f, 1 island, 18 edges with 4
  faces, 20 new vertices on the cut (ids 137-156).
- Sidecars: `absorb()` syncs only what the human changed, what already has a
  text, and what an annotation points at (a review opens the whole scene);
  `join_meshes()` and `absorb()` remove the text and state of objects that left
  the file (`sync.prune_sidecars`).

### Status 2026-10-21 (the `Plane.019` junction, AI then modeler)
- The AI's junction (three-way split at v87) used `make_face`; `weld` now
  keeps `id_b`'s id (it kept `id_a`'s, and the next call lost v87).
- The modeler's correction (`human/review-20261021-051941-...`): one quad
  closing the fork at v87, crease on v87-v104, a loop cut on the left leaf,
  ~50 moves (the curl leaf moved as a block by 5.8 mm, the crotch 8-10 mm),
  sharp marks instead of `Smooth by Angle` (D-081, D-082).
- New: `topology_report` lists `folds`; `fill_notch(name, id)` closes one and,
  run on the AI's version, makes the modeler's quad (87, 177, 176, 104).
- Junction recipe: `join_meshes` → `topology_report` → `delete_faces` the
  overlapping base faces → `weld` the base row onto the stem's row →
  `make_face` what the split leaves open → `fill_notch` every fold → crease
  the triangle's edges → `views(crop=True)` → review.

### Status 2026-10-21 (the `Plane.021` junction, a side branch)
- `Plane.021` (a small curl) does not leave from a fork: its base row lies
  along the stem and the leaf rises off the stem's top border. Recipe for a
  side branch: `delete_faces` the leaf's base row (it lies on the stem) →
  `loop_cut` the stem on each side of the border vertex under the leaf
  (ids 211-216) → `bridge_loops` the leaf's new base run (209, 210, 208) to
  the stem's border run (212, 0, 215) → slide the cut so the bridge faces are
  not slivers (factor 0.4: aspect 4.3 → 2.9) → `views(crop=True)`.
- New: `loop_cut(name, id_a, id_b, factor)`. `subdivide_edges` can rebuild
  the vertices it touches, so the new ones are found by position.
- Fixed: an `edit` op was refused when the mesh already held an accepted
  triangle (D-080); now only an error the op adds refuses it.

### Status 2026-10-21 (the modeler's `Plane.021` correction)
- Review `human/review-20261021-054615-...`: merge ×2 (v0 into the stem rib
  v216), J ×1, knife ×1 (v218-v222), vert slide ×10, mark sharp ×3 with
  crease, 56 moves, resize Y→0 on the curl. D-084.
- New: `topology_report` lists `fold_ends`; `mark_fold(name, ids)`.
- Side-branch recipe, amended: after the bridge, `weld` the stem border
  vertex under the leaf onto the stem's rib vertex, so rib meets rib; run
  every `fold_ends` into the rib and `mark_fold` it; the crotch between the
  leaf's inner edge and the stem is a fold too.
- Fixed: `views(crop=True)` drew horizontal stripes: `Panel.dot` sliced a row
  with a negative end for a vertex left of the panel.
