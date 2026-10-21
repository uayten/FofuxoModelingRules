# Window arabesques — work log

## 2026-10-21 — environment and first merge

### Tooling
- The agent session (DeepSeek Harness) has no Blender MCP tool. Blender is driven
  through `tools/blender_exec.py`, which speaks the addon's TCP protocol
  (`{"type": "execute", "code": ..., "strict_json": false}`, null-byte framed).
- AI instance started with
  `python extension/fofuxo-bridge/launcher.py models/tasks/arabesco-janela/arabescos.blend`.

### Bug found: `collect()` drops an object the human created by separating
The modeler split `Plane.017` (96 v) into two objects in the review Blender:
`Plane.001` (51 v, the top of the vine stem) and `Plane.017` (45 v, the bottom).
`collect()` reported `"changed": true` and `absorb()` wrote the new topology of
`Plane.017` (45 v) into the AI file, but **`Plane.001` did not exist in the AI
file afterwards**: 51 vertices of geometry were lost from the working file.

- The human's `review.blend` still held both objects, so nothing was lost on
  disk; `Plane.001` was restored with `bpy.data.libraries.load` and linked back
  into `Videira do Arco`.
- Side effect of the restore: the loaded object brought a duplicate material
  (`M_Ouro.001`). It was merged back into `M_Ouro` and the unused slot removed.
- Not yet diagnosed in the extension: whether `absorb()` ignores added objects
  by design or fails to link them. Worth a focused test in the bridge suite.

### First merge step
- `Plane.020` (12 v, 6 faces, the small top leaf) joined into `Plane.001`
  (51 v, 32 faces) with `bpy.ops.object.join`. No modifier was applied.
- Result: 63 v, 38 faces, one material slot (`M_Ouro`), `Plane.001` keeps its
  `Subdivision (2)` and `Smooth by Angle`. Both pieces had the same stack, so
  the render is unchanged.
- **The pieces overlap but do not touch**: 0 vertex pairs within 0.5 mm. Joining
  made one object, not one connected surface. Connecting needs the modeler's
  operation: delete the faces hidden under the overlap, move the border
  vertices onto the neighbour, weld (`remove_doubles` or `bridge_edge_loops`).
- Backup of the file before the join: `arabescos.bak-01.blend`.

### Second step: welding the leaf into the stem
- 3 vertex pairs snapped and welded (`remove_doubles`, 0.1 mm), no modifier
  applied: 63 v / 38 f → **60 v / 38 f, 1 connected component**.
- Cost of the weld: the leaf's base vertices moved up to 6 mm, a new
  **non-manifold edge** appeared at (0.001, -0.007, local) and the boundary
  went 46 → 44 edges. The junction is a pinch, not a clean seam.
- Backup before the weld: `arabescos.bak-02.blend`.
- Renders: `arabescos.bridge/Plane.001.zoom.png` (before, cage + subdivision),
  `arabescos.bridge/Plane.001.join.png` (after), `renders/junction_zoom.png`.

### Visualisation used
`llm_modeling_bridge.views(name, views=[...], focus=ids, crop=True,
isolate=True)` renders the labeled cage and the subdivided result side by
side, cropping to the stable ids of the region. Stable ids live in the
`llm_modeling_bridge_id` point attribute.

### Modeler's correction on the same junction (2026-10-21, 01:01)
The window was handed over with `human_access()`; the modeler worked in the real
file and returned it with `resume_ai(save=True)`. Recorder: knife ×3, loop cut
×2, translate ×33, vertex slide ×6, edge slide ×2, merge ×1, shortest-path
select ×7, one local view, one `mark_sharp`.

- Result: **71 v / 46 f, 1 component, 0 non-manifold edges** — the pinch I left
  is gone; boundary 50 edges. He reshaped the junction with new faces instead
  of welding points.
- The 2 triangles are **not an error**: the modeler creased the edges around
  them and the Subdivision result holds. Recorded as D-080.
- Example preserved: `human/review-20261021-040140-1792555300996234700/`.

### Bugs fixed in the bridge (2026-10-21)

1. **`absorb()` lost an object the human separated.** `replace_from` only
   replaced the names the review had opened, so `Plane.001` (the separated top
   of the stem) never reached the AI file while `Plane.017` was overwritten
   with the smaller half. Fixed in `instance.replace_from`: objects that exist
   in the review but not in the AI file are loaded in (materials remapped by
   name, stable ids repaired); objects the human deleted are removed. Test:
   a simulated separate produced `Plane.002`/`Plane.003` in the review, both
   arrived in the AI file (49 → 51 objects).
2. **A join left duplicated stable ids**, so `catalog_edit` gave up on the
   before/after deltas. Fixed twice: `review()` repairs every mesh's ids before
   writing the human's file, and the new `join_meshes(names, into)` joins and
   repairs in one call. Test: join of `Plane.018` + `Plane.021` → 51 vertices,
   51 unique ids, 21 fresh, `_positions()` returns data.

