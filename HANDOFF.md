# Handoff

Updated: 2026-10-21

## State
- The window's arabesques (`models/tasks/arabesco-janela/`, ROADMAP 1).
  `Plane.001` (the vine stem) carries four connected leaves: 150 v / 100 f,
  1 island, 0 non-manifold, no `fold_ends`, no `unsharp_folds`, every leaf tip
  at depth 0. Last leaf joined: `Plane.022`, corrected by the modeler. 15
  leaves of `Videira do Arco` are still separate.
- Surgery calls by stable id, all tested (`tests/test_surgery.py`, 40
  checks; the other suites pass): `topology_report` (islands, loops, folds,
  fold_ends, unsharp_folds, sharp_only, tips, crossings), `delete_faces`,
  `bridge_loops`, `cut_between`, `intersect`, `loop_cut`, `make_face`,
  `fill_notch`, `mark_fold`, `sharpen_folds`, `flatten_tip`, `weld`,
  `weld_region`. Recipes (fork, side branch) in
  `extension/fofuxo-bridge/EDITING.md`; rules D-080 to D-086.
- Cage texts: only `Plane.001.txt` is on disk; `absorb()` syncs only what
  changed and joins prune the texts of objects that left.

## Next step
The next leaf down the stem: the cluster `Plane.027` / `.030` / `.029`
(touches the stem near world z 1970-1985 mm). `join_meshes`, read
`topology_report`, pick the recipe (fork D-081 or side branch D-084), run the
closing checks, `views(crop=True)`, `review(["Plane.001"])`, then `collect()`
and turn the modeler's correction into rules or calls.

## Open questions
- The AI suggested keeping the sync state (`.state/*.json`) inside the
  .blend instead of beside it; not accepted yet.

## Notes for the next session
- Backups `arabescos.bak-01..08.blend` are not committed; `bak-08` is the
  file before `Plane.022`.
- `Plane.013` mirrors around the `Mirror` empty at the world origin; the band
  mirrors around `Plane.048`. Keep both in the file.

## Read first
`ROADMAP.md` (item 1), `extension/fofuxo-bridge/EDITING.md`,
`extension/fofuxo-bridge/OPS.md`, `models/tasks/arabesco-janela/report.md`,
DECISIONS D-080 to D-086. Avoid: `models/tests/`, raw `.jsonl` logs, the
`human/review-*` folders unless a correction is being read.
