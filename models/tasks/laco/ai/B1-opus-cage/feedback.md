# B1 feedback

Filtered as in `models/FEEDBACK.md`. One row per item: the modeler's words,
what the AI understood, the class, and where it went. Reference for this
round: `../../human/Laço.blend` (the modeler's bow, same as E1).

## Round 1 (2026-09-29)

| # | Modeler said | AI understood | Class | Goes to |
|---|---|---|---|---|
| 1 | "na vista lateral o nó está muito quadrado. compare com a vista lateral do meu modelo" | Measured: the knot's cross-sections fit a superellipse of exponent 4.3–4.6 (boxy); the reference's fit 2.5. Fixed: knot fitted to n 2.5 at the reference's proportions. | Rule, second case of D-041 ("round looks round") | D-041 evidence (proposed); metric pending question A |
| 2 | "o meu modelo é mais arredondado quando visto de perspectiva" | Measured: the difference is mostly the knot (item 1). The wings are not less round in section (reference 3.5–4.0, B1 2.9–3.0); they differ in shape: two lobes joined by a thin groove at mid height and a deep dent at the tip (a heart), which B1 lacked. Partly fixed with ops. | Specific, pending question B | `models/example/laco/EXAMPLE.md` |
| 3 | "a identificação dos vertices fique mais distantes do modelo; ... linhas ... maiores" | Labels go off the model with long leader lines. | Tool | Fofuxo Cage render (done) |
| 4 | "possibilidade de pedir vistas de ângulos diferentes ... 45º ... laterais superiores ou inferiores" | `views(name, [(yaw, pitch), ...])`. | Tool | Fofuxo Cage (done) |
| 5 | "pode incluir para você utilizar os modificadores" | Read as: the AI may change modifier settings and crease through the text (`set`, `crease` ops). Used for `crease plane-x 1.0` and `render_levels 2`. | Pending question C | D-048 scope (proposed) |

## AI deductions from the reference (pending)

| Deduction | Evidence |
|---|---|
| The horizontal fold (D-036) is built in the cage as a thin middle row: the wing is only 1.5 mm deep at h 0 near the knot | reference cage `v3` (-29.1, -1.5, 0) mm |
| The tip dent is deeper than the concept's silhouette shows (about 9% in the cage, 5% after Subdivision) | reference `v0` 61.6 mm against `v4` 67.6 mm |
| Round parts use few cage vertices: the knot is 10 vertices per 1/8, and fewer vertices under Subdivision give a rounder form (D-045) | reference knot 10 vertices, B1 knot 19 |

## Questions and answers

| # | Question | Modeler's answer | Class | Goes to |
|---|---|---|---|---|
| A | Knots and pillows round like an ellipse (exponent ~2.5): general rule? | "Isso depende mais do concept, mas parte da avaliação é: um asset para jogo = precisa ser low poly. um asset estilizado = pode existir abstrações que não existe na mesma peça da vida real." | Rule (the general part); the exponent is Specific | D-051; `models/example/laco/EXAMPLE.md` |
| B | The heart-shaped wing: always, or this concept? | "é só desse conceito, mas em uma quantidade considerável de desenhos os laços são em formato de coração. Na vida real eles não são assim." | Specific, with a reading hint for concepts | `models/example/laco/EXAMPLE.md` |
| C | Modifiers: settings only, or add and remove too? | "A AI precisa adicionar, remover, editar, mudar a ordem e em casos específicos aplicar o modificador." | Rule | D-052; Fofuxo Cage ops `add`, `remove`, `reorder`, `apply` |

## Round 2 (2026-09-29)

| # | Modeler said | AI understood | Class | Goes to |
|---|---|---|---|---|
| 6 | "você vai ter que fazer a decisão de quando aplicar um modificador conforme seu entendimento de modelagem aumenta ... cada caso é um caso" | No rule for applying; AI judgment, reported | Rule | D-052 |
| 7 | "o nó do laço ficou muito muito muito melhor, está ótimo! ... deixaria sem modificador de subdivision ... para precisar utilizar o modificador ele teria que ser mais low poly" | Knot accepted; Subdivision removed (`remove Subdivision`) | Rule | D-053; B1 `Laço Nó` |
| 8 | The heart-shaped part of the wing is still too square from the top with Subdivision | Open work | Specific | next session |

Items 1 and 2 resolve through A and B: item 1 is D-051 applied to this
concept; item 2 is the heart shape of B. When to apply (from C) is settled by
item 6: case by case.
