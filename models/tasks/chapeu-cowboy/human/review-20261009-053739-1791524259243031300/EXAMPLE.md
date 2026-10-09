# Human edit

A preserved correction with stable-id deltas and recorder receipts.

## Contents

- [Files](#files)
- [Why](#why)
- [Validation](#validation)

## Files

- `before.blend`: the saved AI file before the correction.
- `after.blend`: the human's saved review.
- `edit.json`: deltas in local mm, provenance, recorder summary.

## Why

The modeler (2026-10-09): "agora sim, tinha um problema nas normais na borda do chapéu, coloquei um mark sharp e agora estão certas"

After Solidify, the shading normals at the hat's border were wrong. The
modeler marked the brim's outer edge loop and the crown-brim fold loop sharp
(24 edges), which fixed them; Smooth by Angle was tried and removed. Here
sharp is a shading fix, not the 'this loop' signal of D-060.

## Validation

Recorded only. Replay and artistic approval are pending.
