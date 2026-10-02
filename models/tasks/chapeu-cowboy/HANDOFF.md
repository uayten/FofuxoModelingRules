# Straw cowboy hat: where it stands (handoff, 2026-10-01)

> Tooling update (2026-10-02): the extension source is now
> `extension/fofuxo-bridge/`, importing `llm_modeling_bridge` (the old import
> and launcher remain compatible). Read `ROADMAP.md` for the current numbering
> and `extension/fofuxo-bridge/HUMAN_TESTS.md` for the pending interaction checks.
> The hat's saved files below were preserved. Historical `.cage/` paths remain
> valid until the file is opened with the new extension and migrated.
> Use `ai/C1/recording-summary.json` instead of rereading all 343 operators.
> C1's former in-memory round has no persisted checkpoint; do not reconstruct
> or invent its past usage from the new counters.

Read this first in a new conversation about the hat. It says what was done,
what was decided, what the tools now do and what comes next.

## Contents

- [State in one paragraph](#state-in-one-paragraph)
- [Files](#files)
- [How the work went](#how-the-work-went)
- [Rules that came out of it](#rules-that-came-out-of-it)
- [Tools built during the task](#tools-built-during-the-task)
- [Changed after the first handoff (same day)](#changed-after-the-first-handoff-same-day)
- [Pitfalls met in C1](#pitfalls-met-in-c1)
- [The model now](#the-model-now)
- [Next steps](#next-steps)
- [Opening prompt for the next conversation](#opening-prompt-for-the-next-conversation)

## State in one paragraph

ROADMAP item 1 (the modeling plan reviewed before modeling, D-065), on a new
concept: a straw cowboy hat from a 3/4 photo, real adult size, no body. A
blind plan (P1, written by a subagent) was reviewed by the modeler; the
method was corrected, then the modeler asked to model **in the conversation,
stage by stage**, stopping after each render for correction (run C1). The
crown and brim exist; the top's three dents (a middle crease, two egg-shaped
side dents, two mountains between them) were built partly by the AI and
partly by the modeler in the review Blender, watched with a new operator
recorder. Still to do on the hat: thickness (Solidify), band, buckle, tail,
materials, and a check that cage and result both "make sense" (D-078). The
round `C1 build` is still open (`round_start` was called; no `round_end`).

## Files

| path | what |
|---|---|
| `prompt.md` | the task: adult size, about 800 faces (later dropped: "não vamos nos preocupar com contagem de faces"), the planner's prompt |
| `concept.jpg`, `start.blend` | the photo, packed as the `Concept` Image Empty with `fofuxo_perspective = True` (shown beside the model on the sheet, never under its outline) |
| `ai/P1/plan.md` | the blind plan, reviewed (pixel-and-perspective reading, every cut decided ahead: both judged wrong in method) |
| `ai/C1/plan.md` | the conversation run's plan; its **Changes** section is the step-by-step log of everything that left the plan |
| `ai/C1/C1.blend` | the hat now (object `Chapéu`, collection `Chapéu`) |
| `ai/C1/C1_top_v1.blend` | copy before the top was rebuilt |
| `ai/C1/C1.cage/Chapéu.txt` | the cage text (ids, loops, faces) |
| `ai/C1/C1.cage/ops_egg.json` | the last 29 operators of the modeler's egg dent (before the recorder) |
| `ai/C1/C1.cage/ops_central.json` | all 343 operators of the modeler's middle dent (the recorder's first session) |
| `ai/C1/renders/sheet_central.png` | the latest Workbench render (3/4, front, high 3/4, top) |
| `ai/C1/workbench_render.py` | the Workbench render code (shaded, or with the cage over it) |

## How the work went

1. **P1, blind plan.** Read the photo in pixels with perspective math, cut
   every loop ahead. The modeler: read the form, not the pixels (D-066);
   start from the lowest cage and add loops where a check asks (D-067);
   every part of a soft model gets Subdivision (D-068); one render per
   silhouette stage (D-069); more than one route can be right (D-070).
2. **C1 in the conversation.** 12-sided cylinder, bottom cap deleted, two
   `extrude_scale` for the brim, crease on the crown-brim fold. Brim: the
   modeler asked for one more ring placed near the bend, to sharpen the
   curl. Crown: taper, pinch, crease from a formula; then the modeler:
   **go to half + Mirror once details start** (D-071). The cap was refilled
   (`fill_grid span=2 offset=11`) so a row of vertices ran on x = 0.
3. **The top rebuilt, the modeler's method.** Three dents (middle: like a
   cylinder's boolean; sides: like an egg's), two mountains between them.
   Delete the top down to the mid wall ring, extrude the rim up, extrude the
   mountain inward, a face for the mountain top, a temporary **Mirror Y**
   (`Mirror.001`, first in the stack; to apply once the side dent is good),
   a loop between v126 and v127. The modeler then edited in the review:
   "delete edge" means Delete > Edges, it opens a hole (D-073); the ridge
   raised 13-19 mm; the egg dent built as a center quad, a ring of quads
   around it and a ring to the mountain; the middle dent as the ridge
   extruded in place and pulled to the plane, closed with F2, then about 10
   minutes of small moves, LoopTools Circle/Space, slides, Sculpt Grab and
   Smooth.
4. **Report and rules.** The AI's reading of the recorded session became
   D-074 to D-079, approved by the modeler.

## Rules that came out of it

All in `DECISIONS.md`; the SKILL carries them (step 4, step 6, modifier
stack).

| | rule |
|---|---|
| D-066 | read a perspective photo for its form; one known size sets the scale; other references only to understand, never to trace |
| D-067 | lowest cage first, loops added where a check asks |
| D-068 | soft model: every part gets Subdivision, the band at the hat's level |
| D-069 | one render per stage that changes the silhouette |
| D-070 | more than one route can be right; name the route and why |
| D-071 | a cylinder goes to half and Mirror once the details start |
| D-072 | after the modeler's edit the AI saves, absorbs and closes (`collect()`) |
| D-073 | "delete edge" is Delete > Edges (opens a hole), not dissolve |
| D-074 | close a hole with the fewest faces, shape it after |
| D-075 | small steps (up to ~10 mm), a cheap check every 3-5 steps |
| D-076 | tidy tools first: LoopTools Circle/Space, edge/vert slide, scale an axis to 0 |
| D-077 | undo is part of the method |
| D-078 | cage and result must both make sense: faces about the size of their neighbours, loops evenly spaced |
| D-079 | the modeler records, the AI converts |

Also: `add` puts a modifier last, as Blender does: `add MIRROR at first`.

## Tools built during the task

In `extension/fofuxo_cage/` (README sections "View sheet" and "Two
Blenders"; tests pass, 244 checks):

- **Labels by mesh attributes** (`labels.py`): the sheet labels nothing by
  itself. `fofuxo_show_vertex` (ids), `fofuxo_loop` (edges drawn as one
  loop, closed across mirror planes, named by plane `h80` or `loop1`),
  `fofuxo_show_face`; all INT, **levels**: only the highest value present
  shows. `show(name, sel)`, `mark_loop(name, sel)`, `show_faces(name, sel)`
  open a new level by default; `level="add"` joins it, `level=1` on `"all"`
  resets. Each stage shows only what it works on.
- **Perspective concept**: an Image Empty with `fofuxo_perspective` is drawn
  whole beside the model, no outline.
- **`collect()`**: the human's review Blender saves, closes, then `absorb()`.
- **Operator recorder** in the review Blender (`review.ops.jsonl`, returned
  by `absorb()` as `operators`): every operator with its settings, UNDO and
  REDO, and, newer and **not yet tried in a real session**, the ids
  `selected` and how far each vertex `moved`, and `SCULPT` lines (brush,
  radius in px, strength, moved vertices). Tested only in a background
  simulation.
- Workbench renders: the sheet's panels are too small to judge a crown.
  `ai/C1/workbench_render.py` (`render(name, out, cage=False)`): 3/4,
  front, high 3/4 and top with a temporary camera, optionally the cage's
  edges and vertices drawn over the result; leaves nothing in the file.
  Run it with `exec(open(path).read(), ns)` through the MCP. To become one
  call of the extension (ROADMAP item 8).

## Changed after the first handoff (same day)

- **Name.** The extension is shown as **LLM Modeling Bridge**: the manifest,
  the READMEs, and every label, panel, tab ("LLM"), header and undo name in
  Blender. "Fofuxo" stays only in file, folder, module and data names
  (`fofuxo_cage`, `fofuxo_cage_id`...); renaming those to `fofuxo-bridge`,
  with a migration for saved files, is ROADMAP item 9.
- **The LLM's black screen** says, in Portuguese, that the window is the
  LLM's only, that the human asks in the conversation for a Blender of
  their own (or for this window to be released: not built yet, ROADMAP
  item 7), and not to close it while working together.
- **READMEs.** `README.md` (English) is only a Tip pointing to
  `README.pt-BR.md` (Portuguese, the full one: what the project is, the
  comparison with Tripo, the hat as example with `images/chapeu-cowboy/`
  (reference, a Workbench render, a cage sheet), how it works, a link to the
  roadmap). Both open with a `> [!TIP]` to the other language.
- **ROADMAP.md is the repository's main development file**, written for AI
  agents: how an agent uses it, only what is left (a finished item is
  removed, never marked done), the order of the next steps. Item 12 lists
  the token problems seen in C1 with their solutions, or "think of a
  solution".
- The recorder (above) gained ids, moves and Sculpt lines after the
  modeler's middle-dent session; `absorb()` returns them.

## Pitfalls met in C1

- `import fofuxo_cage.sync` (or any `import fofuxo_cage.<name>` whose name
  is also a function of the package) replaces the function on the package
  with the module: `fofuxo_cage.sync(...)` then fails with "module object is
  not callable". Use `sys.modules[...]` to reach a submodule; if it
  happened, `fofuxo_cage.sync = sys.modules["fofuxo_cage.sync"].sync`.
- After editing the extension's code, reload in the LLM's Blender:
  `importlib.reload(sys.modules[base + ".<module>"])`, then
  `importlib.reload(sys.modules["fofuxo_cage"])` (`base` is the package's
  real name, `sys.modules["fofuxo_cage"].__name__`). A review Blender
  already open keeps the old code: close it and `review()` again.
- Computer use: `open_application("Blender")` launches a new, empty
  Blender; to reach the review window click its title bar (the taskbar
  needs the "File Explorer" grant). Prefer `collect()`.
- In background Blender, operators called from a script do not enter
  `window_manager.operators`: the recorder's operator path can only be
  tested with a stand-in (see the recorder test in the conversation's
  approach) or in a real window.
- Blender 5.2 keeps the Sculpt brush's unified size and strength in
  `tool_settings.sculpt.unified_paint_settings`, not
  `tool_settings.unified_paint_settings`.
- A region selection like `h>500` also takes vertices far away (the brim's
  curled tip); add a second condition (`w>-100`) and preview with `select()`.
- Delete faces on a plane (`delete faces w>=500`) can leave faces whose
  vertices read a hair under 500; delete those with a `faces vA vB ...`
  list.
- A file the sheet writes can be locked (OneDrive); remove it and render
  again.

## The model now

- `Chapéu`: Mirror.001 (Y, temporary) > Mirror (X) > Subdivision (the
  modeler turned its viewport display off; renders turn it on). A quarter of
  the hat is modeled. Faces smooth-shaded.
- Brim: three rings (flat, bend, edge), sides curled up ~45 mm, front and
  back dipping ~10 mm. The brim's side tips came down ~13 mm in the
  modeler's last session (Sculpt, probably).
- Crown: band loop at 10 mm, mid wall loop, rim, mountains (ridge
  v125-v156-v147-v150-v131), egg dent, middle dent on the X plane.
- Known: v153 sat near the Y plane, not on it (`near_plane`), before the
  last session; check it again.

## Next steps

In `ROADMAP.md`, the table "Order": it is kept up to date and wins over any
list written here. For the hat itself, item 1 (Mirror Y, Solidify, band,
buckle, tail, materials, the D-078 check, `round_end` and the report).

## Opening prompt for the next conversation

> Projeto FofuxoModelingRules, chapéu de cowboy (ROADMAP, item 1).
> Ler primeiro: `ROADMAP.md` (instruções para agentes e a ordem dos
> próximos passos), `models/tasks/chapeu-cowboy/HANDOFF.md`, depois
> `models/tasks/chapeu-cowboy/ai/C1/plan.md` (seção Changes) e, do
> `DECISIONS.md`, só D-066 a D-079. Abrir o Blender da AI com
> `python extension/fofuxo_cage/launcher.py models/tasks/chapeu-cowboy/ai/C1/C1.blend`.
> Não ler: os runs do chifre, `ai/P1/` (já revisado), os `.json` de log
> inteiros (só se for analisar uma sessão). Seguir modelando por etapas na
> conversa, parando a cada render.
