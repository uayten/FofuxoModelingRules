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
