# Handoff

Updated: 2026-10-21

## State
- The window's arabesques (`models/tasks/arabesco-janela/`, ROADMAP 1).
  `Plane.001` is the whole vine stem now (the lower part `Plane.017` joined at
  a hidden elbow) with ten leaves connected: 387 v / 270 f, 1 island, one
  border, no fold ends, no unsharp folds. The only `folds` are the flap roots
  v12, v330, v400 (intended, D-088). Nine leaves are left, all on the lower
  stem: `Plane.023`, the clusters `.035`/`.034`/`.036` and
  `.031`/`.032`/`.033`, then `.018` and `.037`.
- The bridge asks the modeler questions inside the review Blender
  (`review(names, questions=[...])`, answers in `collect()["answers"]`);
  used three times, works. New calls this session: `knife_row`,
  `crease_border(ids=...)`, `lift_crotch`, `loop_cut(level_with=...)`.
  Tests: `test_surgery.py` 52 checks, `test_questions.py` 12, others pass.

## Next step
`Plane.023` (1 mm from the lower stem, world z 1754-1831 mm): `join_meshes`,
`topology_report`, pick the recipe (fork D-081/D-087, side branch D-084),
then the junction rules: `lift_crotch` (D-090), a loop on the stem each
side (D-091), base rows level with the stem's and stem loops where its rows
are long (D-092), `crease_border(ids=<the leaf's ids>)`, `views(crop=True)`,
`review(["Plane.001"], questions=[...])` for anything unsure, `collect()`.

## Open questions
- The sync state (`.state/*.json`) inside the .blend instead of beside it:
  suggested by the AI, not accepted yet.
- ROADMAP 2 to 5 (checklist, `connect_leaf`, Jev, Sonnet executor) were
  accepted; the Order puts the checklist before the next leaf.

## Notes for the next session
- `bridge_loops` may pair two runs crossed (it twisted 82→629 at the elbow):
  check the faces it made; `make_face` by hand when it does.
- After a revert (`wm.revert_mainfile`), run the next bridge call in a new
  MCP call: the same call's context breaks `object.join`.
- Backups `arabescos.bak-09..13.blend` are not committed; `bak-13` is the
  file before `Plane.017` joined.

## Read first
`ROADMAP.md` (item 1), `extension/fofuxo-bridge/EDITING.md` (the recipes and
the status notes at the end), `extension/fofuxo-bridge/OPS.md`, DECISIONS
D-080 to D-093, the last sections of `models/tasks/arabesco-janela/report.md`.
Avoid: raw `.jsonl` logs, and the `human/review-*` folders unless a
correction is being read.
