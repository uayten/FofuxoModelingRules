---
name: fofuxo-modeling-rules
description: Non-destructive modeling rules for Blender driven through the official Blender Lab MCP server (Blender 5.2+). Use whenever creating or editing 3D models in Blender via MCP tools (execute_blender_code, get_objects_summary, get_object_detail_summary, get_screenshot_of_area_as_image) — building parts, adding modifiers, boolean cutters, topology, origins, naming, collections. Enforces a live modifier stack instead of baked meshes, the fofuxo_lib helper library instead of raw vertex editing, and a mandatory scene audit before delivery. Never exports.
---

# Fofuxo Modeling Rules

> Status: **draft v0.1**. Rules are being refined from reference models made by a
> human modeler. Items marked **[TBD]** are open and must not be treated as final.

## The two ideas

1. **Shape first.** The model must match the concept's shape and proportions.
   This matters more than anything else in this skill: a clean, non-destructive
   stack on the wrong shape is a **failed delivery** (D-032). The concept is a
   starting reference, read for proportions and for the points where its
   outline turns, not a stencil: a 2D drawing of an organic object works from
   one angle, the 3D has to work from all of them (D-056). A model that covers
   the drawing's silhouette exactly can still be the wrong shape.
2. **A working file, not an output.** A human will open the `.blend` and keep
   editing. Symmetry, smoothing, thickness and repetition stay live in the
   modifier stack. A mesh with the right shape but baked symmetry or smoothing
   is also a **failed delivery**: cut it and put the Mirror back (D-034).

## Hard limits

Never, under any circumstance:

- Apply a modifier (`bpy.ops.object.modifier_apply`), run
  `bpy.ops.object.convert(target='MESH')`, or do anything else that bakes a
  stack into mesh data.
- Export (`bpy.ops.export_*`, `bpy.ops.wm.*_export`, glTF/FBX/OBJ/USD/STL…).
  Export is a manual human validation step done with Fofuxo FastExport. Your
  job ends at the audit and the saved `.blend`.
- Build by hand what a modifier should produce: the mirrored half, the
  smoothed surface, the thickness, the repeated copies. The cage (silhouette)
  is yours to shape; smoothing, symmetry, thickness and repetition come from
  modifiers (D-033).
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
4. **Read the concept** — before planning, write down the shape you see, in
   three layers (D-036, D-037):
   - **silhouette**: the outer contour and its proportions;
   - **inner forms**: every dent, fold, crease and bulge the shading shows
     (E1 bow: a dent in the middle of each wing's outer edge, a fold where each
     wing enters the knot). Each one needs edge loops in the cage;
   - **hidden forms**: extend the visible contours behind the parts that hide
     them. E1 bow: the wings' top and bottom edges keep converging behind the
     knot, crossing like an X, so each wing narrows almost to a point at the
     center. The concept only shows what is visible; the model must be whole;
   - **the other views**: a front concept still implies a top and a side.
     Imagine them and write them down. E1 bow from the top: each wing also
     narrows in depth toward the center, a figure eight, not a flat bar.
     Forms that look round in the concept get round cross-sections, not boxy
     ones (D-041).
   - **techniques**: look each form up in `models/TECHNIQUES.md` and read
     only its block (when, how, how to measure). One marked pending or
     Provisional is a lead, not a rule: use it, measure it, say so.
5. **Plan** — decompose the object into parts. For each part, write one line:
   base primitive, modifier stack, cutters, parametric or not. For anything
   with more than one part, show the plan in your reply before building.
   Wait for approval? **[TBD]**
6. **Build** — only through library helpers.
7. **Look** — compare the shape with the concept before anything else (D-032).
   Check **each object alone first** (Local View, `/`), then **all together**
   (D-042):
   - front, top and side orthographic views of each object; the top and side
     must match what you wrote in step 4, not just look plausible;
   - front orthographic view aligned with the concept's Image Empty, the model
     over the image: silhouette and proportions must match. Then put a
     screenshot of the model **side by side** with the concept at the same
     scale: that is where the inner forms show (T1, A3);
   - parts in front must stay whole: check that no part hides another that
     the concept shows (T1, A3);
   - every inner and hidden form listed in step 4 is in the model. A matching
     outer silhouette is not enough: in T1 a bow with 94.6% silhouette overlap
     still missed the dents, the folds and the narrowing behind the knot;
   - at least one more angle (side or 3/4) for depth;
   - measure the dimensions with code, from the **evaluated vertices**
     (`evaluated_get(depsgraph).to_mesh()`), never from `obj.dimensions` or
     `bound_box`: with GPU Subdivision on, those measure the cage, not the
     subdivided surface. In T1 `obj.dimensions` gave 14.0 × 10.0 cm for a bow
     whose evaluated vertices span 13.5 × 7.1 cm (D-044).
   Fix the shape before auditing.
8. **Audit** — run the auditor. Fix every `ERROR`. Fix every `WARN` or justify
   it in the report. Re-run until clean.
