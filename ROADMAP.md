# Roadmap

> [!IMPORTANT]
> **This file is written to be read and acted on by AI agents** that carry
> on the development of this repository. It is the repository's main
> development file: start here, take the next step from [Order](#order),
> and keep this file true when you finish.

What is still to be built so a text LLM models in Blender with Blender's own
tools, and learns from the modeler's use of them.

## How an agent uses this file

1. **Read** this file, then only what the step names (each item points to
   its files). Do not read the whole repository: `DECISIONS.md` is long,
   read the decisions an item cites.
2. **Take the first step in [Order](#order)** that is not blocked, unless
   the modeler asks for another. Say which one before starting.
3. **Work with the modeler, not around them.** Modeling is done in stages,
   in the conversation, stopping after each render for the modeler's
   correction; the modeler's edits come back through the review Blender
   (`collect()`). A correction of method becomes a decision in
   `DECISIONS.md` (with the modeler's words) and, when it changes how every
   model is built, a line in `skill/fofuxo-modeling-rules/SKILL.md`.
4. **Tools:** the extension (`extension/fofuxo_cage/`, its README lists every
   call) runs in the LLM's own Blender
   (`python extension/fofuxo_cage/launcher.py <file.blend>`). Run its tests
   after any change to it (README, "Tests").
5. **Keep this file true.** Only what is left goes here: when an item is
   done, remove it, renumber, and update [Order](#order). Do not mark items
   done: what an item built is in the extension's README, the rules it gave
   are in `DECISIONS.md`, and the history is in git. A new need found while
   working becomes a new item, with what is left and the files to read.
6. **Code, comments, file names and commit messages in English;** talk to
   the modeler in Portuguese, with Blender's terms in English (vertex, edge,
   Subdivision).

## Contents

- [How an agent uses this file](#how-an-agent-uses-this-file)
- [Principles](#principles)
- [To do](#to-do)
- [Order](#order)

## Principles

- **Wrap, don't rewrite.** When Blender has the tool, the extension selects
  and calls it; new bmesh code only for what Blender lacks (the modeler, B1
  round 5: "existem ferramentas no blender para fazer todas as edições que
  você está escrevendo scripts").
- **Keep what Blender lacks.** Stable ids, the mesh as text, the check on
  every sync, shape measures, `target` and `fit`: these stay the extension's
  job.
- **Every op is safe to try.** Checked before it runs, undone if the result
  breaks a rule (quads, mirror planes, no loose geometry), reported in
  numbers (vertices added or removed, new ids, the size and the deviation
  from before).
- **One line per edit.** An edit the LLM makes often costs one line of text,
  never a new script per session.

## To do

1. **Finish the cowboy hat (run C1) and judge the method** (D-065: the
   plan reviewed before modeling, then the build). The
   blind plan (P1) was reviewed and its corrections became D-066 to D-070;
   the build then moved into the conversation, stage by stage, with the
   modeler correcting each render and building the top's dents in the
   review Blender (D-071 to D-079). State and files:
   `models/tasks/chapeu-cowboy/HANDOFF.md`. Left:
   - apply the temporary Mirror Y once the side dent is approved;
   - thickness (`add SOLIDIFY after Subdivision`), the band extracted from
     the crown's band row, the buckle and the tail (Mirror X and
     Subdivision), materials;
   - a check that cage and result both make sense (D-078);
   - `round_end`, `ai/C1/report.md` with the cost line, and the modeler's
     verdict on the hat and on the method.
   **Done when** the modeler judges the hat good and the method approved;
   the cost is reported against the T2 horns' 180-220k tokens a horn.
2. **A second new concept, chosen by the modeler,** built the same way,
   to see whether D-066 to D-079 carry without the modeler explaining as
   much. What a session cannot settle goes to the open questions in
   `DECISIONS.md`.
3. **Try the operator recorder in a real review.** The review Blender
   writes every operator, UNDO and REDO to `review.ops.jsonl`; the newest
   part (the ids `selected` and `moved` per operator, `SCULPT` lines with the
   brush, radius, strength and moved vertices) passed only a background
   simulation. Check it on a session with Edit Mode and Sculpt (Grab,
   Smooth) and turn what it shows into ops the LLM can run (D-079).
4. **Record mouse and keys, turned into the model.** A modal listener in
   the review Blender (as Screencast Keys does): each press and release
   with the vertex under the cursor and the point on the surface, a drag as
   a few points on the surface, the shortcuts (G, S, R, Ctrl+R, E, F2, X)
   with their modifiers. A Grab stroke then reads as "from v152, 12 mm up
   and out, radius 40 mm": one `translate ... falloff=smooth`.
5. **Region names as vertex groups.** The modeler and the LLM name regions
   ("crista", "fundo do ovo") as vertex groups, which Blender selects by,
   shows in its panel and keeps through operators; the selection grammar,
   the sheet and the recorder speak of regions by name. Single vertices
   keep their ids in the id attribute.
6. **An evenness check (D-078).** Each face's size against its neighbours'
   and the spacing of loops, on the cage and on the subdivided result,
   reported on every sync like `cage_dips`.
7. **Let the human edit in the LLM's window.** The black screen's notice
   says the LLM opens a new Blender for the human "ou liberará a edição
   usando essa janela": only the first exists. Lifting the screen and
   blocking the LLM's edits while the human works there, then giving the
   window back.
8. **Workbench renders as a tool.** The sheet's panels are too small to
   judge a crown; C1 used ad hoc code for a temporary camera and a
   Workbench render (3/4, front, high 3/4, top, optionally the cage drawn
   over the result). Make it one call that leaves nothing in the file.
9. **Rename Fofuxo Cage to LLM Modeling Bridge.** The modeler's choice
   (2026-10-01): "Fofuxo" may stay in file names and the repo's name, never
   in what a user sees in Blender. The display name, the READMEs and every
   label in Blender are renamed already. Left:
   - the files and the module: `extension/fofuxo_cage/` to
     `extension/fofuxo-bridge/`, the extension id and the import name
     (`fofuxo_cage`, used by every call), the launcher;
   - the data names saved in `.blend` files (`fofuxo_cage_id`,
     `fofuxo_cage_lock`, `fofuxo_show_vertex`, `fofuxo_loop`,
     `fofuxo_show_face`, `fofuxo_review`, `fofuxo_on`,
     `fofuxo_perspective`) and the `<file>.cage/` folders, with a migration
     that renames them when an old file is opened, so saved files keep
     working;
   - "Fofuxo Cage" and "cage text" in `SKILL.md`, `DECISIONS.md`, the
     console messages and the tests.
10. **The modeler's edits as examples.** When the modeler fixes an LLM cage
    in Blender, save the edit in `human/` (the README convention) and file
    the deltas with their why: each fix is a small example of a technique.
    The recorder (item 3) gives the steps, not only the result.
11. **Measures kept with each example.** `measures.json` exists for the bow
    tie; the hat and the skirt ruffles (E1) get theirs when catalogued, so
    the LLM reads them instead of measuring again.

12. **Fewer tokens per model: measure, then cut.** The modeler's goal is a
    model from an approved plan without the cost of the T2 horns (180-220k
    tokens a horn); nothing is promised yet. Each problem below was seen in
    the C1 session (about 560k tokens of context, half of it messages), with
    its solution, or marked to think of one.
    1. **Nobody knows where the tokens go.** Solution: `round_end` writes the
       cost by kind: renders made (count, pixels), tool reports (sync, edit,
       absorb: count and characters), the agent's own text where it can be
       read. Think of a solution for counting what the agent reads outside
       the extension (files, images it opens), and for the real token cost
       of an image of a given size.
    2. **The context piles up.** Every new message re-reads the whole
       conversation, so a long session costs more per turn as it grows.
       Solution: one stage or one tool per session, opened from a brief
       (`HANDOFF.md`, `NEXT.md`) instead of the history; the brief written at
       the end of each session.
    3. **Images bigger than the question.** About 25 sheets and renders were
       read, most with three views where one mattered. Solution: a render of
       the region the stage changed, one view when one is enough, at the
       smallest size that still reads; the full sheet only when the whole
       object is in question.
    4. **Reports longer than needed.** `sync`, `edit` and `absorb` return
       every op's profile and surface lines and lists of dozens of vertices.
       Solution: a short answer by default (action, counts, issues, what
       moved by region), the full report on request.
    5. **Throwaway scripts.** Regex edits of the cage text to set many
       vertices' positions, the Workbench render, reading a region's ids:
       written ad hoc several times, 1-3k tokens each. Solution: one call
       each (`set_positions`, a Workbench render call, a region-ids call).
    6. **Raw recorder logs.** The modeler's 343 operators were read as JSON
       and summed up by the agent. Solution: `absorb` sums them itself
       (operators by kind, moves by region, undos), the raw log on request.
    7. **A blind subagent for the plan.** P1 alone cost about 140k tokens and
       its method was replaced. Solution: the plan written in the
       conversation, short, and reviewed there.
    8. **Tools built in the middle of modeling.** Debugging the sheet, the
       recorder and their tests inside the modeling session filled its
       context. Solution: tools in sessions of their own. Think of a solution
       for a tool need found mid-stage (the modeler asks for it now): how to
       build it apart and come back to the stage without losing it.
    9. **Commands found by trial.** Solution: the modeler's recorded steps
       (item 3) become techniques with their ops, run instead of found. Think
       of a solution for why the technique library did not carry in the T2
       horns (twice the run without it was judged better: D-063, D-064), so
       recorded techniques do carry.
    10. **Docs read whole.** The README's op tables and the skill are long.
        Solution: a short card of the ops (one line each) and the skill read
        by section.

## Order

| Step | What | Why first |
|---|---|---|
| 1 | Item 12, its first part: measure where the tokens go | every cut after it is checked against numbers |
| 2 | Item 3: the recorder in a real review | the next steps of the hat are recorded sessions |
| 3 | Item 1: finish the hat and judge the method | the open run; every rule since D-066 is waiting on its verdict |
| 4 | Items 5 and 6: region names, the evenness check | what the hat's sessions asked for |
| 5 | Item 4: mouse and keys | the Sculpt and the drags the recorder cannot place |
| 6 | Item 2: a second concept | checks that the rules carry |
| 7 | Items 7, 8, 9 | the tools and the name, once the method holds |
| 8 | Items 10, 11 | the example catalog |
