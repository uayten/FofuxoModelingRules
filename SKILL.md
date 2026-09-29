---
name: fofuxo-modeling-rules
description: Non-destructive modeling rules for Blender driven through the official Blender Lab MCP server (Blender 5.2+). Use whenever creating or editing 3D models in Blender via MCP tools (execute_blender_code, get_objects_summary, get_object_detail_summary, get_screenshot_of_area_as_image) — building parts, adding modifiers, boolean cutters, topology, origins, naming, collections. Enforces a live modifier stack instead of baked meshes, the fofuxo_lib helper library instead of raw vertex editing, and a mandatory scene audit before delivery. Never exports.
---

# Fofuxo Modeling Rules

> Status: **draft v0.1**. Rules are being refined from reference models made by a
> human modeler. Items marked **[TBD]** are open and must not be treated as final.

## The one idea

The `.blend` you deliver is a **working file**, not an output. A human will open it
and keep editing. Every dimension, bevel, hole and repetition must still be
adjustable from the modifier panel or a Geometry Nodes input. A mesh that looks
right but can only be changed by moving vertices is a **failed delivery**, no
matter how good it looks.

## Hard limits

Never, under any circumstance:

- Apply a modifier (`bpy.ops.object.modifier_apply`), run
  `bpy.ops.object.convert(target='MESH')`, or do anything else that bakes a
  stack into mesh data.
- Export (`bpy.ops.export_*`, `bpy.ops.wm.*_export`, glTF/FBX/OBJ/USD/STL…).
  Export is a manual human validation step done with Fofuxo FastExport. Your
  job ends at the audit and the saved `.blend`.
