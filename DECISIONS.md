# Decisions

Every rule in `SKILL.md` comes from here. Each entry says what the rule is, why
(in the modeler's words when possible), and which example it came from.

Status:

- **Stated**: the modeler stated it as a general practice.
- **Provisional**: inferred from a single example; confirm with another.
- **Open**: question still pending.

Examples:

- **E1**: `Laço.blend`, dragon + "Roupa Estadunidense" outfit. Focus: the bow tie
  (`Laço`, `Laço Nó`).

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

### D-004: Plural when the object shows more than one unit (Stated, E1)

A Mirror pair (left and right wings: `Asas`) or an Array (`Estrelas`) makes the
name plural. By this rule `Chifre` should be `Chifres`: the inconsistency in E1
is human, not a rule.

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
is then pushed inside the sleeve/limb. Same logic in E1 on the knot and wing
junction of the bow.

---

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

## Coincidences

- E1 `Fita Azul`: the Shrinkwraps have very specific functions, exclusive to this
  model.
- E1 Mirror merge threshold: 0.0001 on `Laço`, 0.001 on `Laço Nó`.

## Open questions

- Modifier stack order: to be rebuilt from E1 `Chapéu`, `Fita Azul`,
  `Estrelas`, `Asas`.
