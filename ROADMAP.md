# Roadmap

What to build next so the AI models with Blender's own tools, and how the
modeler's use of the tool turns into rules and examples.

- Give the AI Blender's modeling operators through the cage text: select by
  cage id, run the operator, read the result back.
- Let the modeler point at things in Blender (marks, annotations) and have
  every mark read and answered.
- Turn each round of feedback into measurable targets, named techniques and
  rules, with less re-reading and fewer tokens per session.
- Have the AI say how it will build a model, and the modeler judge that
  method, before any modeling (Part 2, item 11).

## Contents

- [Principles](#principles)
- [Part 1: Blender's tools for the AI](#part-1-blenders-tools-for-the-ai)
  - [Phase 0: the generic operator op](#phase-0-the-generic-operator-op)
  - [Phase 1: topology](#phase-1-topology)
  - [Phase 2: shaping without moving vertices one by one](#phase-2-shaping-without-moving-vertices-one-by-one)
  - [Phase 3: building new parts](#phase-3-building-new-parts)
  - [Phase 4: marks, normals and data](#phase-4-marks-normals-and-data)
  - [Phase 5: the human points, the AI answers](#phase-5-the-human-points-the-ai-answers)
- [Part 2: learning from use](#part-2-learning-from-use)
- [Order](#order)

## Principles

- **Wrap, don't rewrite.** When Blender has the tool, the extension selects
  and calls it; new bmesh code only for what Blender lacks (the modeler, B1
  round 5: "existem ferramentas no blender para fazer todas as edições que
  você está escrevendo scripts").
- **Keep what Blender lacks.** Stable ids, the cage as text, the check on
  every sync, shape measures, `target` and `fit`: these stay the extension's
  job.
- **Every op is safe to try.** Checked before it runs, undone if the result
  breaks a rule (quads, mirror planes, no loose geometry), reported in
  numbers (vertices added or removed, new ids, the size and the deviation
  from before).
- **One line per edit.** An edit the AI makes often costs one line of text,
  never a new script per session.

## Part 1: Blender's tools for the AI

### Phase 0: the generic operator op

```
mesh <operator> <selection> [key=value ...]
  mesh dissolve_edges seam
  mesh loopcut_slide ring v25-v22 number_cuts=2
  mesh vertices_smooth v24 v25 v26 factor=0.5 repeat=2
```

- **Selection grammar** (shared with `crease`, `dissolve`): ids (`v25`),
  pairs (`v25-v22`), loop labels (`L3`), `plane-x/y/z`, marks (`sharp`,
  `seam`, `crease`), and walkers: `loop vA-vB` and `ring vA-vB` through
  Blender's `select_edge_loop_multi` / `select_edge_ring_multi`, `path vA vB`
  (`shortest_path_select`), `faces vA vB vC vD`.
- **Running:** the object's lock is taken (it leaves Edit Mode for the
  human), the mesh enters Edit Mode, the selection is set by id through
  bmesh, the operator runs under a 3D View override, the mesh leaves Edit
  Mode, and the sync pulls the result. New vertices take ids as a human's
  edit would.
- **Whitelist** of operators with their parameters written down (name,
  meaning, unit), so the AI does not guess; anything outside it is refused
  with the list.
- **Safety:** a copy of the mesh is kept; if the checks fail after the
  operator, the copy comes back and nothing is written.
- **Report:** what changed in topology (`+6 v, -0 v, faces 14 -> 20, all
  quads`), the new ids, and the deviation from the shape before (mm).
- **Replaces** the hand-written `dissolve` and `cut` of round 5 (they stay
  as aliases for the same operators, with their tests).
- **Done when:** the round-5 loop removal and the test's loop cut pass
  through `mesh` with the same results.

**Status: done (2026-09-29).** `mesh_ops.py` and `selection.py`; the
whitelist starts with `dissolve_edges`, `dissolve_verts`, `delete_edgeloop`,
`loopcut_slide`, `subdivide_edgering`, `vertices_smooth` and `translate`
(with proportional editing). `fofuxo_cage.edit(name, line)` writes a line and
syncs, `select(name, text)` previews a selection. Checked on copies:
- the round-4 file (git `0d8e8b5`) with the loop v9 v8 v11 v12 v7 v22 v4
  marked sharp: `mesh dissolve_edges sharp` gives exactly round 5's topology
  (29 -> 22 vertices, 20 -> 14 quads). Blender's `dissolve_edges` already
  takes the pole's last spoke, so the bmesh code for it went away;
- the round-6 seams of `human/B1-human-edit.blend` (v15-v27, v23-v32,
  v27-v32): `mesh translate seam d=+3% falloff=smooth radius=25%` moves them
  3% deeper and 4 neighbours by 0.1-0.5%; surface max 0.34 mm, the section at
  w 850 goes from d 837 to 852.

### Phase 1: topology

| Need (seen in) | Blender operator |
|---|---|
| Remove a loop (B1 r5) | `dissolve_edges`, `delete_edgeloop`, `dissolve_verts` |
| Add a loop for a fold (D-036, D-039) | `loopcut_slide` (EXEC with an edge ring), `subdivide_edgering`, `offset_edge_loops_slide` |
| Even out loop spacing | `space_edge_loops_evenly`, LoopTools `space` |
| Lighter cage where it carries no shape (D-045) | `dissolve_limited`, `unsubdivide`, `edge_collapse` |
| Merge, weld, close gaps | `merge`, `remove_doubles` (Merge by Distance) |
| Turn an edge for flow, remove poles | `edge_rotate`, `tris_convert_to_quads` |
| Join two parts, fill a hole | `bridge_edge_loops`, `fill_grid` |

Each row gets a line in the whitelist and a test on the E1 copy.

**Status: done (2026-09-29).** Every row is in the whitelist, plus `delete`
and `edge_face_add` (a hole to bridge or fill). Tests on the E1 copy and on
a plain grid made in the test: `edge_rotate` there and back, `delete` +
`edge_face_add`, `bridge_edge_loops` over a deleted row, `fill_grid` over a
deleted block, `subdivide_edgering`, `space_edge_loops_evenly` putting a
moved row back; `edge_collapse`, `merge`, `unsubdivide` and
`offset_edge_loops_slide` on a loop that ends on a plane are refused (they
leave triangles on the cage). Found on the way:
- a 3D View left in Local View made every Edit Mode operator skip an object
  outside it (`CANCELLED`, nothing said): the op now takes the object into
  the Local View and lets it out after;
- `space_edge_loops_evenly` works on the rings across the loops, two deep;
- `bridge_edge_loops` needs the two loops' edges listed: on a border, the
  `loop` walker selects the whole border.

### Phase 2: shaping without moving vertices one by one

The round-5 lesson: moving single vertices bends the cage; Blender's shaping
tools move a region the way a modeler would.

- **Pull with falloff:** `transform.translate` with proportional editing
  (`mesh translate seam d=+3% falloff=smooth radius=12%`). The seam-marked edges
  of B1 round 6 are this case: pull toward -Y, neighbours follow.
- **Slide along the surface:** `transform.edge_slide` / `vert_slide`: move a
  loop without changing the shape it rests on (to tighten a loop toward a
  fold, D-039).
- **Along the normals:** `transform.shrink_fatten` (inflate or thin a
  region evenly).
- **Round:** `transform.tosphere`, LoopTools `circle` (a round section),
  `relax`, `vertices_smooth` (`vertices_smooth_laplacian` was tried: see
  the status below).
  The knot's roundness (D-051) would take one line.
- **Symmetry:** `symmetrize`, `symmetry_snap` for parts modeled whole.
- **Measured, then accepted:** each shaping op reports the section and
  profile change it caused (`sections`, `profile`), so the AI checks the
  numbers, not a render.
- LoopTools is an extension, and part of the toolset (the modeler, step 1):
  `ensure_looptools()` enables it from disk or installs it from
  extensions.blender.org on a machine without it (done in step 1).

**Status: done (2026-09-29).** In the whitelist: `translate` (the pull, with
proportional editing), `edge_slide`, `vert_slide`, `shrink_fatten`,
`push_pull`, `tosphere`, `vertices_smooth`, LoopTools `circle`, `relax`,
`space`, `symmetrize`, `symmetry_snap`. Every op now reports how each view's
outline changed (`profile top +0.6 mm at 0.60`). Found on the way:
- `vertices_smooth_laplacian` left out: on a 28-vertex cage it moves
  nothing on a part and blows the whole up at the strength that moves it;
- LoopTools `circle` and `relax` are for loops off the mirror planes: a
  loop that ends on a plane is half of one, and the check refuses the result;
- `symmetrize` on a mirrored half crosses the plane and is refused: it is
  for parts modeled whole;
- a refused `edit()` puts the text back, so the refused line does not run
  again with the next call.
Example on a copy of the modeler's B1 edit: `mesh shrink_fatten faces v14
v15 v26 v27 v20 v28 v22 v32 v33 value=0.6mm falloff=smooth radius=20%`
makes the lobe's outer side 3.5% deeper; the section at w 850 goes from d
837 to 875 and its exponent from 3.6 to 3.45 (rounder).

### Phase 3: building new parts

For the next examples (the hat, the skirt ruffles), where there is no cage
to start from.

- **Start:** `primitive_*_add` with its parameters, or a cut and mirrored
  half (D-034); the part is framed and synced at once.
- **Grow:** `extrude_region_move`, `extrude_context_move`, `inset`, `spin`,
  `screw`, `bevel` (edges or vertices, with segments).
- **Cut:** `bisect` (a plane), `knife_project` (a shape onto the mesh; the
  interactive knife has no EXEC mode).
- **Split and join:** `separate`, `split`, `rip`, object join.
- **Sit on another part (D-029):** extract faces of the body, then
  Shrinkwrap through the modifier ops already there.

**Status: built (2026-09-29), revised after the modeler's review of a top
hat: cylinders whole (D-061), caps of quads, smaller vertex marks in the
views, `h92%` accepted for planes.** `start_part()`, regions in the selection
grammar (`h>900`, `faces h>900`), `resize` (added when the first real build
needed it), the extrudes, `inset`, `spin`, `screw`, `bevel`, `bisect`,
`separate`, `extract` and the `join` op; `rip` and `knife_project` left out
(they need the mouse or the view). Tests: a quarter cylinder grown into a
hat (inset, extrudes, bisect, resize, bevel), extract + Shrinkwrap onto it,
separate and join back, spin and screw on a disc. A top hat from seven
lines as a check of the toolkit (extension README, "New parts"); it found
the missing `resize`, a region read as a parameter, and a bug in the text:
wide values ran together (`500-10000`), now always spaced.

**The plan it followed.** Every operator named
here exists in Blender 5.2.2 with the parameters used (checked); whether each
runs under the 3D View override is for the tests:

1. `fofuxo_cage.start_part(name, primitive, size, mirror="XY", subdivision=1,
   parent=None, at=None)`: `primitive_cylinder_add` / `uv_sphere_add` /
   `cube_add` / `circle_add` with its vertex counts, then `bisect` with
   `clear_outer` to keep the modeled side (D-034, model on -Y, D-055), Mirror
   with merge 0.1 mm (D-054) and Subdivision, the frame set from `size` (mm)
   and a first sync. One call gives a cage the AI edits with text.
2. Grow, in the whitelist, lengths in mm or % of the frame:
   `extrude_region_shrink_fatten` (out along the normals), `extrude_region_move`
   (along w, d, h), `extrude_context_move`, `inset` (thickness, depth),
   `spin` (steps, angle, around a frame axis through a frame point), `screw`,
   `bevel` (width, segments, edges or vertices), `bisect` (a plane given as
   `w 500` or `h 250`).
3. Split and join: `separate` (the new object synced with its own text and
   fresh ids), `split`; object `join` as an object op. `rip` and
   `knife_project` tested and left out: `rip` returns PASS_THROUGH without
   the mouse; `knife_project` finishes without cutting in background (the
   view's matrices update only when the window draws). `bisect` does the
   straight cuts.
4. Sit on another part (D-029): `duplicate` + `separate` the body's faces
   into a new part, then `add SHRINKWRAP` and `set Shrinkwrap target <body>`
   with the stack ops already there.
5. Tests: a hat-like part from a cylinder (start, extrude the brim, inset
   and extrude the crown, bevel, bisect), all quads and fresh ids at every
   step; a separated part and a joined one; a ribbon extracted and
   shrinkwrapped.

### Phase 4: marks, normals and data

**Status: done (2026-09-29).** `mark_seam`, `mark_sharp`, `crease` and
`bevel_weight` by selection; `normals_make_consistent`, `flip_normals`, and an
`inside_out` warning on every sync (a closed result with a negative volume);
`vertex_group_assign` / `vertex_group_remove_from` with a weight; `unwrap`
after seams from marks.

- `mark_seam`, `mark_sharp`, crease and bevel weight by selection (the AI
  can mark for the human too).
- `normals_make_consistent`, face orientation checks after every op.
- Vertex groups by selection (for Shrinkwrap, Displace, later rigs: rig is
  out of scope, D-017).
- UV: seams from marks and a basic unwrap, only when a task asks for it.

### Phase 5: the human points, the AI answers

- **Marks are messages.** Every sync lists the marks found since the last
  one (`sharp: v9-v8 ...`, `seam: v15-v27 v23-v27`) under `marks`, so none
  goes unseen. The meanings (D-060, confirmed): sharp or seam on a loop =
  "this loop" (remove, move, look), crease = "pinch here".
  Once acted on, the AI clears its marks and says so.
- **Annotations.** Strokes drawn with Blender's Annotate tool read as 3D
  points; the sync names the vertices under each stroke. A way to say
  "here" without selecting.
- **Two Blenders (done, D-058).** The AI works in a Blender of its own
  (`launcher.py`: a black screen, input swallowed, the MCP server); the human
  sees and changes the model in a normal Blender (`review`), and what the
  human saves comes back through the sync (`absorb`). Checked live: a
  human's Blender already on port 9876 lets it go to the AI's within 3 s.
- **Human edits explained.** When the modeler moves vertices, the sync's
  deltas come with a guess of the intent (`L1 rim up 4%: the silhouette was
  low?`) that the AI asks about, as `models/FEEDBACK.md` describes.

**Status: done (2026-09-29).** Every sync reports `marks` (new and cleared,
with their reading, D-060), `annotations` (new strokes and
the vertices under each, a stroke on the mirror copy counting for the
modeled side) and `blender_by_loop` (the human's moves grouped by loop: the
tool gives the shape of an edit, the AI reads the intent and asks).
`mark_seam` / `mark_sharp` with `clear=on` and `clear_annotations()` clear
what was acted on; `absorb()` brings the strokes from the review Blender.
The modeler's B1 edit read this way into a copy of round 5: `L2 3/5
d+21.5%`, `L3 4/5 d+10.2% h-15.6%`, `L4 4/5 d+12.0%`, `L1 6/7 w+0.4%`
(deeper lobes, the rim kept), seams new on v23-v32 v27-v32. Found on the
way: a removed vertex's id could come back on a new one when a loop cut
interpolated it (`+v22` in that read); an id below `next_id` that the last
sync did not have now gets a fresh one.

## Part 2: learning from use

What would improve the modeling as the modeler uses the tool, and where each
piece goes.

1. **(Done.) Numeric targets per task.** Each form in the shape map gets a measure
   and a target taken from the reference (waist ratio, section exponent,
   top profile, face count), written in the task's `target.md`. The AI
   stops when the numbers are in, and the modeler judges what numbers miss.
   Round 5 showed it works: the pinch went from "fraco" to the modeler's
   ratios in one pass once it was measured.
   Done: a ` ```targets ` block in `target.md`, measured by
   `check_targets()`. The targets come from the modeler's latest edit
   (D-059): it passes 15/15, round 5 fails on what the modeler changed.
2. **(Done: `models/TECHNIQUES.md`, the bow tie's "Techniques", and the
   pointer in `SKILL.md`'s workflow, step 4.) A technique library.** Named techniques in each example's `EXAMPLE.md`,
   one block each: when to use it, how (in cage words), how to measure it,
   the source. Already there in draft: the pinch into the knot, the heart
   lobes, the 10-vertex round knot, the silhouette rim on the Y plane, the
   cage bigger than the result. `SKILL.md` would point to the index and read
   a technique only when the concept shows that form.
3. **Measures kept with each example** (`measures.json`, started for the
   bow tie): read instead of re-measured; each new example gets one when
   it is catalogued.
4. **(Done: "Rule candidates" in `DECISIONS.md`.) Rule candidates with a
   count.** A list in `DECISIONS.md` of items seen
   once (Provisional) with the case that would promote them; at the end of
   a session the AI asks about the ones that got a second case. Today's
   candidates: the marks convention; "remove a loop that carries no shape,
   refit the volume" (D-045, second case); "a tight row next to a thin row
   keeps a pinch" (D-039, second case).
5. **(Done: `poly_budget` in every sync.) Poly budget warning.** The task's target holds the reference's face
   count; the sync warns past it (for example 20% over). "Muito high poly"
   would have been caught before the modeler saw it.
6. **(Done: `editability()`, E1's numbers in `measures.json`. The offset's
   evenness is a number to compare, not a grade: E1 is less even than the
   modeler's B1 edit.) Editability measured.** `cage_dips` today; next, how even the cage's
   offset from the surface is, and pole count and placement against the
   reference's. The modeler's cage is the yardstick.
7. **(Done: `models/FEEDBACK.md`, first one in `ai/B1-opus-cage/NEXT.md`.)
   A session brief file per run.** `ai/<run>/NEXT.md`: open items, files
   to read, measures to trust, what not to touch. Written at the end of
   each session, read first in the next: fewer tokens than re-reading the
   history, and the modeler can edit it.
8. **(Done: `round_start()` / `round_end()`, `rounds.json`, a line for
   `report.md`; tokens from the session.) Cost per round.** Time and tokens in each `report.md` (still "not
   measured"), to see whether the tools actually make rounds cheaper.
9. **Transfer tests.** A new task (the hat, T2) run with and without the
   technique library, judged blind as in T1: do the rules carry to a part
   the AI has not seen?

   **Status: run and judged (2026-09-30).** The modeler, blind: T2-B
   (without the techniques) better, both "muito ruins": both traced the
   concept's horns and ignored the body already in the file. The answer so
   far is no: the library did not carry, and the failure was one no
   technique covers, now D-063 (a part on a body is built on the body). The
   numbers, and what the runs found in the tools, in
   `models/tasks/chifre/judge/results.md`. Next: fix the tools the runs hit,
   then run T2 again with D-063 in the skill (T2-C with the techniques, T2-D
   without) to see whether the rule closes the gap.
   **Second pair judged (2026-10-01):** T2-D (without the techniques)
   better again; D-063 brought the horns down onto the head, but the base
   is still thin: the runs copy the visible outline instead of reading what
   the 3D needs (D-064). Twice the library lost: it does not carry to the
   horn as it stands. The tool gaps this pair found were fixed the same
   day (`judge/results.md`): `mesh rotate`, `resize around=selection`,
   `sections(name, "rings")`, `start_part(on=...)`, a new Mirror's merge.
   `models/tasks/chifre/`: `start.blend` (the posed body and its rig, the
   concept behind it at the body's scale, no horn), `prompt.md` (the prompt
   and what each run may read), `judge/target.md` (11 targets from E1's
   horn, E1 11/11; out of `find()`'s reach from a run's folder). New target
   measures for a part mirrored across another object: `world min|max|size`,
   `base` and `tip`, one side in world mm.

   **Plan (step 7).**
   - **The part (the modeler's pick): `Chifre`**, no rule came from it. A
     cube extruded with its loops rotated along the curve, no mirror of its
     own (Mirror X across the body makes the pair), Subdivision 1/2, 57
     vertices, 52 quads, open where it enters the head. The hat was not a
     clean transfer: D-024, D-026 and D-029 came from it.
   - **Task folder** `models/tasks/<part>/`: `start.blend` with the concept
     packed and the part removed; `prompt.md`; `target.md` with numeric
     targets from the modeler's part, hidden from the runs (the AI reads
     only the concept and the prompt).
   - **Runs**, same model (Opus 5.5), same prompt, same tools (Fofuxo Cage,
     its own Blender): T2-A with `models/TECHNIQUES.md` and the bow tie's
     techniques; T2-B without them. Neither reads the part's own example
     nor opens E1 (the modeler's part is in it).
   - **Judged** blind by the modeler, as in T1: the two results as "model 1"
     and "model 2" in a random order, in a review Blender each; then the
     numbers (`check_targets`, `editability` against the modeler's part).
     Cost and time per run in each `report.md` (item 8).
   - **The question it answers:** does a run with the library get closer
     to the modeler's part, in the modeler's eyes and in the numbers, than
     one without?
10. **The modeler's edits as examples.** When the modeler fixes an AI cage
    in Blender, save the edit in `human/` (the README convention) and file
    the deltas with their why: each fix is a small example of a technique.
11. **The modeling plan, reviewed by the modeler before any modeling
    (D-065).** The T2 runs cost about 180-220k tokens a horn, most of it
    finding commands by trial, and two judged pairs showed the method was
    wrong before the shape was (D-063, D-064). The AI now says how it would
    build the model and the modeler judges the method first. The horn task
    (`models/tasks/chifre/`) stays as it is; the plan is validated on a new
    concept.

    **Built (2026-10-01):** SKILL step 5 and
    `skill/fofuxo-modeling-rules/PLAN.md` (the sections: Read, Parts, Stack,
    Commands, Checks, Budget, Risks, Changes); `round_start(label,
    plan=...)` refuses an incomplete plan, the sync warns past its budget
    (`round_budget`), the cost line shows plan against done.

    **To validate, in order** (on a new concept, not the dragon: the
    modeler's choice, 2026-10-01, to see the AI build from nothing):
    1. **The task.** `models/tasks/chapeu-cowboy/`: `concept.jpg` (a straw
       cowboy hat, a 3/4 photo: perspective, not an orthographic front),
       `prompt.md` and `start.blend` with the concept as an Image Empty. No
       body to sit on and no modeler's part to measure against: the modeler's
       judgment is the reference. Asked of the modeler before the prompt is
       written: the size (a real adult hat, or a stylized game asset at
       another scale) and the poly budget.
    2. **A plan, written blind.** A fresh context (a subagent) reads
       `SKILL.md`, `PLAN.md`, the README's op tables and the task, and
       writes only `models/tasks/chapeu-cowboy/ai/P1/plan.md`; Blender only
       to read the scene, no modeling call. Not read: `ROADMAP.md`,
       `DECISIONS.md` (the skill carries the rules), the other tasks' runs.
    3. **The modeler reviews the method.** The session shows the plan to the
       modeler in Portuguese, section by section: how the photo is read (the
       perspective, the crown's pinch and dents, the brim's curl up at the
       sides and down at front and back, the band), the primitive and how the
       shape is reached, the modifiers and their order, the commands, the
       checks, the budget. The modeler marks each one good, wrong or missing,
       and says how they would build it.
    4. **The answers become rules.** Each correction of method goes to
       `DECISIONS.md`, and to `PLAN.md` or `SKILL.md` when it changes how
       every plan is written. Steps 2-3 again (P2, ...) with the corrected
       skill until the modeler approves the plan.
    5. **The approved plan, built.** A run builds it in its own Blender: its
       cost (minutes, syncs, renders, tokens) against the T2 horns' 180-220k,
       its Changes log (how far the build left the plan), and the modeler's
       verdict on the hat.

    **Validated when** the modeler approves the method in at most two
    reviews and the hat built from it costs at most half of a T2 horn (about
    100k tokens) and is judged good. A second new concept, chosen by the
    modeler, then checks that the plan carries. What a review cannot settle
    goes to the open questions in `DECISIONS.md`.

12. **Rename Fofuxo Cage to LLM Modeling Bridge.** The modeler's choice
    (2026-10-01): "Fofuxo" may stay in file names and the repo's name, never
    in what a user sees in Blender. Done so far: the extension's display
    name (manifest), the READMEs, and every label, panel, tab, header and
    undo name in Blender (they say "LLM"). To do:
    - the files and the module: `extension/fofuxo_cage/` to
      `extension/fofuxo-bridge/`, the extension id and the import name
      (`fofuxo_cage`, used by every call), the launcher;
    - the data names saved in `.blend` files (`fofuxo_cage_id`,
      `fofuxo_cage_lock`, `fofuxo_show_vertex`, `fofuxo_loop`,
      `fofuxo_show_face`, `fofuxo_review`, `fofuxo_on`,
      `fofuxo_perspective`) and the `<file>.cage/` folders, with a migration
      that renames them when an old file is opened, so saved files keep
      working;
    - "Fofuxo Cage" and "cage text" in `SKILL.md`, `DECISIONS.md`, this
      roadmap, the console messages and the tests.

## Order

| Step | What | Why first |
|---|---|---|
| 1 | Phase 0 + `seam` in the selection grammar (**done**) | unlocks every other operator; the round-6 seams need it |
| 1b | The AI's own Blender and the human's review (D-058, **done**) | the AI tests every tool alone, the human reviews in a normal Blender |
| 2 | Phase 2: pull with falloff, slide, smooth, to sphere (**done**) | the next edits on B1 are shaping, not topology |
| 3 | Part 2 items 1, 5, 7 (targets, poly budget, session brief) (**done**) | cheap, and each round gets cheaper |
| 4 | Phase 1 whitelist complete (**done**) | covers the loop work of the next examples |
| 5 | Phase 5 marks report and annotations (**done**) | the modeler's way of pointing, made reliable |
| 6 | Part 2 items 2, 4, 6 (technique library, candidates, editability) (**done**) | turns B1's lessons into reusable knowledge |
| 7 | Phase 3 (**built**) and a transfer test on the horn (two pairs **judged**: D-063, D-064) | when the bow tie is accepted |
| 8 | Part 2 item 11: the modeling plan (**built**), reviewed by the modeler on a new concept (a cowboy hat, from nothing), then built from the approved plan | the runs cost too much, and the method was wrong before the shape (D-063 to D-065) |
| 9 | Part 2 item 12: rename to LLM Modeling Bridge, files to `fofuxo-bridge` (the display names **done**) | the name a user sees says what the tool is |
