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

## Round 3 (2026-09-29)

| # | Modeler said | AI understood | Class | Goes to |
|---|---|---|---|---|
| 9 | "A parte em formato de coração da asa do laço ainda está muito quadrada vista de cima com Subdivision" (item 8) | Measured: the top outline kept 81% of its depth at the tip (flat end); the reference falls to 38%. Matched the reference's top profile with `target` ops, no new loops. | Specific (heart, B1); second case of D-041 for "round from the top", pending the verdict | B1 `Laço`; D-041 evidence if accepted |
| 10 | "uma op `target` que resolve o cage para o sub cair num alvo" (idea from earlier sessions, in this session's brief) | `target <vid> <axis> <value>`: the sync solves the base so the sub lands there | Tool | Fofuxo Cage (done) |

## Round 4 (2026-09-29)

| # | Modeler said | AI understood | Class | Goes to |
|---|---|---|---|---|
| 11 | Labels: the leader in the vertex's color, no "v", neighbours in different colors, more space between numbers, leaders that do not cross | Done as asked, plus shared labels for coincident vertices and hollow dots for hidden ones | Tool | Fofuxo Cage render |
| 12 | "a solda por causa do modificador mirror é causada por uma opção do modificador ... da forma como eu faço é deixar um valor bem bem pequeno, pois eu quero que eles se conectem quando encosta no X0" | Merge distance very small (0.1 mm, as on the modeler's wing); set on both objects | Rule | D-054 |
| 13 | "queria que a extensão do blender bloqueasse a malha que você está editando, ou se precisar, bloqueasse a utilização do usuário no blender" | `lock(name, ui=False)`: object not selectable; `ui=True` swallows input; Esc or Unlock takes over | Tool | Fofuxo Cage (done) |
| 14 | "faça o nó ter 10 vertices (igual como eu fiz) e depois use o solidify [Subdivision: the modeler corrected the name] para dar a forma arredondada" | Knot rebuilt with the modeler's topology, Subdivision 1/2, fitted to the approved knot within 0.8 mm | Specific, test of D-053 from the other side | B1 `Laço Nó`; EXAMPLE open question |
| 15 | "o laço com formato de coração, também é bom você dar uma olhada e fazer uma auto crítica em relação ao seu" | Self-critique in `report.md`: same outline, worse layout (columns against radial loops), uneven cage | AI deduction, pending | `report.md`; EXAMPLE deductions |
| 16 | "as informações de configurações dos modificadores são muito importantes, você deve poder editá-las e compreender o resultado das mudanças na malha" | `modifiers` section with each modifier's settings and effect; `set` with units | Tool | Fofuxo Cage (done) |
| 17 | "é para você modelar no eixo -Y ... os vertices que importam estão na parte de trás do mirror" | Base mesh on -Y; `flip` and a warning | Rule | D-055 |

Proposed for `SKILL.md` (not yet written): "Mirror merge distance very small
(0.1 mm): vertices join only when they touch the plane" (D-054) and "Model
on -Y, the side the front view sees" (D-055).

## Round 5 (2026-09-29)

| # | Modeler said | AI understood | Class | Goes to |
|---|---|---|---|---|
| 18 | "a sua asa ainda está muito high poly se comparada com a minha. marquei um loop inteiro com sharp que você poderia remover e reajustar os vertices para conseguir o mesmo volume, ou até um volume melhor" | Loop dissolved (`dissolve sharp`), volume refitted: 22 vertices per 1/8 | Rule, second case of D-045 | D-045 evidence; B1 `Laço` |
| 19 | "está faltando um finco maior no meio da asa quando entra no nó ... veja como eu fiz e dê uma sugestão para si próprio de como escrever o que eu fiz com palavras" | The pinch measured as the waist of the cross-sections (0.28-0.32 of the lobe depth near the knot); built with a thin h 0 row and a tight row next to it. Words written in `EXAMPLE.md` | Specific (heart) + second case of D-039 | `EXAMPLE.md`; D-039 evidence |
| 20 | "você pode implementar todas as suas sugestões" | Done: topology ops, shape tools, views options, quiet reports, editability check, measures file, test verdict line | Tool | Fofuxo Cage |

Marking edges sharp in Blender worked as a way for the modeler to point at a
loop; the tool now reads it (`dissolve sharp`, `crease sharp ...`). Worth
keeping as the convention? (question D)

After round 5 (open, next session):

| # | Modeler said | AI understood | Class | Goes to |
|---|---|---|---|---|
| D | "pode ser loop ou seam como referência para você" | The modeler points at edges with sharp or seam marks; the tool should read seam as it reads sharp | Tool | Fofuxo Cage (`seam` keyword, to do) |
| 21 | "marquei com seam as edges que precisam ser puxadas para Y- para dar um formato mais arredondado. no geral o modelo está bom" | Seams on v15-v27 and v23-v27 (around v27, the lobe's outer side at 85% of the width): pull them toward -Y (deeper) for a rounder lobe | Specific | next session |
| 22 | "existem ferramentas no blender para fazer todas as edições que você está escrevendo scripts ... não valeria mais a pena você utilizar as do blender do que escrever scripts novos? em termos à longo prazo sobre performance" | Yes: wrap Blender's own operators (select by id, run the operator, read the result back) instead of writing new bmesh code per tool | Tool | Fofuxo Cage: generic operator op (to do) |
| 23 | "você, ao assumir o controle do blender, deveria sair do edit mode e bloquear o usuário de mexer" | `lock()` leaves Edit Mode (edits kept) and blocks input by default; the AI locks before editing | Tool | Fofuxo Cage (done) |

## Round 6 (2026-09-29): the modeler's edit of B1

| # | Modeler did / said | AI understood | Class | Goes to |
|---|---|---|---|---|
| 24 | Edited B1: "alterações no B1 para ficar igual ao concept (modelagem correta) tire suas próprias conclusões e anote para você conseguir entender e replicar em outra situação" | Edit saved to `human/B1-human-edit.blend`; lessons in `EXAMPLE.md` (loops end on silhouette turning points; four rim points at a heart's tip; fuller lobes; the knot wider) | AI deductions, pending | `EXAMPLE.md`, questions E-G |
| 25 | Re-added a loop after round 5 removed one, in another place | Placement, not count: a loop should end on the rim at a turning point of the outline | Provisional (first case) | `EXAMPLE.md`; DECISIONS if confirmed |

| # | Question | Modeler's answer | Class | Goes to |
|---|---|---|---|---|
| E | The edit is about 6% bigger than the concept's red silhouette, as E1 was. On purpose (and why), or the Image Empty's scale? | "não foi proposital, foi a forma que eu encontrei de chegar no formato que eu queria mais rápido. o concept é uma referência inicial, mas principalmente para concepts de objetos orgânicos, um desenho não bidimensional não vai conseguir ser traduzido fielmente para o 3D, pois o 2D funciona em um único ângulo, o 3D precisa funcionar em múltiplos ângulos." | Size: Coincidence. The concept as a starting reference: Rule | Coincidences; D-056 |
| F | The knot is 11% wider than round 5 and fuller at its front corners: read from the concept's knot, or to sit better on the wings? | "Ambos, eu identifiquei que no 3D, durante a sobreposição, estava um pedaço sendo cortado de uma forma que não se parecia com o concept, então para ajustar isso eu enlargueci o nó para esconder a junção das asas com ele." | Provisional (first case) | D-057; `EXAMPLE.md` |
| G | `cage_dips` flags v5 and v9 of the edited knot: a pinch on purpose at the knot's sides, or should the check leave round parts alone? | Misread as about the heart: "tentei deixar ele mais arredondado, antes às edges estavam muito juntas, isso é bom quando eu quero, usando o subdivision surface, deixar um canto menos arredondado. eu queria exatamente o oposto ... tive que aumentar o espaçamento". The knot's case is answered by F: v5 and v9 are the knot's side vertices that stayed while the front and back ones moved out, so the knot hugs the wings. | The heart answer: Rule (D-039, the other side). The check: Tool | D-039; `cage_dips` now says a dip may be on purpose |

Items 1 and 2 resolve through A and B: item 1 is D-051 applied to this
concept; item 2 is the heart shape of B. When to apply (from C) is settled by
item 6: case by case.
