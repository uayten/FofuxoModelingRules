# Cowboy hat: recorded correction

An index of the human's middle-dent session in C1. The open hat remains in
`models/tasks/chapeu-cowboy/`; this entry does not mark it finished.

## Contents

- [Evidence](#evidence)
- [Observed method](#observed-method)
- [Reuse check](#reuse-check)

## Evidence

- [Handoff](../../tasks/chapeu-cowboy/HANDOFF.md): model state and the modeler's decisions.
- [Compact recorder receipt](../../tasks/chapeu-cowboy/ai/C1/recording-summary.json): 343 recorded operators,
  including 81 translations, 5 LoopTools Circle calls, 4 LoopTools Space calls,
  7 edge slides, 3 vertex slides and 3 undos.
- [Original recorder log](../../tasks/chapeu-cowboy/ai/C1/C1.cage/review.ops.jsonl): retained at its historical path.

This earlier log does not contain moved-id or region receipts. It cannot
establish per-operator displacements, Sculpt stroke radii or exact replay.
The extended recorder must be checked in a new real review.

## Observed method

D-074 to D-079 document the modeler's method and reasons: close with the
fewest faces, shape with small moves, tidy a ring before moving individual
vertices, use slides to stay on the surface, and undo an unhelpful step.
Do not extract an exact command sequence from the counts alone. Resolve the
stage's ring/region ids and read the corresponding operator help when replaying.

## Reuse check

Status: observed; replay pending. Before reuse, check that the part is an
organic dent with equivalent surrounding ridges, mirror planes and live
Subdivision; use the new region ids rather than the C1 ids. Compare cage
and result evenness and one cropped render with the modeler's correction.
The hat verdict and a second concept are still required to judge transfer.
