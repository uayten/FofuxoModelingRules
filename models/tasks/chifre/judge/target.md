# Target: horns (hidden from the runs)

Kept in `judge/` so that `fofuxo_cage.check_targets()` does not find it from
a run's folder (it walks up from the `.blend`); the judge passes the path:
`check_targets(path="models/tasks/chifre/judge/target.md")`. A run's horn
object is renamed `Chifre` before the check if it has another name (D-004
asks for `Chifres`; E1 has `Chifre`).

## The modeler's part

`Chifre` in E1 (`models/example/laco/human/Laço.blend`): a cube extruded
with its loops rotated along the curve, no mirror of its own; Mirror X
across `Dragão Corpo` makes the pair, then Subdivision 1/2. 57 vertices,
52 quads, one open border where it enters the head. Material `Dragão Base`.

## From the concept

The cream mask of the horn on the viewer's right, with the concept behind the
body as in `start.blend` (0.607 mm per pixel, centred on x 0): tip at about
w 115, h 595 mm; the outer edge reaches w 155 at h 530–538; visible down to
h 483 (the head hides the rest); the inner side is partly behind the hat.
The concept's tip is about 28 mm higher than E1's: the concept is a first
direction, not the final mesh (D-056).

## Numeric targets

One horn, Mirror off, world mm (w d h = x y z, front is -y). `base` is the
middle of the open border, `tip` the point farthest from it.

```targets
# object  measure        target    tolerance  why
Chifre    faces          52        +20%       the modeler's horn (poly budget)
Chifre    verts          57        +20%       the modeler's horn
Chifre    world size w   88.6mm    10%        one horn's width
Chifre    world size d   91.0mm    10%        one horn's depth
Chifre    world size h   124.3mm   10%        one horn's height, the buried part included
Chifre    base w         88.4mm    10mm       where it sits on the head
Chifre    base d         -74.0mm   10mm       where it sits on the head
Chifre    base h         472.6mm   10mm       where it sits on the head
Chifre    tip w          117.5mm   8mm        where the curve ends; the concept's is about 115
Chifre    tip d          -74.0mm   8mm        the tip over the base, seen from the side
Chifre    tip h          567.2mm   8mm        the horn's height; the concept's is about 595
```

Besides the numbers: `editability(<run's horn>, ref="Chifre",
blend="models/example/laco/human/Laço.blend")` (offset, poles, dips against
the modeler's cage), and the modeler's blind verdict.
