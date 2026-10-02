# Decisions

Every rule in `skill/fofuxo-modeling-rules/SKILL.md` comes from here. Each entry says what the rule is, why
(in the modeler's words when possible), and which example it came from.

Status:

- **Stated**: the modeler stated it as a general practice.
- **Provisional**: inferred from a single example; confirm with another.
- **Open**: question still pending.

Examples:

- **E1**: `models/example/laco/human/Laço.blend`, dragon + "Roupa Estadunidense" outfit. Focus: the bow tie
  (`Laço`, `Laço Nó`).

Tests:

- **T1**: `models/tasks/laco/ai/`, bow tie modeled by Sonnet with and without the
  skill, judged blind.
- **B1**: `models/tasks/laco/ai/B1-opus-cage/`, Opus reshapes run A2 with
  LLM Modeling Bridge; judged by the modeler against his bow (`models/tasks/laco/human/`,
  the E1 bow). E1 may be used for decisions; what is ambiguous is asked.

---

## Naming

### D-001: Naming language follows the user (Stated, E1)

Names use the user's language. Where to find it, in order:

1. objects already renamed in the scene;
2. Blender's language, if nothing is renamed yet.

Blender's language means `preferences.view.language`, even with "Translate
Interface" off (E1: `pt_BR`, UI in English → Portuguese).

### D-002: Object name is the part alone (Stated, E1)

`Laço`, `Chapéu`, `Presa`. Prefixing with the asset name depends on the project:
a game that builds its assets across many `.blend` files may need it.
Project context (prefixes, shared materials, target): the AI asks the user. If
the project spans several `.blend` files, the AI suggests creating a project
context file in Markdown so the answers are not repeated every task.

### D-003: Parent groups parts that move together (Stated, E1)

Complex objects are split into smaller, simpler objects. They stay together
through a parent instead of a merge: the parent moves all of them and they keep
their relative position. Example: `Laço Nó` is a child of `Laço`.
Child naming: a descriptive name (`Laço Nó`; `Asas 2` should have been
`Asa Membrana`, the number was a missing name). Numbering is acceptable when
there are many complex technical names.

### D-004: Plural when the object shows more than one unit (Stated, E1, T1)

A Mirror pair (left and right wings: `Asas`) or an Array (`Estrelas`) makes the
name plural. By this rule `Chifre` should be `Chifres`: the inconsistency in E1
is human, not a rule. The count is of the thing the name describes: a bow with
two loops is one bow (`Laço`), confirmed in T1.

### D-005: Mesh data named after the object (Stated as good practice, E1)

Humans rarely do it, but it is good organization, and it becomes necessary with
linked duplicates (Alt+D) or when appending the mesh into another `.blend`.
For the AI it costs nothing, so the AI always does it.

### D-006: Modifiers keep their default names (Stated, E1)

Humans do not rename modifiers. The exception is leftovers: parenting a mesh that
already has an Armature modifier to another armature creates `Armature.001`.
Remove the unused one and rename the remaining one to `Armature`.
Disabled modifiers may stay on purpose (E1: the Shrinkwraps on `Fita Azul`).

### D-007: Sub-collection for 3+ related, unparented objects (Stated, E1)

`Olhos` exists because it holds 3+ objects of the same section that are not
parented to each other.

### D-008: Material names depend on reuse across the project (Stated, E1)

- Materials reused by many assets in the engine have generic names (E1:
  `Azul`, `Branco`, `Vermelho`, reused across the dragons in Unity).
- Materials exclusive to one asset (own texture) carry the asset's name (E1:
  `Dragão Base`). Another project could use `Tracer_Corpo`, `Tracer_Rosto`.

This is a project decision that goes beyond one `.blend`.

---

## Construction

### D-009: Mirror on every axis the shape is symmetric in (Stated, E1)

The bow is symmetric (or very close) in X, Y and Z, so only 1/8 is modeled.
The knot is a box with Subdivision to round it; the Mirror avoids doing the same
work several times on an object that is identical on many sides.

### D-010: The concept in the scene is the reference (Stated, E1)

E1 has an Image Empty `Concept` (`EUA-Frente.png`). Visual choices follow the
concept.

### D-011: Split into separate objects for editability (Stated, E1)

The knot is a separate object even with the same material and pivot. Separate
objects get their own origin and base shape, their own modifiers, and their own
tools (Sculpt Mode, Proportional Editing Objects) without touching the other
part. This is the human standard for building assets.

### D-012: Closed volume vs. sheet + Solidify is an artistic choice (Stated, E1)

Both are correct; the visual result against the concept decides.

### D-013: Prefer extruding the faces that need thickness over Solidify (Stated, E1)