Both fixes are in `extension/fofuxo-bridge/instance.py` and were copied into
the installed extension (`user_default/llm_modeling_bridge`) and reloaded in
the open Blender.

### Third step: the next leaf joined, junction still open
- `Plane.019` joined into `Plane.001`: 71 v / 46 f → **92 v / 58 f**, 49
  objects, **2 islands**, 0 non-manifold. Backup: `arabescos.bak-04.blend`.
- Two automated connection attempts failed and were reverted:
  - `bpy.ops.mesh.intersect` on the two islands: 112 v / 87 f, **18
    non-manifold edges**, 12 triangles — it cuts both surfaces but does not
    weld the cut line;
  - deleting the 5 overlapping faces and calling `bmesh.ops.bridge_loops` on
    every border edge: 137 faces, **86 triangles, 12 non-manifold edges** — the
    operator bridged the whole outline, not just the junction.
- Lesson: the bridge must be given only the two loops of the junction; a
  "select all border" bridge destroys the outline.

### State
- `arabescos.blend`: 49 objects, `Plane.001` = 92 v / 58 faces (two islands:
  the stem + the modeler's junction, and the leaf just joined), `Plane.017` =
  45 v / 28 faces, 18 vine leaves left.
- Renders: `renders/top_cluster_solid.png`, `renders/top_cluster_xray.png`,
  `renders/merge_step1.png`, `renders/junction_zoom.png`.

### The `Plane.019` junction by the AI (2026-10-21, Claude)
- The saved file carried duplicated ids on the leaf (joined with
  `object.join`, not `join_meshes`); repaired, the leaf is now ids 157-177.
- `intersect` gave one island but no clean X: the leaf lies about 1 mm from
  the stem over a long strip, so the cut came out as 7- to 9-gons and two
  chains that split neither surface. Reverted.
- The leaf's base row 157-166-159 sits on the stem's crotch row 86-87-88
  (2.9 / 1.0 / 4.6 mm). Attempt: a three-way split at 87, like the modeler's
  two-way one. `delete_faces` [166,159,176,177] (the leaf's left base face)
  and [86,87,103,104] (the middle leaf's right base face), `weld` 157→86 and
  166→87, `make_face` [87,103,104]. Result: 89 v / 57 f, 1 island,
  0 non-manifold, one closed border of 65 edges, one triangle (not creased).
- Render: `arabescos.bridge/Plane.001.junction2.png`. Sent to the modeler in
  a review of `Plane.001` alone. Backup before: `arabescos.bak-06.blend`.

### The modeler's correction of the AI junction (2026-10-21, 02:19)
Review `human/review-20261021-051941-...`: 240 operators, 55 moves, F2 ×1,
loop cut ×1, edge slide ×1, rotate ×1, resize ×2 (Y to 0: flattened the
depth of v95, v96, v99, v102), mark sharp ×1, `Smooth by Angle` removed,
viewport Subdivision 2 → 1. Result 92 v / 60 f, 0 non-manifold, 3 triangles.
- Kept the AI's three-way split and its triangle 87-103-104.
- Closed the fork: quad 177-176-104-87; v87 is no longer on the border
  (D-081). Creased v87-v104.
- Loop cut on the left leaf (v178-v180) and reshaped it; the curl leaf moved
  as a block by 5.8 mm; the crotch v86-v88 moved 8-10 mm.
- Sharp by hand along the stem (D-082).
- `fill_notch` on the AI's version reproduces the quad.
- The modeler confirmed both (D-082 sharp by hand; D-083 Subdivision drops to 1 as loops go in, export likely at 1).

### Third leaf: `Plane.021`, a side branch (2026-10-21, Claude)
- `join_meshes(["Plane.001", "Plane.021"])`: leaf ids 181-210; its text and
  state pruned by the join. Backup before: `arabescos.bak-07.blend`.
- The leaf's base row (181-195-182) lay along the stem, not across it.
  Deleted it, cut two loops in the stem beside v0 (211-213 at 0.4 of 49→0
  after a slide, 214-216 at 0.4 of 0→10), bridged 209-210-208 to 212-0-215.
- Result: 125 v / 82 f, 1 island, 0 non-manifold, no folds, one border.
  The stem's sharp and crease on its rib survived the cuts (52-213, 52-216).
- Render `arabescos.bridge/Plane.001.leaf3.png`; sent to review.

### The modeler's correction of `Plane.021` (2026-10-21, 02:46)
Review `human/review-20261021-054615-...`: 129 v / 86 f, 0 non-manifold,
5 triangles (2 new, creased). v0 merged into the stem rib v216; knife row
v218-v222; folds 52-222-216, 210-221-216, 209-220-216 (crease + sharp);
base 12.7 → 8.1 mm; curl flattened in depth (resize Y→0 on v184, v187,
v188, v198). Recorded as D-084; `fold_ends` finds the AI's dangling rib.
- The 43 cage texts of objects nobody works on (written by an absorb of the
  whole scene) were removed with their states; `Plane.001.txt` stays.
