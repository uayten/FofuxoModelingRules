# T2-D (opus): dragon horns, no techniques step

Saved by the judging session: the run's harness refused report files from a
subagent, so the run returned this text and it was written here unchanged,
with the tokens filled in from the session's usage.

## 1. File

`models/tasks/chifre/ai/T2-D-opus/T2-D.blend` (copy of `start.blend`; `start.blend` untouched). Cage text and sheets in `T2-D.cage/` (`Chifres.txt`, `Chifres.png`, `Chifres.views.png`, `Chifres.sections.png`, `rounds.json`). `concept_overlay.png`: the concept with the horn outline in magenta (moved up 19 mm to the concept's head), the horn where it really is in green, and the body outline in yellow.

## What I read

- `skill/fofuxo-modeling-rules/SKILL.md` (all of it)
- `extension/fofuxo_cage/README.md`
- `models/FEEDBACK.md`
- `models/tasks/chifre/prompt.md` (the task folder's own prompt; not in the forbidden list)
- Extension code, only where the README did not say enough:
  - `extension/fofuxo_cage/parts.py`, `start_part`, lines 60-160: where the origin and the caps go.
  - `extension/fofuxo_cage/sync.py`, `set_frame`, lines 535-610: where the frame sits on an axis the part does not mirror on its own.
  - A grep of the `def` lines for `start_part`, `set_frame`, `views`, `round_start/end`, `edit`, `profile`, `sections`, `audit`, `check_targets`, `editability`, `deviation`.
- The concept image, saved out of the file with bpy (and crops of it).

Not opened: `TECHNIQUES.md`, `models/example/`, `ROADMAP.md`, `DECISIONS.md`, `judge/`, the other runs, `laco/`, git history. `review()` and `check_targets` were not called.

## Scene read (step 2)

- **Objects:**
  - `Concept`: Image Empty with `EUA-Frente.png`, 1254 px wide and shown 0.7615 m wide (0.607 mm/px). Centered at x 0, z 0.3073, at y +0.478.
  - `Dragão Corpo`: mesh with an Armature modifier and the material `Dragão Base`, textured through UVs.
  - `Dragaozinho`: the armature.
- **Collections:** `Dragão Base` > `Rig`, `Malha`; and `Referência`.
- **Units and language:** metric, scale 1, cm display. Language pt_BR (object names and `preferences.view.language`).
- **Body against the concept:** I projected the body's evaluated vertices onto the image. Eyes, nostrils, fangs and head width line up, so the scale matches. The body's head top is 17 to 20 mm lower than the concept's at the horns' place. I compared the first blue pixel under the hat and horns with a downward ray on the body at the same x (z in mm):

  | x (mm) | concept z | body z |
  |---|---|---|
  | 80 | 520 | 503.5 |
  | 100 | 509 | 491 |
  | 125 | 488 | 469.5 |
  | 135 | 477 | 458 |

  The body wins (D-063). The horn is moved 19 mm lower than the concept draws it, and keeps its size in mm (the scales match).
- **Head top at the horn's place:** x 125 mm, z ≈ 470 mm, highest around y −40 to −60 mm.

## Concept read (step 4)

- **Silhouette** (the dragon's left horn, image right; the other side matches within 1 to 2 px): a thick cream horn in a crescent shape.
  - Tip at (117, 597) mm in the concept (x, z).
  - The outer edge bulges out to x 155 at z 511 to 523, then comes back in to x 135 where it meets the head (z 478).
  - The inner edge runs almost straight up at x ≈ 109 to 110 from the tip down to z 567. It then flares toward the hat to x 94 at z 542. Below that the brim hides it.
  - Width: about 62 mm horizontally at the widest, 38 mm at 20 mm below the tip, 20 mm at 6 mm below it.
  - Visible height about 118 mm.
- **Inner forms:** a soft line across the horn at about 45% of its height. I read it as the lower part facing the viewer and the upper part turning away (bending back). The tip is rounded, not sharp.
- **Hidden forms:** the inner lower part continues behind the brim and the head toward the center, to about x 88. The root is buried in the head.
- **Other views** (imagined):
  - Sections are round (D-041), a little narrower in depth than in width.
  - From the side, the horn rises and sweeps back about 30 mm by the tip, which curls slightly up and back.
  - From the top, a round footprint on the head's upper side, behind the brim's front edge (y ≈ −30 mm).
- **Techniques:** skipped by the run's rules.

## Plan (step 5; written here and carried out without waiting)

One part:

- **`Chifres`:** a cylinder with 8 vertices, modeled whole (D-061).
  - Stack: Mirror X with `mirror_object` = `Dragão Corpo`, then Subdivision level 1 (small accessory). No cutters, not parametric.
  - The base cap is deleted: the root is buried in the head (D-022, lean cage).
  - 7 rings along a bent axis: L1 buried, L2 to L6 up the horn, L7 the cap's inner ring, and the tip vertex.
- **Origin** on the part, at the base ring's center (the rule for a side part mirrored across the body). Rotation 0, scale 1, world-aligned.
- **Name** `Chifres`, plural for a Mirror pair (D-004). The skill's table lists E1's as `Chifre`, but the naming rule's text says the plural.
- **Collection and material:** `Malha`, `Dragão Base`.
- **Size** taken in mm from the concept (it shares the body's scale). **Placement** 19 mm lower than drawn (see the scene read).

## 2. Parts

- `Chifres` → Mirror (X, mirror_object `Dragão Corpo`, clip off, merge on 0.1 mm) > Subdivision (levels 1, render 2). Location (104, −32, 462) mm, rotation 0, scale 1, material `Dragão Base`, collection `Malha`, no parent.
- Cage: **57 v, 52 f**, all quads, open at the buried root. Evaluated with both horns: 434 v, 416 f, 0 triangles or n-gons.

How it was built, all through Fofuxo Cage:

1. `start_part("Chifres", "cylinder", size=(50,50,130), vertices=8)`
2. `mesh delete faces h<1`
3. `mesh bisect all plane=h200/400/600/800`
4. `add MIRROR at first`, `set Mirror mirror_object "Dragão Corpo"`, `set Mirror use_axis X`, `set Mirror merge_threshold 0.1mm`
5. Vertex positions: I rewrote the base w d h lines of the cage text and synced. The values came from a ring spec in Python (center, radius across, radius in depth, each ring square to the bent axis), tuned in two passes against the concept.

## 3. Shape map

| form | status | where |
|---|---|---|
| crescent silhouette: outer bulge, tip back inward | **done** | L2 to L3 (bulge), L5 to L7 (tip) |
| outer edge profile | **done**: within 1 to 3 px (≤ 2 mm) of the concept on every row from the tip to the head | L2 to L6, +X side |
| inner edge, upper half | **done**: within 1 to 4 px | L4 to L6, −X side |
| inner flare toward the hat (concept z 542) | **partial**: 6 px (3.5 mm) short at its widest row; the brim hides it in the concept anyway | L3/L4, −X side |
| rounded tip | **done**: cap ring plus a center vertex, so round rather than pointed | L7, v24 |
| line across the horn (bend back) | **partial**: the horn sweeps back ~30 mm and the tip tilts back, but there is no separate crease | L4 to L7, d |
| root buried in the head | **done**: all 32 evaluated border vertices are inside the body | L1 |
| round sections | **partial**: horizontal cuts give n ≈ 1.45 to 1.5. They cut the leaning horn at a slant; 8 sides at level 1 look faceted up close | all rings |
| side view: sweep back | **done** (my reading; no side concept) | ring centers y −32 → −1, tip y +1 |

## 4. Measures

From the evaluated vertices, one horn (+X), world, mm.

- **Size and place:**
  - x 84.1 to 155.2, y −55.2 to 2.7, z 446.1 to 577.8.
  - Tip at (117.4, −1.7, 577.8).
  - One side: 71.1 × 57.9 × 131.7 (w × d × h, including the buried root).
  - The pair spans 310.5 mm in x.
- **Against the concept**, with the horn moved +19 mm and rasterized at level 3 over the image:
  - Outer edge by row (model/concept px): 832/831, 845/845, 854/855, 861/862, 867/868, 871/873, 874/877, 877/880, 879/882, 881/883, 882/883, 881/882, 879/880, 877/877, 874/873, 870/869.
  - Tip: x 117 vs 117; z 577.8 vs 578 (597 − 19).
  - IoU over the horn's unhidden upper part: **0.93**.
- **Against the body:** the horn enters the head at z ≈ 458 on the outer side and ≈ 500 on the inner side. Visible length along the outer edge ≈ 120 mm (concept: 118 mm).
- **Views checked:** front, right, top, 3/4 front (yaw 35°, pitch 20°) and 3/4 back (yaw 150°, pitch 25°), each with the body shown (`Chifres.views.png`), plus the view sheet (`Chifres.png`).

## 5. What the user can adjust

- **Bend and thickness:** the ring centers and radii (L1 to L7) in the cage text; the tip is v24.
- **Smoothness:** `Subdivision levels` (1 now; 2 would remove the octagonal facets if the model's density allows).
- **Placement of the pair:** the object location. The Mirror follows the body's origin.

## 6. Audit

There is no `fofuxo_lib.audit()`. I checked by hand and with the sync's checks.

- **0 ERROR:**
  - canonical order (Mirror > Subdivision), default modifier names;
  - scale 1, rotation 0;
  - quads only (cage and evaluated);
  - no loose geometry, no `inside_out`;
  - material set, mesh data named `Chifres`;
  - no cutters.
- **WARN `open_edge`** (v0 v2 v4 v6 v8 v10 v12 v14): on purpose. It is the buried root, removed because every border vertex is inside the body.
- **Not parented** to the body or the rig: rig work is out of scope (D-017). A rigger parents it to the head bone.
- **No UVs** (D-018): with the textured `Dragão Base`, the horns show cream only after they are unwrapped onto the atlas.
- **Hard limits kept:** no modifier applied, no export, no join.

## 7. Library gaps and tool notes

- **No `audit()`** in the extension, so the audit was manual.
- **Merge distance:** `start_part` gives Mirror merge 0.1 mm, but the `add MIRROR` op gives Blender's default 1 mm. I had to `set` it.
- **No op to place whole rings along a bent axis** (horn, tail). I wrote the text's base lines from Python. An op like `ring <L> center= radius= normal=`, or a sweep along a curve, would make this one line per ring.
- **No way to compare the silhouette with the concept at an offset**, when the body and the concept disagree about where the part sits. The concept panel draws the image where the empty is, so the horn looks 19 mm low there. I rasterized the evaluated mesh over the image with numpy. `set_frame(concept=...)` has no z offset.
- **Slanted sections:** horizontal `sections` of a leaning horn cut it at a slant, so n and the sizes read low. A cut square to the part's axis would be the right measure.
- **My own slip:** my first z conversion from the concept was wrong by about 25 mm (arithmetic). Projecting the body onto the image caught it.
- No tool errors or refusals.

## Unsure

- **Depth placement and sweep:** the concept is front only. y −32 at the base and ~30 mm of sweep back are my choice.
- **The 19 mm move down:** I carried the horn with the head's top. The other choice was to keep the tip's height and lengthen the horn.
- **Depth radius:** 0.85 of the width at the lower rings.
- **Open base:** I opened it (leaner, hidden) instead of keeping it closed.
- **Name:** `Chifres` versus E1's `Chifre`.
- **Facets:** level 1 on 8 sides looks slightly faceted up close.

Cost: 5.1 min, 13 syncs, 9 ops, 2 renders, 11 measures, 182,780 tokens (the
subagent's total, 45 tool calls).
