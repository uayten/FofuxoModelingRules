# Task: straw cowboy hat (ROADMAP, Part 2, item 11)

The first concept built from nothing: no body to sit on, no modeler's part to
measure against. The modeler's judgment is the reference.

- **Concept:** `concept.jpg`, packed in `start.blend` as the `Concept` empty
  (collection `Referência`). A 3/4 photo with perspective, not an
  orthographic front: the empty's scale is only a starting guess (610 px to
  0.5 m, about 0.82 mm/px, brim tip to tip about 42 cm); the plan sets the
  real numbers.
- **Size:** a real adult hat. Head opening for an adult head (about 58 cm
  around); brim and crown in the proportions of the photo.
- **Poly budget:** at most about 800 faces in the final mesh, with every
  modifier applied (band included).
- **Units:** metric, centimeters, unit scale 1.

## P1, P2, ...: the plan, written blind

The prompt given to the planning run, word for word:

> Plan the straw cowboy hat in `concept.jpg` (packed in `start.blend` as the
> `Concept` empty). A real adult hat, at most about 800 faces with every
> modifier applied. Read `skill/fofuxo-modeling-rules/SKILL.md`,
> `skill/fofuxo-modeling-rules/PLAN.md` and, from
> `extension/fofuxo_cage/README.md`, only the op table rows the plan uses.
> Write only `ai/<run>/plan.md`, following PLAN.md's skeleton. Blender only to
> read the scene; no modeling call, no `round_start`.

Not read: `ROADMAP.md`, `DECISIONS.md` (the skill carries the rules), the
other tasks' runs (`models/tasks/chifre/`).

## Build

Only after the modeler approves a plan: a run builds it in its own Blender
with `round_start(label, plan=...)`, saves `<run>.blend` and `report.md` in
its run folder, ending with the round's cost line. Target: about 100k tokens.
