# Fofuxo Modeling Rules

Modeling rules for AIs that build stylized game models in Blender through the
Blender MCP, learned from a human modeler's files and tested on AI runs.

- Load the skill (`skill/fofuxo-modeling-rules/SKILL.md`) so an AI models with
  a live modifier stack, a cage that carries the silhouette, and honest
  delivery.
- Edit cage meshes as text, taking turns with a human in Blender, with the
  Fofuxo Cage extension (`extension/fofuxo_cage/`).
- Compare AI runs with a human reference on the same task.
- Grow a catalog of human examples from interviews, and turn the modeler's
  feedback into rules through an explicit filter (`models/FEEDBACK.md`).
- Trace every rule back to the file and the words it came from
  (`DECISIONS.md`).

## Contents

- [Layout](#layout)
- [Conventions](#conventions)
- [Why](#why)

## Layout

```
skill/fofuxo-modeling-rules/   the skill (SKILL.md)
extension/fofuxo_cage/         Blender extension: cage text round trip
models/
  FEEDBACK.md                  how interviews and feedback become rules
  example/
    CATALOG.md                 every example, its status, when to read it
    <name>/                    reference material
      EXAMPLE.md               how it was made, whys, AI deductions
      concept.png              the concept image
      human/                   the modeler's files (E ids)
      ai/                      AI models accepted as references
  tasks/<name>/                a challenge and its attempts
    start.blend                starting file, concept packed
    prompt.md, target.md       what is asked and what to reach
    ai/                        AI runs (T ids), one folder per run
    human/                     human work on the task
DECISIONS.md                   every rule, why, and where it came from
ROADMAP.md                     what to build next: Blender's tools for the AI, learning from use
```

Today: the catalog lists the bow tie and the hat (both from E1, the dragon
outfit) and the skirt ruffles (no file yet); `models/tasks/laco/` holds T1
(Sonnet and Opus runs, with and without rules). The extension has its own
[README](extension/fofuxo_cage/README.md).

## Conventions

- **Ids.** `E<n>` is a human example, `T<n>` an AI test, as cited in
  `DECISIONS.md`. Folder names are ASCII (`laco`, not `laço`).
- **Runs.** `tasks/<name>/ai/<run>-<model>-<variant>/`, e.g. `A3-opus/`.
  `ai/README.md` holds each test's protocol and verdict; a new run adds a
  `report.md` with model, skill commit, prompt, time and tokens, measurements
  and verdict, and a `feedback.md` with the modeler's feedback, filtered as in
  `models/FEEDBACK.md`.
- **AI output and human edits stay apart.** When the modeler edits an AI
  result, the run keeps the AI file and the edit goes to `human/`:
  `ai/A2-sonnet/A2-ai.blend` and `human/A2-human-edit.blend`.
- **Cage text.** Fofuxo Cage writes `<file>.cage/<object>.txt` next to each
  .blend; the text is committed (each AI iteration is a readable diff), the
  `.state/` folder is not.
- **Moving a .blend.** Open it and Save As with relative remap (the files link
  Blender's bundled assets by relative path); a plain `git mv` breaks them
  when the folder depth changes.
- **Never save over** `example/` files or finished runs while testing; work on
  a copy.

## Why

The skill started from one human file (E1) and one question: what does an AI
need to model like this modeler? Test T1 showed the models fail more at
execution than at perception, which led to the Fofuxo Cage extension (D-048).
