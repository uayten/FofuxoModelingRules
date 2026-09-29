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
its budget (Part 2, items 1 and 5 of `ROADMAP.md`). Values from the concept
and from the modeler's E1 (`models/example/laco/measures.json`). The AI stops
when every line is in; the modeler judges what the numbers miss.

```targets
# object   measure              target   tolerance  why
Laço       faces                19       +20%       the modeler's wing: 19 quads per 1/8 (D-045, D-046)
Laço       verts                28       +20%       the modeler's wing
"Laço Nó"  faces                5        +20%       the modeler's knot, 10 vertices (D-051)
"Laço Nó"  verts                10       +20%       the modeler's knot
Laço       size w               124.4mm  6%         the concept's width; the modeler's is up to 6% bigger (D-056)
Laço       size h               65.7mm   6%         the concept's height
Laço       size d               28.9mm   15%        E1's depth; the concept shows none
Laço       section w 0.15 waist 0.32     0.06       the pinch into the knot (D-039; round 5 reached 0.28-0.32)
Laço       section w 0.3 waist  0.28     0.06       the pinch, farther out
Laço       section w 0.3 n      3.0      0.4        the section near the knot
Laço       section w 0.85 waist 0.88     0.08       a full outer lobe
Laço       section w 0.85 n     3.8      0.4        a boxy outer lobe
Laço       profile top 0.75     14.5mm   1.5mm      the lobe's half depth from the top
Laço       profile front 0.75   34.3mm   2mm        the lobe's half height from the front
"Laço Nó"  size w               29.7mm   12%        E1's knot; the modeler widened B1's by 11% (D-057)
```

Last check (2026-09-29): E1 15/15 in, B1 round 5 15/15 in, the modeler's B1
edit 10/15 in. The edit is fuller and wider than E1: which one the targets
should follow is question H in `ai/B1-opus-cage/feedback.md`.
