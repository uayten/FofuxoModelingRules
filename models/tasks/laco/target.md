# Target: bow tie

## From the concept

Measured on the red mask of `EUA-Frente.png` at the Image Empty scale of
`start.blend` (0.638 mm per pixel):

| | mm | px |
|---|---|---|
| Width | 124.4 | 195 (x 528–722) |
| Height | 65.7 | 103 (y 705–807) |

The concept shows no depth. The requested width (about 13.5 cm) and the
concept disagree; the concept wins, with tolerance (D-038).

## Forms to reach

From the modeler's reading in T1 (D-036, D-037, D-041):

- a dent in the middle of each wing's outer edge;
- a fold where each wing enters the knot;
- wings that narrow almost to a point behind the knot, crossing like an X;
- from the top, a figure eight: the wings converge to the center in depth.

## Reference

`models/example/laco/human/Laço.blend` (E1): 126.1 × 28.1 × 68.4 mm evaluated.

## Numeric targets

Read by `fofuxo_cage.check_targets()`; the sync warns when a count passes
its budget (Part 2, items 1 and 5 of `ROADMAP.md`). Values from the
modeler's latest edit, `human/B1-human-edit.blend` (D-059: "a última versão
que eu editei é a principal"). The concept is a first direction, not the
final mesh (D-056): its sizes are given in the why. The AI stops when every
line is in; the modeler judges what the numbers miss.

```targets
# object   measure              target   tolerance  why
Laço       faces                19       +20%       the modeler's wing: 19 quads per 1/8 (D-045, D-046)
Laço       verts                28       +20%       the modeler's wing
"Laço Nó"  faces                5        +20%       the modeler's knot, 10 vertices (D-051)
"Laço Nó"  verts                10       +20%       the modeler's knot
Laço       size w               131.3mm  5%         the modeler's width; the concept's is 124.4 mm (D-056)
Laço       size h               69.8mm   5%         the modeler's height; the concept's is 65.7 mm
Laço       size d               33.7mm   10%        the modeler's depth; the concept shows none
Laço       section w 0.15 waist 0.36     0.06       the pinch into the knot (D-039)
Laço       section w 0.3 waist  0.37     0.06       the pinch, farther out
Laço       section w 0.3 n      3.15     0.4        the section near the knot
Laço       section w 0.85 waist 0.9      0.08       a full outer lobe
Laço       section w 0.85 n     3.6      0.4        the outer lobe, rounder than E1's (3.8)
Laço       profile top 0.75     16.7mm   1.5mm      the lobe's half depth from the top: fuller than E1 (14.5)
Laço       profile front 0.75   34.9mm   2mm        the lobe's half height from the front
"Laço Nó"  size w               34.7mm   8%         the knot widened to hide the junction (D-057)
```

Last check (2026-09-29): the modeler's B1 edit 15/15 in; B1 round 5 10/15
(out: width 123.6 mm, depth 28.8 mm, top profile at 0.75 14.4 mm, front
profile 32.6 mm, knot 31.3 mm: what the modeler changed); E1 11/15.