Solidify blocks a Bevel on a single edge loop, so humans often apply it. The AI
may apply Solidify at specific steps when needed, but usually the better path is
to extrude only the faces that need thickness.

### D-014: Model world-aligned, pose with the object rotation (Stated, E1)

Build the mesh in the orientation that is straightest and easiest to model
(for the bow: symmetry axes aligned with the world). When it is done, rotate the
object to match the model/concept. Rotation is not applied (E1: `Laço` at −6° X).
To re-edit, make an Alt+D copy (shared mesh data) with rotation reset: edit
there, world-aligned, while watching the result on the posed copy.

### D-015: Subdivision density must be coherent across the model (Stated, E1)

Only Levels Viewport matters. The level depends on the target: animation takes
more levels, a game must match what will be exported to the engine. Humans check
by zooming out with wireframe on and looking for parts whose density is out of
proportion. Exceptions follow the detail: a dress with many folds may need a bit
more than the body; a tiny accessory can be a textured plane.
Proposed: the auditor flags density outliers (faces per area vs. the rest of the
model).

### D-016: Localized Bevel goes after Subdivision (Stated, E1)

`Chapéu`: Bevel limited by Weight, after Subdivision. Before it, Subdivision
would double the segments (5 set → 10 out).

### D-020: Loose geometry is a modeling error (Stated, E1)

`Laço` had 5 loose edges (6 vertices), a mirrored copy of the creased center
edges. They should not exist. Fix: Mesh > Clean Up > Delete Loose.

### D-021: Crease holds the silhouette where Subdivision would pull it (Stated, E1)

`Laço`: crease 1.0 on the center edges where the wing enters the knot. With
a sparser cage, Subdivision pulled the wing beyond the knot and broke the match
with the concept. With the current cage it no longer shows, but it stays: it is
harmless and keeps the shape "entering" the knot if loops are removed from the
middle of the wing. A leftover crease that does not change the form is fine.

### D-022: Openings in game meshes are closed simply (Stated, E1)

Where a body part passes through (sleeve, pants, boots, shirt), the opening is
closed with extrude → scale inward → Merge at Center. The single center vertex
is then pushed inside the sleeve/limb.
With Subdivision, do not merge: Merge at Center makes a fan of triangles (see
D-023). E1 `Laço`: the wing end is squeezed to ~1 mm inside the knot, not merged,
so it stays all quads.

### D-023: No triangles under Subdivision (Stated, E1)

Subdivision turns triangles into bad normals and changes how shading renders
around them. On any mesh with Subdivision, the ideal is zero triangles.

### D-024: Model one unit, repeat with Array (Stated, E1)

`Estrelas`: a single star with the ideal modeling, then an Array (Geometry
Nodes). One object is easier to edit and to isolate with `/` than ten copies in a
circular array that move the mesh around.

### D-025: Thin parts get a small volume in games (Stated, E1)

`Asas 2` / `Orelhas 2`: a small Solidify so the cartilage is not a flat plane.
No volume is common in games, but engines render one side of the face by
default; a flat plane would need a double-sided material. Visual choice here: a
small volume looks better.

### D-026: Shrinkwrap is a general fitting tool (Stated, E1)

Uses: place a Lattice on a mesh, dress clothes over a character's body,
retopology, align objects on top of others. Its options (wrap method, vertex
group, offset) make each use a different setup.

E1 `Fita Azul` (align on top of another object): the hat was resized and the
ribbon no longer fit. Two Shrinkwraps, each limited to a vertex group (one ring
of 14 vertices each):

- `1.003`: Nearest Surface Point, group `Shrwink2`, keeps the ring on the hat's
  surface (for when the top face of the hat changes size: more pyramid, inverted
  pyramid, more cylindrical);
