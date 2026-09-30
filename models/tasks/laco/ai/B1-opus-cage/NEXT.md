# B1: next session

Written 2026-09-29, after round 6 (the modeler's edit) and the Fofuxo Cage
work of ROADMAP steps 1 to 3. Read this first; the modeler may edit it.

## Open items

- **21**: the seams v15-v27, v23-v32, v27-v32 of the modeler's edit, pulled
  toward -Y for a rounder lobe. Tried on a copy only
  (`mesh translate seam d=+3% falloff=smooth radius=25%`: section at w 850,
  d 837 to 875 with `shrink_fatten`, 837 to 852 with `translate`). How much
  is the modeler's call.
- **24, 25**: the AI's deductions from the edit (EXAMPLE.md, "What the
  modeler's edit of B1 teaches"), Provisional until confirmed.
- Which file the next round starts from: the round-5 `B1.blend` or the
  modeler's `human/B1-human-edit.blend` (called "modelagem correta").

## Read first

- this file;
- `feedback.md`: the tables of rounds 5 and 6 only;
- `models/example/laco/EXAMPLE.md`: "What the modeler's edit of B1 teaches";
- `models/tasks/laco/target.md`: "Numeric targets";
- `extension/fofuxo_cage/README.md`: "Two Blenders" and "Mesh op".

## Measures to trust

- `models/example/laco/measures.json` (E1).
- `check_targets()` on 2026-09-29, targets from the modeler's edit (D-059):
  the edit 15/15 in; round 5 10/15 (out: width, depth, top and front
  profiles at 0.75, knot width); E1 11/15.
- Marks read as D-060: sharp or seam on a loop = "this loop", crease =
  "pinch here".

## Do not touch

- `B1.blend` (round 5), `models/tasks/laco/human/`, `models/example/`: work
  on a copy.

## Start

```bash
python extension/fofuxo_cage/launcher.py <copy of the chosen file>
```

then `fofuxo_cage.instance()` (role `ai`), `sync("Laço")`,
`check_targets()`; show the modeler with `review()`, read back with
`absorb()`.
