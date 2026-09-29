# Roadmap

What to build next so the AI models with Blender's own tools, and how the
modeler's use of the tool turns into rules and examples.

- Give the AI Blender's modeling operators through the cage text: select by
  cage id, run the operator, read the result back.
- Let the modeler point at things in Blender (marks, annotations) and have
  every mark read and answered.
- Turn each round of feedback into measurable targets, named techniques and
  rules, with less re-reading and fewer tokens per session.

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

### Phase 2: shaping without moving vertices one by one

The round-5 lesson: moving single vertices bends the cage; Blender's shaping
tools move a region the way a modeler would.

- **Pull with falloff:** `transform.translate` with proportional editing
  (`mesh pull seam d +3% falloff=smooth radius=12%`). The seam-marked edges
  of B1 round 6 are this case: pull toward -Y, neighbours follow.
- **Slide along the surface:** `transform.edge_slide` / `vert_slide`: move a
  loop without changing the shape it rests on (to tighten a loop toward a
  fold, D-039).
- **Along the normals:** `transform.shrink_fatten` (inflate or thin a
  region evenly).
- **Round:** `transform.tosphere`, LoopTools `circle` (a round section),
  `relax`, `vertices_smooth`, `vertices_smooth_laplacian` (keep volume).
  The knot's roundness (D-051) would take one line.
- **Symmetry:** `symmetrize`, `symmetry_snap` for parts modeled whole.
- **Measured, then accepted:** each shaping op reports the section and
  profile change it caused (`sections`, `profile`), so the AI checks the
  numbers, not a render.
- LoopTools is an extension, and part of the toolset (the modeler, step 1):
  `ensure_looptools()` enables it from disk or installs it from
  extensions.blender.org on a machine without it (done in step 1).

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

### Phase 4: marks, normals and data

- `mark_seam`, `mark_sharp`, crease and bevel weight by selection (the AI
  can mark for the human too).
- `normals_make_consistent`, face orientation checks after every op.
- Vertex groups by selection (for Shrinkwrap, Displace, later rigs: rig is
  out of scope, D-017).
- UV: seams from marks and a basic unwrap, only when a task asks for it.

### Phase 5: the human points, the AI answers

- **Marks are messages.** Every sync lists the marks found since the last
  one (`sharp: v9-v8 ...`, `seam: v15-v27 v23-v27`) under `marks`, so none
  goes unseen. Proposed meanings, to confirm with the modeler: sharp or
  seam on a loop = "this loop" (remove, move, look), crease = "pinch here".
  Once acted on, the AI clears its marks and says so.
- **Annotations.** Strokes drawn with Blender's Annotate tool read as 3D
  points; the sync names the vertices under each stroke. A way to say
  "here" without selecting.
- **Human edits explained.** When the modeler moves vertices, the sync's
  deltas come with a guess of the intent (`L1 rim up 4%: the silhouette was
  low?`) that the AI asks about, as `models/FEEDBACK.md` describes.

## Part 2: learning from use

What would improve the modeling as the modeler uses the tool, and where each
piece goes.

1. **Numeric targets per task.** Each form in the shape map gets a measure
   and a target taken from the reference (waist ratio, section exponent,
   top profile, face count), written in the task's `target.md`. The AI
   stops when the numbers are in, and the modeler judges what numbers miss.
   Round 5 showed it works: the pinch went from "fraco" to the modeler's
   ratios in one pass once it was measured.
2. **A technique library.** Named techniques in each example's `EXAMPLE.md`,
   one block each: when to use it, how (in cage words), how to measure it,
   the source. Already there in draft: the pinch into the knot, the heart
   lobes, the 10-vertex round knot, the silhouette rim on the Y plane, the
   cage bigger than the result. `SKILL.md` would point to the index and read
   a technique only when the concept shows that form.
3. **Measures kept with each example** (`measures.json`, started for the
   bow tie): read instead of re-measured; each new example gets one when
   it is catalogued.
4. **Rule candidates with a count.** A list in `DECISIONS.md` of items seen
   once (Provisional) with the case that would promote them; at the end of
   a session the AI asks about the ones that got a second case. Today's
   candidates: the marks convention; "remove a loop that carries no shape,
   refit the volume" (D-045, second case); "a tight row next to a thin row
   keeps a pinch" (D-039, second case).
5. **Poly budget warning.** The task's target holds the reference's face
   count; the sync warns past it (for example 20% over). "Muito high poly"
   would have been caught before the modeler saw it.
6. **Editability measured.** `cage_dips` today; next, how even the cage's
   offset from the surface is, and pole count and placement against the
   reference's. The modeler's cage is the yardstick.
7. **A session brief file per run.** `ai/<run>/NEXT.md`: open items, files
   to read, measures to trust, what not to touch. Written at the end of
   each session, read first in the next: fewer tokens than re-reading the
   history, and the modeler can edit it.
8. **Cost per round.** Time and tokens in each `report.md` (still "not
   measured"), to see whether the tools actually make rounds cheaper.
9. **Transfer tests.** A new task (the hat, T2) run with and without the
   technique library, judged blind as in T1: do the rules carry to a part
   the AI has not seen?
10. **The modeler's edits as examples.** When the modeler fixes an AI cage
    in Blender, save the edit in `human/` (the README convention) and file
    the deltas with their why: each fix is a small example of a technique.

## Order

| Step | What | Why first |
|---|---|---|
| 1 | Phase 0 + `seam` in the selection grammar (**done**) | unlocks every other operator; the round-6 seams need it |
| 2 | Phase 2: pull with falloff, slide, smooth, to sphere | the next edits on B1 are shaping, not topology |
| 3 | Part 2 items 1, 5, 7 (targets, poly budget, session brief) | cheap, and each round gets cheaper |
| 4 | Phase 1 whitelist complete | covers the loop work of the next examples |
| 5 | Phase 5 marks report and annotations | the modeler's way of pointing, made reliable |
| 6 | Part 2 items 2, 4, 6 (technique library, candidates, editability) | turns B1's lessons into reusable knowledge |
| 7 | Phase 3 and a transfer test on a new task | when the bow tie is accepted |
