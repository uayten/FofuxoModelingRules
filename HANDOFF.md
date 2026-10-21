# Handoff

Updated: 2026-10-21

## State
- The window's arabesques are the new work (`models/tasks/arabesco-janela/`,
  ROADMAP 1). `arabescos.blend` has 49 objects. `Plane.001` is the vine stem
  with two leaves joined: 92 v / 58 f, two islands, 0 non-manifold. The first
  junction (stem + `Plane.020`) was rebuilt by the modeler with knife cuts and
  loop cuts and it holds. The second leaf (`Plane.019`) is joined but not
  connected; 18 vine leaves are still separate objects.
- The by-id surgery calls exist and pass their test: `topology_report`,
  `delete_faces`, `bridge_loops`, `cut_between`, `weld`, `weld_region`
  (`extension/fofuxo-bridge/EDITING.md`, `tests/test_surgery.py`). The
  round-trip suite passes 244 checks. Commit `f127357`.
- Two absorb bugs fixed: an object the modeler separates in the review now
  reaches the AI file, and a join no longer leaves duplicated stable ids.

## Next step
ROADMAP 2, the coincident cut. `mesh.intersect` cuts both islands but creates
no coincident vertices (18 non-manifold edges survive `weld_region`), so the
two borders cannot be bridged. Make the cut line shared, then run the
`Plane.019` junction with the ids from `topology_report` and show it with
`views(crop=True)` before saving.

## Open questions
- `.bridge/*.txt` cage text: inside the .blend as text datablocks, one file per
  asset, or nothing on disk. The modeler is deciding this elsewhere; do not
  change the format here.
- The `Plane.019` junction: the modeler's hand method or the automated flow
  once the cut is shared.

## Notes for the next session
- This session had no Blender MCP tool: it drove the AI Blender through
  `python tools/blender_exec.py -c "<code>"` (port 9876, one Blender per port).
- Backups `arabescos.bak-01..05.blend` are not committed; `bak-04` holds the
  joined-but-unconnected leaf.
- `Plane.013` mirrors around the `Mirror` empty at the world origin; the band
  mirrors around `Plane.048`. Keep both in the file.
- The untracked `human/review-20261021-034641-...` (9 MB, the bug case) and
  `reference/vitral-1.png` were left out of the commit on purpose.

## Read first
`ROADMAP.md` (items 1-2 and Order), `extension/fofuxo-bridge/EDITING.md`,
`models/tasks/arabesco-janela/report.md`,
`skill/fofuxo-modeling-rules/SESSION.md`, `extension/fofuxo-bridge/OPS.md`.
Avoid: `models/tests/`, raw `.jsonl` logs.
