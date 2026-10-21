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

### Fourth leaf: `Plane.022`, a branch off the stem's underside (2026-10-21, Claude)
- `join_meshes`: leaf ids 223-240. Backup before: `arabescos.bak-08.blend`.
- The leaf's first two rows lay on the stem's lower half (root near the stem
  rib v55); it peels off the bottom border at x≈111 mm and hooks down.
- Steps (D-084 applied from the start): `delete_faces` the two rows on the
  stem (4 faces); `loop_cut(4, 6, 0.43)` at the peel (v241-v243); `weld`
  229→242 (leaf's upper edge onto the stem's bottom border) and 233→243
  (rib onto rib); `delete_faces` the stem face under the leaf
  [243, 54, 6, 242]; `fill_notch(243)` made [243, 54, 6, 228], so the stem's
  bottom border runs on into the leaf's lower edge; `mark_fold([242, 243])`
  for the crotch.
- Result: 142 v / 94 f, 1 island, 0 non-manifold, no folds, no fold ends,
  no new triangle. Render `arabescos.bridge/Plane.001.leaf4.png`; in review.
- The leaf's part that ran along the stem (x 125-156) is gone: the branch now
  starts at the peel. The modeler may want that tail back.

### The modeler's correction of `Plane.022` (2026-10-21, 03:02)
Review `human/review-20261021-060243-...`: 150 v / 100 f, 0 non-manifold.
Knife and loop cut at the junction (v244-v251), folds meeting at v243,
sharp on every creased edge and on 58 border edges, the tip v232 to y=0 with
the rows behind it tapered, shade smooth. D-085, D-086. `sharpen_folds` then
marked the last creased edge without sharp (5-7).

### Fifth leaf: `Plane.027`, the outer lobe of a three-lobe curl (2026-10-21, Claude)
- The cluster `Plane.027` / `.029` / `.030` is one curl in three nested lobes
  that pass through each other (11-12 face pairs between lobes, 3-5 with the
  stem); `.030`, the inner one, is shallower (depth 1-4.3 mm) and its tail
  runs down the stem to v15/v16. The modeler chose to connect only the outer
  lobe now and decide the other two after the correction.
- `join_meshes(["Plane.001", "Plane.027"])`: leaf ids 252-272 and 321.
  Backup before: `arabescos.bak-09.blend`.
