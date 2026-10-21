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