- `2.003`: Nearest Vertex, group `ShrinkWrap`, snaps the ring onto the hat's
  vertices (the ribbon's base vertices were extracted from the hat, see D-029).

Both are disabled: the fit already happened, and they stay as a backup to redo
it if the hat changes again (see D-006: disabled modifiers may be intentional).

### D-027: On thin strips, the Bevel rounds the rim, not Subdivision (Stated, E1)

`Fita Azul`: Subdivision → Solidify → Bevel (Weight). Subdivision works poorly on
long rectangular faces. Subdivision over the thickness would round the rim, but
it pulls the rounding toward the center of the mesh and fights the distance
between the top and bottom faces. The Bevel after Solidify does the rounding.

### D-030: Subdivision position: animation logic vs. modeling logic (Stated, E1)

Animation logic puts Subdivision last. Modeling logic puts it where the final
form needs it (E1 `Fita Azul`, `Chapéu`: before Solidify/Bevel). When the order
changes nothing in the result, either is fine (E1 `Asas 2`: Solidify before
Mirror, indifferent).

### D-031: Check density with Optimal Display off (Stated, E1)

Subdivision's "Optimal Display" hides the subdivided edges. To judge quad
density in wireframe, turn it off.

### D-028: Boolean is for hard-surface (Stated, E1)

Windows, doors, shelves, straight props. Rarely used in organic character
modeling. Its slot in the stack waits for a hard-surface example.

### D-029: A part that sits on another starts from its faces (Stated, E1)

`Fita Azul`: the base vertices of the ribbon were extracted from the hat, so the
ribbon starts matching the surface it sits on.

---

### D-032: Shape comes first (Stated, T1)

Matching the concept's shape is "very, very, very important". In T1 the run
without rules got the shape right and was judged better, even with no
modifiers.

### D-033: The cage carries the silhouette, Subdivision only smooths (Stated, T1)

Replaces the first-draft rule "minimal base shape, detail comes from
modifiers". In T1 a 7-vertex cage with Subdivision 2 lost the bow's shape, and
the dense wireframe looked "threatening" for no reason. Fewer visible vertices
feels easier to edit, though a mesh that already has modifiers is easier to edit
in the end. Small accessories: Subdivision level 1.

### D-034: A symmetric baked mesh gets cut and mirrored (Stated, T1)

On T1's run without rules (right shape, no modifiers), the modeler would cut
the mesh in half and add a Mirror "with 100% certainty".

### D-035: No ground rule; move the concept, not the model (Stated, T1)

The draft rule "rests on Z = 0" put T1's first bow on the floor. It is dropped:
the mesh origin is not tied to the ground. The AI models world-aligned (D-014)
and may move, rotate and scale the concept's Image Empty until it sits in a
good position to read against the model (e.g. an asymmetric or tilted
concept).

### D-036: The concept's shading shows forms that need loops (Stated, T1)

The T1 run A2 matched the outer silhouette but missed what the shading shows: a
dent in the middle of each wing's outer edge, and a fold where each wing enters
the knot. The modeler would add loops for both.

### D-037: Imagine what the concept hides (Stated, T1)

"It takes some imagination to understand the concept beyond what is strictly in
the image." The bow's wing contours keep converging behind the knot, crossing
like an X: each wing narrows almost to a point at the center. E1's bow follows
this; A2 could not infer it.

### D-038: Concept size wins, with tolerance (Stated, T1)

When a requested size and the concept disagree, the concept is worth more, "not
set in stone".

### D-039: Tight loops keep sharp turns after Subdivision (Stated, T1)

E1's center vertices are packed close together so the wing keeps its narrowing
into the knot after Subdivision. A2 had loose spacing and drifted "out of shape,
mainly after the Subdivision".

B1 round 5 (second case): the pinch where the wing enters the knot ("um finco
maior no meio da asa quando entra no nó") needs the row next to the thin h 0
row to sit close to it; with evenly spaced rows the waist stayed at 0.44-0.55
of the lobe depth, with the tight row it reached the modeler's 0.29-0.32.

The other side (Stated, B1 round 6): spacing sets how round a turn comes out
under Subdivision. Edges close together keep a corner less rounded; to make
the heart's lobes rounder the modeler spread them apart: "antes as edges
estavam muito juntas, isso é bom quando eu quero, usando o subdivision
surface, deixar um canto menos arredondado. eu queria exatamente o oposto
... então tive que aumentar o espaçamento".

### D-041: Imagine the views the concept does not show; round looks round (Stated, T1)

Seen from the top, E1's bow wing converges to the center in depth as well (a
figure eight). A2 from the top is "a somewhat square bone". The model must
imagine how a form that looks round in the image gets round in every view.

### D-042: Validate each object alone, then all together (Stated, T1)

Suggested by the modeler after A2: judge each object on its own first, and the
set last.

### D-043: Deliver an honest, editable base (Stated, T1)

Inner shading forms stay hard for models. The delivery is the best shape the AI
reached, with a live stack, plus a shape map: each form from "Read the concept"
marked done, partial or not done, and where it lives. The human knows where to
finish; the AI never reports a shape as done when it is not.

### D-044: Measure from the evaluated vertices (Verified, T1)

With GPU Subdivision on (the default here), `obj.dimensions` and `bound_box`
measure the cage, not the subdivided surface. Found by run A3 and verified:
run A's bow measured 14.0 × 10.0 cm by `obj.dimensions` and 13.5 × 7.1 cm by
evaluated vertices. The earlier T1 claim that runs A and A2 misreported their
sizes was wrong: their reports were right, the check was not.

### D-045: Too many loops cost more than too few (Stated, T1)

A3 (Opus) was the best result untouched, but as a start for manual editing A2
was better: fixing A2 meant dragging vertices; fixing A3 meant cleaning excess
loops and then dragging vertices anyway. Start lean.

B1 round 5: the wing was "muito high poly" next to the modeler's. The modeler
marked a whole loop to remove and reshape "para conseguir o mesmo volume, ou
até um volume melhor": 29 → 22 vertices per 1/8, the surface refitted within
0.3 mm of the round before.

### D-046: The face budget mixes reference detail, overall shape and target (Stated, T1)

No fixed number. The overall shape comes fast (the part the models reached);
the inner fold that makes the shadow took the modeler the longest, and is the
part no model reached (Opus scratched it).

### D-047: AI-edited cages stay under 255 vertices (Stated, T1)

The modeler's proposal for the next step: a cage small enough to edit without
rewriting a whole Python script. Humans judge the cage and the subdivided
result side by side, so the AI must see both.

### D-048: The vertex-editing format is a separate project (Stated, T1)

A text format the AI edits to place cage vertices, with a round trip: the AI
writes, a plugin turns the text into mesh and render automatically, the AI
reads the render and writes again; it may give up and say so; a human edits
the vertices in Blender; the AI reads the result back and continues from the
human's state. This skill will use that tool once it exists. Candidates
discussed: section table with named forms (proposed), per-view pixel images
(rejected as a write format: LLMs read pixel coordinates poorly, views do not
link, no topology).

### D-049: Cage text v1: vertices by id, grouped by loops (Provisional, T1)

E1's `Laço` cage, measured: one patch of 28 vertices per 1/8, three corners on
the mirror planes, one valence-3 pole; its Y-plane boundary is the front
silhouette. A section table could not read that cage back, so the format
stores vertices by stable id, groups them by edge loops for reading, shows
where each vertex lands after Subdivision (under Mirror > Subdivision, base
vertex i is evaluated vertex i: verified exactly), and changes topology only
through ops. The modeler approved it as a first option that may not be the
best: only use will tell. Tool: `extension/fofuxo-bridge/`.

### D-050: Cage values in permille of a fixed frame (Provisional, T1)

The modeler's proposal: read vertices as fractions of the object's size ("at
50% of the height") instead of positions, since the AI reads the concept in
proportions. Refined together: the frame is a fixed box (the concept's size,
or the evaluated result at the first sync), not the mesh's own bounding box,
which would shift every value when one extreme vertex moves. Mirrored axes
count from the plane with no sign; values are whole permille (1‰ ≈ 0.06 mm
on the bow tie's width); axes are named w, d, h. Only mm stays in the size
line. Concept bow tie on E1: 118.4 × 62.5 mm at the Image Empty's scale.

### D-051: Stylized game assets: low poly, and abstraction is allowed (Stated, B1)

Asked whether a knot must be as round as the reference's (superellipse
exponent 2.5 against B1's 4.3–4.6): "it depends more on the concept", but
part of the judgment is always: a game asset must be low poly; a stylized
asset may carry abstractions that the same object does not have in real life.
So roundness and shape follow the concept's stylization, not the real object.

### D-052: The AI manages the modifier stack; applying is for specific cases (Stated, B1)

The AI may add, remove, edit and reorder modifiers, and apply one in specific
cases. Widens D-048, whose tool touched mesh data only. LLM Modeling Bridge does it
through ops in the mesh text (`add`, `remove`, `reorder`, `set`, `apply`,
`crease`). When to apply has no rule: "cada caso é um caso". The AI decides
from its own modeling judgment as it grows, and reports every apply.

### D-053: Subdivision only for a cage that needs it (Stated, B1)

The B1 knot (19 vertices per 1/8, fitted round) was judged "muito muito muito
melhor": the modeler would change nothing but drop its Subdivision, since the
cage already holds the form; "para precisar utilizar o modificador ele teria
que ser mais low poly". A cage dense enough to carry its shape goes without
Subdivision; Subdivision is for a lower-poly cage (D-033, D-051).

### D-054: Mirror merge distance very small (Stated, B1)

The weld at a mirror plane comes from the Mirror modifier's merge option. The
modeler keeps its distance "bem bem pequeno", so vertices join only when they
touch the plane (X = 0), never because they came close to it. E1's `Laço`
uses 0.1 mm. In B1 a merge of 1 mm (Blender's default) welded a wing vertex
that the AI had moved 1 mm off the plane. Clipping stays on, so vertices on
the plane stay there while editing.

### D-055: Model on the -Y side (Stated, B1)

With Mirror on Y, the half that holds the base vertices is -Y, the side the
front view looks at. B1 had its base on +Y, so in every render the vertices
that matter sat behind their mirror copy, "ficando uma malha na frente dos
vertices importantes". E1 models on -Y. LLM Modeling Bridge warns `modeled_behind`
and moves a part across with `flip(name, "d")`.

### D-056: The concept is a starting reference; the 3D must work from every angle (Stated, B1)

"O concept é uma referência inicial, mas principalmente para concepts de
objetos orgânicos, um desenho não bidimensional não vai conseguir ser
traduzido fielmente para o 3D, pois o 2D funciona em um único ângulo, o 3D
precisa funcionar em múltiplos ângulos." Seen in B1: round 5 matched the
concept's front silhouette better than the modeler's edit (overlap 0.917
against 0.893) and was still the wrong shape. The concept sets the
proportions and the turning points of the outline; the forms are judged from
several angles (D-041). Refines D-032 and D-038: matching the concept stays
first, as a read of the drawing, not a stencil of its outline.

### D-057: A covering part hides the junction it makes with another (Provisional, B1)

The modeler widened B1's knot 11% because, seen in 3D, the wings cut into it
in a way that did not look like the concept: "eu enlargueci o nó para
esconder a junção das asas com ele". The knot's sides stay in where the wings
pass, so it hugs them. Seen once; ask whether it holds for other covering
parts (belts, buttons, ribbons).

### D-058: The AI works in a Blender of its own; the human reviews in another (Stated, B1)

The modeler: open the AI's Blender as a black screen that says it is for the
AI's exclusive use, even when the human already has a Blender open; when the
human should see or change the model, open a normal Blender with the model
appended. The AI is then in charge of its own file alone, and of saving and
reading the human's changes. In LLM Modeling Bridge: `launcher.py` (the AI's
instance, MCP port 9876), `review()` and `absorb()` (the human's copy and its
way back), and a human's Blender stops its own MCP server while the AI's
instance runs. Replaces locking the human's Blender (`lock`) for the AI's
normal work.

### D-059: The modeler's latest edit is the reference (Stated, B1)

"A última versão que eu editei é a principal, é bom tirar as regras de lá.
Mas no final o concept é um direcionamento inicial, não a malha final."
When the modeler has edited a task's model, that edit wins over the older
example (E1) for the task's numeric targets and for the rules drawn from it;
the concept stays a first direction (D-056). The bow tie's targets now come
from `human/B1-human-edit.blend` (question H).

### D-061: Cylinders are modeled whole: extrudes and loops around (Stated)

The modeler, on a top hat the AI built from a quarter cylinder with Mirror:
"eu não cortaria a cartola e colocaria mirror, mesmo sendo tentador de fazer
isso. a melhor forma de editar cilindros é fazendo extrudes e cortar loops em
volta do cilindro." An exception to D-009 for cylinders. What went wrong
there: an inset on the quarter cap put extra vertices off the circle (v30
and v32, 5 degrees from their neighbours), a lumpy top under Subdivision. In
LLM Modeling Bridge, `start_part` keeps a cylinder whole; loops go around it with
`bisect` or `loopcut_slide`.

A cylinder's cap, the modeler's way: delete the whole top but its outer
loop; extrude the loop, scale it (S, then Shift+Z: X and Y only) toward the
center; Grid Fill the new inner loop. The cap is a ring of quads around a
grid of quads (`mesh delete faces h>999`, `mesh extrude_scale h>999 w=80%
d=80%`, `mesh fill_grid border`).

### D-062: A grid fill lines up with the X and Y extremes (Stated)

"Quando você aplicar o grid fill, você precisa rotacionar ele para ficar
alinhado com os vértices extremos do eixo X e os vértices extremos do eixo
Y. Imagine que você fosse aplicar um mirror, como a malha deveria ficar para
ser possível você cortar e utilizar 1/4 do modelo 3D para ser recriado com
mirror." A good practice even where it changes nothing in the result: the
grid's lines run through the loop's extreme vertices, so the mesh can be cut
in quarters and mirrored. LLM Modeling Bridge's `fill_grid` turns the grid until it
is mirror symmetric on X and Y (unless an offset is given).

### D-063: A part that sits on a body in the file is built on that body, not over the concept (Stated, T2)

The modeler, judging the T2 horns: "ambos estão muito ruins, o claude tentou
fazer por cima da referência sem levar em consideração o corpo do
dragãozinho que já existe no arquivo." Both runs traced the concept's horns
(tips at z 599 mm), noticed that the body's head is about 30 mm lower than
the concept's where the horns sit, and still kept the concept's outline,
stretching the base down into the head. The modeler's horn (E1) sits on the
real head: its tip is at 567 mm, the concept's 599 moved down by that same
gap, with a wide base on the head (89 × 91 mm against the runs' 50 × 49 and
76 × 60) and no backward sweep.

How to apply: when the scene already has the body a part sits on, the body
is the reference for place and size; the concept gives the part's shape and
its proportions against the body (height against the head, width against
the head, where on the head). Read the concept's head, find the body's, and
carry the part over from one to the other. When the two disagree, the body
wins and the part moves with it. Refines D-056 (the concept is a first
direction) and D-035 (move the concept to read it against the model).

### D-064: Read the drawing for what the 3D needs, not for what it shows (Stated, T2)

The modeler, judging the second pair of T2 horns: "ainda está fino na base,
a AI não está sabendo interpretar o concept no sentido do que funciona ou não
funciona na tradução do 2D para o 3D." Measured outside the head, in 15 mm
bands: E1's horn leaves the head with a base of about 80 × 80 mm (w 59-80,
d 75-79) and narrows fast to 25 × 25 at the tip, a cone; T2-D's leaves at
42-64 × 49-51 and keeps about 65 × 50 up to its top third, a tube. The run
took the width the front view shows and set the depth a little under it; the
hat's brim hides the base's inner side (E1 reaches x 69 behind it, the run
stopped at 89), and a front view shows no depth at all.

How to apply (the AI's reading of this case, confirmed by the modeler): the drawn outline is
what is left visible, not the part's size. Where something covers the part
(the brim, the head), it continues at least as wide as its widest visible
row; where the part meets a round body, its base footprint is as deep as it
is wide or deeper, so that it reads as growing out of the body from every
side; and a horn tapers as a cone from that base, not as a tube that narrows
only near the tip. Refines D-037 (hidden forms) and D-056.

### D-065: A written plan comes before modeling (Stated, T2)

The modeler, after the T2 horns (about 180-220k tokens a run): "o Claude está
muito gastão! não tem como continuar gastando tanto assim. A gente precisa
criar uma etapa de raciocínio e planejamento, onde o Claude vai descrever
como ele vai fazer, quais os modificadores ele vai usar, qual a ordem, quais
os comandos ele vai utilizar. Tudo isso antes de começar a modelar
propriamente." The runs found their commands by trial: tool calls, renders
and scripts written while building (T2-A: 248 ops and 24 renders for one
horn).

How to apply: SKILL step 5 and `skill/fofuxo-modeling-rules/PLAN.md`: a
`plan.md` with the reading in numbers, the parts, the stack in order, the
exact commands and what each gives, the checks, a budget, the risks and a
Changes log; `round_start(label, plan=...)` refuses an incomplete plan and
the sync warns past its budget. With a human in the session the plan waits
for an OK (this settles step 5's "[TBD]").

### D-066: Read a photo for its form, not for its pixels (Stated, P1)

The P1 hat plan (`models/tasks/chapeu-cowboy/ai/P1/plan.md`) turned a 3/4
photo into millimeters by perspective arithmetic (camera yaw and pitch,
projected ellipses, mm per px at the crown's depth). The modeler: "não são
para serem utilizadas por cima do modelo para 'copiar' a referência. [...]
Ele observaria a forma, entenderia onde deve ser maior, onde deve ser menor,
onde deve curvar, quão grande deve ser o vão etc." and "Você precisa escolher
se precisa de mais referências ou não."

How to apply: from a concept with perspective, read proportions and turning
points (wider here, narrower there, where it curves and how much, the size of
an opening against the whole); one known size anchors the scale (a hat: the
head opening). Other references (front, side, other angles) only help to
understand the form, never to be traced or overlaid; the AI decides whether
it needs them and says why in the plan's Read.

### D-067: Start from the lowest cage, add loops where detail asks (Stated, P1)

P1 decided every cut before building (bisects at fixed heights, the top's
grid moved by computed regions). The modeler: "Todas as peças bem low poly e
ir acrescentando loops onde eu precisar de mais detalhes."

How to apply: the plan's first cage is the fewest vertices that hold the
silhouette; each later loop is named in the plan with where it goes and the
check that calls for it. A loop the check does not call for is not added.

### D-068: In a soft model every part gets Subdivision (Stated, P1)

P1 left the buckle and the band's tail without Subdivision. The modeler's
build: the hat and brim, the band "com subdivision igual ao chapéu", the tail
and the buckle each with Mirror and Subdivision.

How to apply: on a soft (not hard-surface) asset, small mirrored parts get
Subdivision too, and a part wrapped on another uses the same level, so the
density matches (D-015). D-053 still holds for a cage already dense enough.

### D-069: One render per stage that changes the silhouette (Stated, P1)

P1 had four renders for seven stages, none after the crown; a wrong shape
would show only a stage later and cost two stages. The modeler asked whether
more renders would mean less rework; agreed.

How to apply: a stage that changes the outline or an inner form ends with
one render of it; a stage that does not (thickness, materials, counts) ends
with measures only. `select()` previews still check which vertices a region
takes; the render checks the form they make.

### D-070: More than one route can be right (Stated, P1)

P1 built the band as a new cylinder and gave extracting it from the crown
(D-029) as the other route. The modeler: "Assim como na programação, no 3D
existem várias formas de se chegar no mesmo resultado, essa alternativa
também pode estar certa."

How to apply: the plan names the route it takes and why, in one line, and
the other route when one exists. A route is refused only when it cannot reach
the form or breaks a hard limit.

### D-071: A cylinder goes to half and Mirror once the details start (Stated, C1)

The C1 hat was kept whole (D-061) through the brim's curl and the crown's
pinch and crease, every edit made twice, once per side. The modeler: "quando
começamos a adicionar os detalhes da dobra da aba do chapéu, eu teria deixado
de lado o cilindro completo e deletaria metade do modelo e aplicaria o
mirror. o cilindro foi ótimo no começo, mas agora fazer edições nos dois
lados é muito trabalhoso." Also: no face or vertex count to worry about on
this hat; the form first.

How to apply: D-061 holds for the start (extrudes and loops around a whole
cylinder, the cap as a ring around a grid). When the work turns to details
symmetric in X, cut on the plane through vertices already there (the grid
lined up by D-062, or a cap refilled so a row of vertices runs on the
plane), delete the X+ half (D-055) and `add MIRROR`.


### D-072: After the modeler's edit, the AI saves, absorbs and closes (Stated, C1)

The modeler edited the C1 hat in the review Blender and said so, without
saving; `absorb()` found nothing new. The modeler: "coloque na regra que
depois que eu fizer uma edição, é pra você salvar, importar a edição e
fechar o blender."

How to apply: when the modeler says the edit is done, `collect()`: their
Blender saves the review and closes, then `absorb()` brings it in. Never
close it before its save is in (the edit would be lost).
For C1 the review Blender predated `collect()`; it was saved with Ctrl+S
through the screen, then closed.

### D-073: "Delete edge" is Blender's Delete > Edges: it opens a hole (Seen, C1)

The modeler asked, on the C1 hat's top, to "delete" the edge v126-v130; the
AI ran `dissolve_edges`, which merges the two faces (a 5-sided face, refused
under Subdivision). The modeler's own edit in the review deleted the edge
and the faces on it: the patch and half of the mountain's top went away,
leaving the hole where the side dent is built next (an egg's loop of quads,
then Grid Fill).

How to apply: "deletar a edge" / X > Edges is `mesh delete <edges>
type=edge` (faces on it go too); "dissolve" is `dissolve_edges` (faces
merge). When the wording leaves it open, the hole is the likely intent when
a new loop or a fill comes next.

### D-074: Close a hole with the fewest faces, shape it after (Seen, C1)

Watched in the C1 review (the middle dent, 343 operators logged): the
modeler closed the hole first, the ridge extruded in place (E, then cancel
the move) and pulled to the plane, four faces made with F2, and only then
gave it its form.

How to apply: a hole or a new region gets its topology with the fewest
faces (`extrude_region_move` with no move, `edge_face_add`, `fill_grid`);
the shape comes in later steps, never in the same op.

### D-075: Small steps, each group checked (Seen, approved, C1)

The modeler's middle dent: about 60 moves of 1 to 10 mm in 10 minutes, and a
look at the result (Object Mode, Subdivision on and off) about every 20 s.
The AI had computed whole shapes at once and checked once.

How to apply: move in steps of at most about 10 mm; after a group of 3 to 5
steps, one cheap check of the region (a render of that region or a
measure). A whole shape computed at once is the exception, said in the plan.

### D-076: Tidy tools before vertex-by-vertex moves (Seen, approved, C1)

The modeler rounded a ring with LoopTools Circle (flatten), evened loops
with LoopTools Space, slid vertices along the surface with edge and vertex
slide, and lined a row up by scaling one axis to 0.

How to apply: a ring that should be round: `looptools_circle`; loops spaced
unevenly: `looptools_space`; a vertex that should stay on the surface:
`edge_slide` / `vert_slide`; a row that should be level: `resize` with that
axis at 0%. Moving each vertex by hand comes after these.

### D-077: Undo is part of the method (Seen, approved, C1)

LoopTools Circle was run, undone and run again twice before it stayed.

How to apply: an op that did not give the form is undone and tried again
with other settings; it counts as a step of the plan, not a leave from it.

### D-078: Both the cage and the result must make sense (Stated, C1)

The modeler turned Subdivision off and on many times "para avaliar a malha
low poly e a high poly, se ambas faziam sentido. Geralmente eu sempre deixo
as duas fazendo sentido. O que é fazer sentido? R: As faces estão mais ou
menos com o mesmo tamanho e espaçamento das faces ao lado."

How to apply: check the cage and the subdivided result, not only the
result: each face about the size of its neighbours and the loops about
evenly spaced, in both. An uneven cage is fixed even when the result looks
right.

### D-079: The modeler records, the AI converts (Stated, C1)

"Acredito que é uma boa alternativa eu ir fazendo e salvando todos os meu
passos, no final você avalia e converte o que for melhor para você fazer.
[...] precisamos de um ambiente propício para isso, com ferramentas que você
consegue utilizar para replicar tudo o que eu faço." In the Sculpt the
modeler used Grab and Smooth, with large changes.

How to apply: the review Blender records every operator, the ids each one
moved and how far, and the Sculpt's changes with the brush that made them
(`review.ops.jsonl`). After a recorded session the AI writes what it
understood and turns the steps into ops it can run (Grab: `translate` with
`falloff=smooth` at the brush radius; Smooth: `vertices_smooth` or
`looptools_relax` on the region), and into techniques when they repeat.
### D-060: Marks are messages (Stated, B1)

The modeler points at the model with marks: sharp or seam on a loop means
"this loop" (remove it, move it, look at it); crease means "pinch here".
Seen in B1 round 5 (a sharp loop to remove) and round 6 (seams to pull);
confirmed by the modeler. LLM Modeling Bridge reports the marks new or cleared on
every sync, and the AI clears its marks once acted on and says so.

### D-040: Silhouette overlap as an audit check (Stated, T1)

The auditor compares the evaluated mesh's front silhouette with the concept.
Necessary, not sufficient: A2 scored 94.6% and still missed D-036 and D-037.

## Scope

### D-017: Rig is out of scope (Stated, E1)

In E1 the rig only poses the tail and is not exported. For any rig request the
AI answers one of two things: it cannot do it, or it needs more data about the
human use to try.

### D-018: UV is out of scope, seams help modeling (Stated, E1)

Seams give quick selection areas (face select + L, then H / Shift+H to isolate).
They also mark where sharp goes. Most useful for fine edits on lips and the inside
of the mouth.
For the AI: mark seams only if they help it find its way in the mesh. On a
model that already has textures, seams are marked locally and removed when the
edit in that area is done, as humans do.

---

## Communication

### D-019: Blender terms in English (Stated)

Mesh elements, tools and modifiers use Blender's English names, even in a
Portuguese conversation: vertex, edge, face, Mark Seam, Mark Sharp, Subdivision,
Solidify.

---

## Rule candidates

Items seen once (Provisional, AI deductions, proposals), each with the case
that would promote it. At the end of a session the AI asks about the ones
that got their second case (`ROADMAP.md`, Part 2, item 4).

| Candidate | Cases so far | A second case would be | Status |
|---|---|---|---|
| A loop earns its place by ending on a turning point of the outline (item 25) | the modeler's B1 edit: the loop removed in round 5 went back in another place, ending on the rim | a second lobed or heart-shaped part where the modeler places loops the same way | Provisional |
| Lobes fuller than the front view asks for: half depth about a quarter of the full height, sections n 3.1-3.5 | the modeler's B1 edit | the next lobed part (hat brim, skirt ruffle) | AI deduction, pending |
| A covering part hides the junction it makes with another (D-057) | the B1 knot, 11% wider, sides kept in | a belt, button or ribbon over another part | Provisional |
| The cage is bigger than the result on purpose (a steady margin) | E1 (wing 9 mm shorter and 11 mm thinner after Subdivision) | any other modeler cage: the margin measured with `editability` | AI deduction, pending |
| Cage text by loops, permille of a frame (D-049, D-050) | T1, B1 | a second task run with the same format | Provisional (tool) |

Promoted already: marks are messages (D-060, confirmed by the modeler);
"a tight row next to a thin row keeps a pinch" (D-039,
second case in B1 round 5); "remove a loop that carries no shape, refit the
volume" (D-045, second case in B1 round 5).

## Coincidences

- E1 `Fita Azul`: the specific Shrinkwrap settings are exclusive to this model;
  the general idea is D-026.
- E1 vertex group names `ShrinkWrap` / `Shrwink2`: working names, not a naming
  rule.
- The bow about 6% bigger than the concept's silhouette, in E1 (126.1 against
  118.4 mm) and in the modeler's edit of B1 (131.3 against 124.1 mm): "não
  foi proposital, foi a forma que eu encontrei de chegar no formato que eu
  queria mais rápido" (D-056).
- E1 Mirror merge threshold 0.001 (Blender's default) on `Laço Nó`: left as
  it came; the practice is a very small distance (D-054, 0.0001 on `Laço`).

## Open questions

- Boolean slot in the stack: needs a hard-surface example.