- The lobe's tail lay on the stem face [12, 14, 58, 57], its end row
  266-267-268 on the stem's row 14-58: a fork, the stem going up and the lobe
  going left. Steps: `delete_faces` the tail's two rows and the stem face
  under it; `weld` 263→12 (crotch, at the stem's position); `make_face`
  [14, 264, 265, 58] (lobe's lower border onto the trunk's border, rib onto
  rib) and the triangles [265, 12, 58], [12, 57, 58] around the valley;
  `mark_fold` [254, 265, 58] (the lobe's rib runs into the stem's rib) and
  [12, 58] (valley from the crotch); v265 raised to rib depth (5.27 mm).
- Result: 167 v / 112 f, 1 island, 0 non-manifold, one border of 115 edges,
  no folds, no fold ends, no unsharp folds; 2 new creased triangles (D-080).
  Render `arabescos.bridge/Plane.001.leaf5.png`; in review.

### The modeler's correction of `Plane.027` (2026-10-21, 04:21)
Review `human/review-20261021-072146-...`: 175 v / 118 f, 1 island,
0 non-manifold, no folds, no fold ends. A knife row above v58 (330-332-331-
329-328) split the AI's two long triangles into quads plus two short creased
triangles at v58; a loop cut on the lobe (333-334-335); the stem above the
junction bent outward (v5-v8, v54, v55 by 2.5-4.7 % of the frame's width) and
the rows below moved up (v15, v16, v59 by 4-6 % of its height). Subdivision
viewport level 1. D-087; `knife_row` reproduces the row on the AI's version.

### The inner lobes `Plane.029` and `Plane.030`, each born from the lobe above (2026-10-21, Claude)
- The modeler's direction: each inner lobe is born from the face of the lobe
  above it, with a fold where it emerges. Backup before: `arabescos.bak-10.blend`.
- `join_meshes(["Plane.001", "Plane.029", "Plane.030"])`: middle lobe ids
  337-378 (odd), inner lobe 336-383 (even) and 377, 379, 381, 383.
- Both lobes have the same layout: the lower lobe's rib runs just inside the
  upper lobe's lower border, and its upper strip (rib to upper border) lies
  hidden under the upper lobe; its tail lies on the stem.
- Middle lobe: `delete_faces` its upper strip and its tail (6 faces);
  `weld` 347→260 and 341→14 (at the outer lobe's position); `make_face` four
  quads from the middle rib (349-357-359-373-345) to the outer lobe's lower
  border (260-258-253-333-264-330-14). That border is now the valley fold.
- Inner lobe: the same onto the middle lobe's lower border (351-353-363-371-
  14): `delete_faces` 7 faces, `weld` 377→351, 383→14, 381→16 (the inner
  border lands on the stem border), four quads from the inner rib
  (376-358-344-368-374).
- `mark_fold` both valleys and the middle rib's last edge (345-14); the
  valleys raised to mid depth (2.6 and 2.4 mm), not left on the base;
  `flatten_tip` on both lobes' tips (D-086).
- Result: 203 v / 142 f, 1 island, 0 non-manifold, one border of 127 edges,
  no folds, no fold ends, no unsharp folds, no new triangle. Four folds meet
  at v14 (two valleys, two ribs), all through quads. Render
  `arabescos.bridge/Plane.001.lobes.png`; in review.

### The modeler's correction of the inner lobes (2026-10-21, 04:55)
Review `human/review-20261021-075553-...`: 252 v / 176 f, 1 island,
0 non-manifold, 14 triangles, 2 pentagons. The lobes are flaps again, held at
their roots v330 and v400 (folds of 361-362°, the overlap); their folds run
down the stem and merge at v58, v431 and v59 (D-088); 80 border edges creased
(D-089); the D-087 row applied at v87 (`Plane.019`); `Smooth by Angle` added
by Shade Auto Smooth, then removed by the AI. After the review: `crease_border`
creased the 81 border edges left, `mark_fold([400, 420])` gave that fold its
sharp. Render `arabescos.bridge/Plane.001.lobes_corrected.png`.
- The row 16-59-15 across the stem, creased without sharp, is a fold (the
  modeler confirmed); `sharpen_folds` gave its two edges sharp. Closing
  checks: no unsharp folds, no uncreased border, no fold ends.

### The acanthus leaf at the stem's bend: first blade, `Plane.026` (2026-10-21, Claude)
- Next cluster down the stem: three blades rising from the stem's inner
  border at the bend (v19/v61): `Plane.026` (green, along the stem),
  `Plane.024` (red, the pointed wedge), `Plane.025` (blue, the curl). The
  modeler set the layering: green over red over blue, each next blade coming
  out from under the one before (D-088). Built in stages: the top blade first.
  Backup before: `arabescos.bak-11.blend`.
- `join_meshes(["Plane.001", "Plane.026"])`: blade ids 469-489.
- The blade's root row (485-487-486) lay on the stem face [19, 21, 62, 61]
  and its left border touched the stem's inner border at 488, on edge 17-19:
  a fork like `Plane.027`, the stem going up, the blade going up beside it.
  Steps: `delete_faces` the root row; `weld` 488 onto 17 at 488's position
  (17 slides down its own border to the crotch); `delete_faces` the stem face
  [17, 19, 61, 60]; `make_face` [19, 471, 476, 61] (blade's far border onto
  the trunk's border, rib onto rib) and the triangles [476, 17, 61],
  [17, 60, 61]; `mark_fold` [484, 476, 61] and [17, 61]; `knife_row` across
  [20, 18], [61, 60], [61, 17], [61, 476], [19, 471] at 0.45 (D-087,
  ids 490-494); `flatten_tip(470)`; `crease_border`; `sharpen_folds`.
- Result: 274 v / 192 f, 1 island, 0 non-manifold, no fold ends, no unsharp
  folds, no uncreased border, every leaf tip at 0; the only folds are the
  flap roots of the curl above (v12, v330, v400). Render
  `arabescos.bridge/Plane.001.green.png`; in review.

### The modeler's correction of `Plane.026` (2026-10-21, 05:17)
Review `human/review-20261021-081713-...`: 280 v / 196 f, 1 island,
0 non-manifold. Two loop cuts across the stem, halfway above (495-497-496)
and below (498-500-499) the junction; the junction's row slid straight (v60,
v18 down to v17's level); the crotch v17 lifted to 1.64 mm (v12 sits at
1.51). Rules D-090 (crotch off the base) and D-091 (a loop each side);
`lift_crotch` added. The closing checks stay clean.