- Build finished detail by writing vertices/faces directly (`bmesh`,
  `mesh.from_pydata`, `mesh.vertices[i].co = ...`). Detail comes from
  modifiers. See [When no helper fits](#when-no-helper-fits).
- Delete, apply or merge Boolean cutters.
- Join parts (`bpy.ops.object.join`). Each part stays a separate object, grouped
  by parent (D-003, D-011).
- Use Decimate, Remesh or Triangulate to "fix" a model. **[TBD]**
- Do rig work (armatures, weights, bone parenting) or UV unwrapping. Both are
  out of scope (D-017, D-018). For a rig request, answer that you cannot do it,
  or that you need more data about how a human will use it before trying.

The only transform you apply is **scale**, and only through `apply_scale()`.
Rotation is never applied (D-014).

**Single exception to "never apply":** Solidify, at a specific step where it is
needed (e.g. a later Bevel must hit a single edge loop). Usually the better path
is to extrude only the faces that need thickness (D-013). Report every Solidify
you applied.

## Workflow

Every task follows these steps, in order:

1. **Bootstrap** — load `fofuxo_lib` and check its version (see
   [Library](#library-fofuxo_lib)). If it fails, stop and report; do not fall
   back to raw `bpy`/`bmesh` modeling.
2. **Read the scene** — before creating anything:
   - concept/reference images (Image Empties): they decide the visual choices
     (D-010);
   - the naming language and style of objects already renamed (D-001);
   - existing collections, parents and materials to reuse or follow;
   - project context (name prefixes, shared materials, target: game or
     animation). Ask the user. If the project spans several `.blend` files,
     suggest a project context file in Markdown so the answers are written
     once (D-002).
3. **Scene setup** — `setup_asset("<Asset>")`: units, collections.
4. **Plan** — decompose the object into parts. For each part, write one line:
   base primitive, modifier stack, cutters, parametric or not. For anything
   with more than one part, show the plan in your reply before building.
   Wait for approval? **[TBD]**
5. **Build** — only through library helpers.
6. **Look** — `get_screenshot_of_area_as_image("VIEW_3D")` from at least two angles; compare with
   the request and the concept. Fix before auditing.
7. **Audit** — run the auditor. Fix every `ERROR`. Fix every `WARN` or justify
   it in the report. Re-run until clean.
8. **Deliver** — save the `.blend` and write the delivery report
   (see [Delivery report](#delivery-report)). Stop.

## Base mesh

- Start from the simplest primitive that carries the silhouette: cube,
  cylinder (vertex count = what the silhouette needs, not more), plane,
  circle. Curves as base: **[TBD]**.
- The base mesh is a **cage**: few vertices, all of them meaningful. Allowed
  cage edits (through helpers only): extrude, loop cut, inset, edge data
  (bevel weight, crease, sharp, seam).
- Prefer **edge data over extra geometry** for hard edges: bevel weight +
  `Bevel(limit=WEIGHT)`, or crease + Subdivision, instead of manual support
  loops — they stay editable. **[TBD — confirm against examples]**
- **Split into simple objects.** A complex part becomes several smaller objects
  parented to a main one, so each keeps its own origin, modifiers and tools
  (Sculpt Mode, Proportional Editing Objects) (D-011, D-003).
- **Model world-aligned.** Build the mesh in the straightest orientation, with
  its symmetry axes on the world axes. Pose it afterwards with the object
  rotation, never applied (D-014).
- **Mirror on every axis the shape is symmetric in**, with clipping and merge
  on. A bow symmetric in X, Y and Z is modeled as 1/8 (D-009).
- Closed volume vs. sheet + Solidify is an artistic choice: follow the concept
  (D-012). For thickness, prefer extruding the faces that need it (D-013).
- **Close openings simply** where a body part passes through (sleeves, pants,
  boots, collars): extrude → scale inward → Merge at Center, then push the
  center vertex inside the limb (D-022).
- **Crease holds the silhouette** where Subdivision would pull the shape out of
  place, e.g. a part entering another (D-021).
- **No loose geometry.** Vertices and edges without faces are an error; clean
  with Mesh > Clean Up > Delete Loose (D-020).
- Seams: mark them only if they help you find your way in the mesh. On a model
  that already has textures, remove the seams you added when that edit is done
  (D-018).
- Quads. Triangles and n-gons only on flat faces that no modifier deforms; the
  auditor flags them as `WARN`.
- Regions that will deform (rigging, bending): extra edge loops. Spacing and
  count: **[TBD — from examples]**.

## Modifier stack

> **Under revision.** The table below is the first draft. E1 shows stacks that
> contradict it (`Chapéu`: Subdivision → Bevel → Smooth by Angle). It will be
> rewritten from the examples.

Confirmed so far:

- A Bevel limited by **Weight** goes **after** Subdivision; before it, Subdivision
  multiplies the segments (5 set → 10 out) (D-016).
- Subdivision: only **Levels Viewport** matters. The level comes from the density
  of the whole model and the target (game vs. animation). No part may have a
  density out of proportion to the rest (D-015).

Use only the modifiers the part needs, always in this order. Helpers insert
each modifier at its canonical slot regardless of call order.

| # | Modifier        | Use for                                   | Defaults (draft)                                  |
|---|-----------------|-------------------------------------------|---------------------------------------------------|
| 1 | Mirror          | symmetry                                  | axis X, clipping on, bisect on                    |
| 2 | Array           | repetition                                | merge on; relative or object offset               |
| 3 | Boolean         | holes and cuts from live cutters          | solver Exact                                      |
| 4 | Bevel           | edge rounding / highlight                 | limit Angle 30°, segments 2–3, clamp overlap on   |
| 5 | Solidify        | thickness of sheet parts                  | even thickness on                                 |
| 6 | Subdivision     | smooth / soft forms                       | viewport 1–2, render 2                            |
| 7 | Weighted Normal | shading of low-poly hard-surface          | keep sharp on, weight 50                          |

Open points on the order **[TBD]**:

- Bevel before Solidify rounds only the outline of a sheet; Solidify before
  Bevel also rounds the thickness rim. Which one is the default?
- Subdivision and Weighted Normal usually belong to different pipelines (smooth
  subd vs low-poly hard-surface). Can both appear on the same part?

**Modifier names** stay at their defaults (D-006). Never leave an unused
modifier behind: a second Armature created by re-parenting is removed, and the
remaining one is renamed to plain `Armature`. A disabled modifier may be
intentional; leave it.

## Boolean cutters

- Create them only with `make_cutter(target, ...)`, which also adds the
  Boolean modifier to the target in the right slot.
- They live in the `<Asset>_Cutters` collection, display as **Wire**, are
  **hidden in render**, and stay selectable in the viewport.
- Name: `CUT_<Target>_<Purpose>`.
- Parented to the target so they move together. **[TBD]**
- One cutter per Boolean, or a collection operand for groups of cutters: **[TBD]**.

## Parametric parts and Geometry Nodes

- Use Geometry Nodes when a part is defined by numbers the user will want to
  change (count, length, radius, spacing) and modifier fields alone cannot
  expose them cleanly. Which parts qualify: **[TBD — from examples]**.
- Group inputs have plain names with units (`Length (m)`, `Tooth Count`) and
  sensible min/max.
- Exposing modifier values through custom properties + drivers: **[TBD]**.

## Units, transforms and origin

- Scene: Metric, unit scale 1.0. Display unit follows the scene (E1 shows cm).
- Model at real-world size. If the request gives no size, state the size you
  assumed in the plan.
- Scale applied: every object at `(1, 1, 1)`.
- Rotation not applied: the mesh is world-aligned, the object rotation poses
  it (D-014).
- Origin:
  - self-symmetric part (mirrored on its own axes): at the symmetry center
    (E1: `Laço`) — **Provisional**;
  - side part mirrored across the body: origin on the part, Mirror with
    `mirror_object` = the body (E1: `Asas`, `Chifre`) — **Provisional**;
  - other cases: **[TBD]**.
- The asset rests on the ground plane (Z = 0).

## Naming and collections

- **Language**: the user's. Take it from objects already renamed in the scene;
  if none are, from Blender's language (`preferences.view.language`, even with
  Translate Interface off) (D-001).
- **Objects**: the part name alone (`Laço`, `Chapéu`). A prefix with the asset
  name comes only from the project context (D-002).
- **Child objects**: descriptive name (`Laço Nó`, `Asa Membrana`). Numbering only
  when there are many complex technical names (D-003).
- **Plural** when the object shows more than one unit: a Mirror pair (`Asas`)
  or an Array (`Estrelas`) (D-004).
- **Mesh data** named after its object (D-005).
- **Collections**: one per asset, with sub-collections by role (E1: `Rig`,
  `Malha`). Create a sub-collection when a section has 3+ related objects not
  parented to each other (D-007). An outfit/accessory set gets its own
  collection (E1: `Roupa Estadunidense`) — **Provisional**. Cutters collection:
  **[TBD]**.
- **Materials**: every visible part has one. Generic names for materials
  shared across the project (`Vermelho`); the asset name for exclusive ones
  (`Dragão Base`). Which case applies comes from the project context (D-008).

## Library (`fofuxo_lib`)

> **Proposed API — not implemented yet.** Signatures will change.

Loading: **[TBD — depends on how the library reaches Blender]**.

| Helper | Does |
|---|---|
| `setup_asset(name)` | Metric units, creates `<name>` and `<name>_Cutters` collections |
| `make_part(name, primitive, size, location, ...)` | Primitive at real size, scale applied, origin at base, in the asset collection |
| `add_mirror / add_array / add_bevel / add_solidify / add_subsurf / add_weighted_normal(obj, ..., purpose)` | Add one modifier at its canonical slot, default name |
| `make_cutter(target, name, primitive, size, location)` | Live cutter + Boolean on the target |
| `mark_edges(obj, selector, bevel_weight=, crease=, sharp=)` | Edge data on edges picked by a selector (by angle, axis, boundary) |
| `loop_cut(obj, selector, cuts)` | Cage loop cut, for deformation or silhouette |
| `set_origin(obj, mode)` | `BASE`, `MIRROR_PLANE`, `PIVOT(point)` |
| `apply_scale(obj)` | The only transform-apply allowed |
| `audit()` | Runs the auditor, returns the report |

## When no helper fits

**[TBD]** Draft: stop and tell the user which helper is missing and what it
would do. Do not improvise with raw `bmesh`. A gap in the library is fixed in
the library, not worked around in the model.

## Audit

Run the auditor at the end of every task, and after every fix, until it is
clean. It reports, per object:

- modifier stack (types, names, order vs canonical order)
- scale applied or not
- origin position relative to the bounding box
- polygon count, triangles, n-gons
- flipped normals
- missing materials
- baked-mesh suspicion: high polygon count with an empty or trivial stack
- density outliers: evaluated faces per area far from the rest of the model
  (the human check: zoom out, wireframe on) (D-015)
- loose geometry: vertices and edges with no face (`ERROR`; fix with Delete
  Loose)
- leftover modifiers: duplicated Armature, `.001` suffix on a lone modifier
- mesh data name different from the object name
- cutters: collection, display type, render visibility, orphan cutters

Severity: `ERROR` blocks delivery; `WARN` must be fixed or justified.

## Delivery report

End every task with:

1. File saved (path).
2. Parts: name → stack, one line each.
3. What the user can adjust and where (modifier / GN input).
4. Audit summary: `0 ERROR`, list of `WARN` with justification.
5. Library gaps found, if any.

Do not offer to export.

## Communication

Mesh elements, tools and modifiers use Blender's English names, in any
language: vertex, edge, face, Mark Seam, Mark Sharp, Subdivision, Solidify
(D-019).