9. **Deliver** — save the `.blend` and write the delivery report
   (see [Delivery report](#delivery-report)). Stop.

## Base mesh

- Start from the simplest primitive that carries the silhouette: cube,
  cylinder (vertex count = what the silhouette needs, not more), plane,
  circle. Curves as base: **[TBD]**.
- **The cage carries the silhouette; Subdivision only smooths it** (D-033).
  Give the cage the vertices the silhouette needs (pinches, flares, notches):
  E1's bow uses 33 vertices per 1/8. A cage too sparse for the shape, with a
  high Subdivision level making up the form, is wrong: in test T1 a 7-vertex
  cage at level 2 turned a bow tie into a bone. On small accessories,
  Subdivision level 1. Allowed cage edits (through helpers only): extrude,
  loop cut, inset, moving vertices, edge data (bevel weight, crease, sharp,
  seam).
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
  on. A bow symmetric in X, Y and Z is modeled as 1/8 (D-009). Keep the merge
  distance very small (0.1 mm): vertices weld only when they touch the plane,
  never because they came close to it (D-054).
- **Except cylinders: model them whole** and edit them with extrudes and
  loops cut around them. Cutting a cylinder and mirroring it is tempting,
  and wrong: a cap cut on the planes comes out uneven (D-061). A cap: keep
  only the top's outer loop, extrude it, scale it in X and Y toward the
  center, Grid Fill the new loop (D-061), the grid turned to run through the
  loop's X and Y extremes, so the mesh could be cut in quarters (D-062).
- **Model the half on -Y**, the side the front view sees, so the vertices you
  edit are in front of their mirror copy (D-055).
- Closed volume vs. sheet + Solidify is an artistic choice: follow the concept
  (D-012). For thickness, prefer extruding the faces that need it (D-013).
- **Close openings simply** where a body part passes through (sleeves, pants,
  boots, collars): extrude → scale inward → Merge at Center, then push the
  center vertex inside the limb. With Subdivision, do not merge (it makes
  triangles): squeeze the opening closed and hide it inside the other part
  (D-022).
- **Model one unit, repeat with Array.** One well-modeled star + Array, not ten
  copies (D-024).
- **Thin parts get a small volume in games** (ears, wing membranes): engines
  render one side of a face by default, so a flat plane would need a
  double-sided material (D-025).
- **A part that sits on another starts from its faces** (duplicate/extract
  them), so it matches the surface from the start (D-029).
- **Shrinkwrap fits one thing onto another**: clothes over a body, an object on
  top of another, a Lattice onto a mesh, retopology. Limit each Shrinkwrap to a
  vertex group and pick the wrap method per job (Nearest Surface Point to stay on
  the surface, Nearest Vertex to snap onto vertices). Once the fit is done, a
  Shrinkwrap may stay disabled as a backup to redo it (D-026).
- **Thin strips** (ribbons, belts, straps): round the rim with a Bevel after
  Solidify, not with Subdivision. Subdivision handles long rectangular faces
  poorly and pulls the rounding toward the center (D-027).
- **Boolean is for hard-surface** (windows, doors, shelves, straight props).
  Avoid it on organic characters (D-028).
- **Spacing sets roundness.** Subdivision smooths every turn: loops placed
  close together keep a pinch, fold or dent after it; loops spread apart make
  it round. E1's bow has its center vertices packed "juntinhos" so the wing
  narrows into the knot; the pinch where B1's wing enters the knot needed the
  row next to the thin middle row close to it; the modeler rounded B1's heart
  lobes by spreading their edges (D-039).
- **Start lean.** Too many loops cost more than too few: a cage with excess
  loops has to be cleaned and then shaped anyway. A loop that carries no form
  is removed and the volume refitted by moving vertices (D-045).
- **Low poly, stylized.** A game asset must be low poly, and a stylized one
  may carry abstractions the real object does not have: roundness and shape
  follow the concept's stylization (D-051).
- **A covering part hides the junction it makes** with the part it covers:
  B1's knot grew to hide where the wings cut into it, hugging them at its
  sides (D-057) — **Provisional**.
- **Crease holds the silhouette** where Subdivision would pull the shape out of
  place, e.g. a part entering another (D-021).
- **No loose geometry.** Vertices and edges without faces are an error; clean
  with Mesh > Clean Up > Delete Loose (D-020).
- Seams: mark them only if they help you find your way in the mesh. On a model
  that already has textures, remove the seams you added when that edit is done
  (D-018).
- Quads. **Under Subdivision, zero triangles**: they break the normals and
  the shading around them (D-023). Without Subdivision, triangles and n-gons
  only on flat faces; the auditor flags them as `WARN`, and as `ERROR` on a
  mesh with Subdivision.
- Regions that will deform (rigging, bending): extra edge loops. Spacing and
  count: **[TBD — from examples]**.

## Modifier stack

Confirmed so far:

- A Bevel limited by **Weight** goes **after** Subdivision; before it, Subdivision
  multiplies the segments (5 set → 10 out) (D-016).
- Subdivision: only **Levels Viewport** matters. The level comes from the density
  of the whole model and the target (game vs. animation). No part may have a
  density out of proportion to the rest (D-015). To judge it in wireframe,
  turn Subdivision's **Optimal Display off** (restore it afterwards) (D-031).
- Subdivision position: last for meshes that will be animated; otherwise
  where the final form needs it, as in the table below. When the order changes
  nothing in the result, either is fine (D-030).
- **Subdivision only for a cage that needs it**: a cage dense enough to carry
  its shape goes without; Subdivision is for a lower-poly cage (D-053).
- The AI adds, removes, sets and reorders modifiers, and applies one only in
  specific cases, decided case by case and reported (D-052).

Use only the modifiers the part needs, always in this order. Helpers insert
each modifier at its canonical slot regardless of call order.

**Order for modeling** (rebuilt from E1):

| # | Modifier        | Use for                                        | E1 evidence                          |
|---|-----------------|------------------------------------------------|--------------------------------------|
| 1 | Shrinkwrap      | re-fit a part onto another (D-026)             | `Fita Azul`                          |
| 2 | Mirror          | symmetry; clipping + merge on                  | `Laço`, `Chifre`, `Asas`             |
| 3 | Boolean         | hard-surface holes and cuts (D-028)            | none yet (slot **[TBD]**)            |
| 4 | Subdivision     | smooth / soft forms                            | `Laço`, `Chapéu`, `Fita Azul`        |
| 5 | Solidify        | thickness, after Subdivision                   | `Fita Azul`                          |
| 6 | Bevel           | localized (limit Weight); rounds strip rims    | `Chapéu`, `Fita Azul` (D-016, D-027) |
| 7 | Array           | repeat the finished unit (D-024)               | `Estrelas` (Geometry Nodes Array)    |
| 8 | Smooth by Angle | shading, last                                  | `Chapéu`, `Asas 2`                   |

Weighted Normal: no evidence in E1 yet. Boolean slot: **[TBD]** until a
hard-surface example.

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
- Size: the concept's proportions win over a requested number, with some
  tolerance (D-038). If the request gives no size, state the size you assumed
  in the plan.
- Scale applied: every object at `(1, 1, 1)`.
- Rotation not applied: the mesh is world-aligned, the object rotation poses
  it (D-014).
- Origin:
  - self-symmetric part (mirrored on its own axes): at the symmetry center
    (E1: `Laço`) — **Provisional**;
  - side part mirrored across the body: origin on the part, Mirror with
    `mirror_object` = the body (E1: `Asas`, `Chifre`) — **Provisional**;
  - other cases: **[TBD]**.
- Placement: no ground rule; the mesh origin is not tied to Z = 0. Model
  world-aligned (D-014), and **move, rotate and scale the concept's Image
  Empty** until it sits in a good position to read against the model, e.g. an
  asymmetric or tilted concept (D-035). Adjusting the reference is always
  allowed; it never goes to render.

## Naming and collections

- **Language**: the user's. Take it from objects already renamed in the scene;
  if none are, from Blender's language (`preferences.view.language`, even with
  Translate Interface off) (D-001).
- **Objects**: the part name alone (`Laço`, `Chapéu`). A prefix with the asset
  name comes only from the project context (D-002).
- **Child objects**: descriptive name (`Laço Nó`, `Asa Membrana`). Numbering only
  when there are many complex technical names (D-003).
- **Plural** when the object shows more than one unit of the thing its name
  describes: a Mirror pair (`Asas`: two wings), an Array (`Estrelas`). A bow
  with two loops is still one bow (`Laço`) (D-004).
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
- silhouette overlap with the concept in front view (evaluated mesh vs. the
  concept's object mask). A low overlap is an `ERROR`; a high one does not prove
  the shape (inner and hidden forms are checked in Look) (D-040)
- evaluated dimensions, measured from the evaluated vertices (D-044)
- open edges on the evaluated mesh: a closed part must stay closed after the
  Mirror (a too-high merge threshold can weld rows near the mirror plane)
- leftover modifiers: duplicated Armature, `.001` suffix on a lone modifier
- mesh data name different from the object name
- cutters: collection, display type, render visibility, orphan cutters

Severity: `ERROR` blocks delivery; `WARN` must be fixed or justified.

## Delivery report

The delivery is an **honest, editable base** (D-043): the best shape you could
reach, with a live stack, and a precise map of what is still missing. Never
report the shape as done when it is not.

End every task with:

1. File saved (path).
2. Parts: name → stack, one line each.
3. **Shape map**: every form you wrote in step 4 (silhouette, inner, hidden,
   other views), each marked **done**, **partial** or **not done**, with the
   object and area where it lives. This is where a human will finish the work.
4. Measured dimensions (from code) vs. the concept.
5. What the user can adjust and where (modifier / GN input).
6. Audit summary: `0 ERROR`, list of `WARN` with justification.
7. Library gaps found, if any.

Do not offer to export.

## Communication

Mesh elements, tools and modifiers use Blender's English names, in any
language: vertex, edge, face, Mark Seam, Mark Sharp, Subdivision, Solidify
(D-019).
