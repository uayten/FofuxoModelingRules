# T2-C: the dragon's horns (Opus, alone)

Saved by the judging session: the run's harness refused report files from a
subagent, so the run returned this text and it was written here unchanged,
with the tokens filled in from the session's usage.

## Contents

- [Delivery](#delivery)
- [What I read](#what-i-read)
- [Reading the scene](#reading-the-scene)
- [Reading the concept](#reading-the-concept)
- [Plan](#plan)
- [Build](#build)
- [Look and measures](#look-and-measures)
- [Shape map](#shape-map)
- [What the user can adjust](#what-the-user-can-adjust)
- [Audit](#audit)
- [Techniques used](#techniques-used)
- [Unsure of](#unsure-of)
- [Tools: what failed or confused me](#tools-what-failed-or-confused-me)
- [Cost](#cost)

## Delivery

- File: `models/tasks/chifre/ai/T2-C-opus/T2-C.blend` (`T2-C.blend1` is Blender's backup of the save before it).
- Parts: `Chifres` → `Mirror(X, mirror_object "Dragão Corpo", clip on, merge 0.1 mm)`. No Subdivision (why: [Build](#build)).
- Cage: 128 vertices, 126 faces, all quads (one horn). Evaluated: 256 v, 252 f (the pair).
- Origin at the horn's root center, buried in the head: (-110.5, -28.0, 448.2) mm. Rotation 0, scale 1.
- Collection `Malha` (where the body is), mesh data `Chifres`, material `Dragão Base`, shade smooth, no parent.
- The cage text: `T2-C.cage/Chifres.txt`. The view sheets: `T2-C.cage/Chifres.png`, `Chifres.views.png`.
- Comparison images: `compare_front.png`, `compare_front_zoom.png` (the concept moved 25 px down, see below, with the body in green and the horns in magenta), `compare_side.png`, `compare_top.png`.
- `T2-C.cage/attempt1_8sides_subdiv/`: the text and sheets of the first version (8 sides + Subdivision 1), which I replaced.

## What I read

1. `skill/fofuxo-modeling-rules/SKILL.md` (whole)
2. `models/TECHNIQUES.md`
3. `models/example/laco/EXAMPLE.md`, the Techniques section only (lines 146–236: all the blocks under it, read together; the ones I used are listed below)
4. `extension/fofuxo_cage/README.md`
5. `models/FEEDBACK.md`
6. `extension/fofuxo_cage/sync.py`, lines 535–604 (`set_frame`, `flip`): to see how a frame is placed
7. `extension/fofuxo_cage/parts.py`, lines 71–150 (`start_part`): to see what happens with an existing name and how the caps are made

I also listed `models/tasks/chifre/` (it holds `prompt.md`, `judge/`, `ai/`, `start.blend`). I opened none of them other than copying `start.blend`. I read nothing from ROADMAP, DECISIONS, judge, the other runs, `tasks/laco`, `.blend` files under `models/example/`, or git.

## Reading the scene

- Objects: `Concept` (Image Empty, `EUA-Frente.png` 1254², size 5 × scale 0.1523 = 761.5 mm, at y 478 mm behind the body), `Dragaozinho` (armature, collection `Rig`), `Dragão Corpo` (2555 v, Armature modifier, collection `Malha`, material `Dragão Base`). Units Metric, cm display. Blender in pt_BR, objects named in Portuguese → Portuguese names.
- Concept → world: x = (px/1254 − 0.5)·761.5 mm, z = 307.3 + (0.5 − py/1254)·761.5 mm (0.607 mm per px).
- **The body against the concept** (D-063), from the evaluated vertices: the head's width matches the concept's (body 374–880 px at the eyes, concept 358–892 px; both centered on x ≈ 627 px). The head's top at the horns is lower on the body: at px 480 the concept head's top is at py 282, the body's at 308, and the same ~25 px at px 440. So I **moved the horns 25 px (15 mm) down** from where the concept draws them: they sit on the body the way they sit on the concept's head. No change of scale (the widths agree within 5%).
- The body has no ears or hat (the concept has both): the horns only have to meet the head.

## Reading the concept

- **Silhouette**: a crescent. From the head it rises and bulges outward (outer edge out to px 367 at py 240–270), then the upper third curves back inward to a blunt tip at about (430, 150) px. The inner edge is almost vertical (px ~440) from the tip down to the hat's brim. Widest ≈ 100 px (61 mm) about a third of the way up; visible height ≈ 180 px (109 mm). The two horns are mirror images within a few px (right horn tip 819 px ↔ 435 mirrored).
- **Inner forms**: the shading shows a faint curved line across the horn a little below mid height (from the outer edge up toward the inner side). I read it as the light's terminator on the lower bulge, not a ridge or a ring; I did not model it (see Unsure).
- **Hidden forms**: the brim hides the lower inner side of each horn: the horn continues as the same round tube under it, down into the head. The root, hidden by the head, is buried in it.
- **Other views** (written before building): side, a round cone leaning a little back, no strong backward curl, since the front view shows the crescent with no foreshortening; top, a round section, since the concept shades it as a round, soft part (D-041).

## Plan

(The skill says to show a plan when there is more than one part; there is one part, but here it is anyway, not waited on.)

- `Chifres`: a cylinder (whole, D-061), loops cut around it, rings moved and scaled along a crescent centerline taken from the concept; `Mirror` across `Dragão Corpo` (side part, E1's horn pattern); origin at the root; not parametric. No cutters, no Geometry Nodes.
- Size: from the concept at the body's scale (factor 1), 15 mm lower (above).
- Model the -X horn (the one on the left of the front view); the Mirror makes the +X one.

## Build

1. `start_part("Chifres", "cylinder", size=(56,56,110), vertices=8)`, `mesh loopcut_slide ring v0-v1 number_cuts=4`: 6 rings, caps from start_part (ring at 80% + grid fill).
2. Rings placed by a script that writes the **base values in the cage text** and then syncs (only positions, no bmesh): for each ring a center and radius read from the concept (px), a depth y, and a plane at right angles to the centerline. Every vertex keeps its angle around the ring. The root cap and the tip cap are domed along the centerline.
3. `add MIRROR at first`, `set Mirror mirror_object "Dragão Corpo"`, `use_clip on`, `merge_threshold 0.1mm`.
4. Three rounds of reading the silhouette over the concept and moving the rings. That version was a good fit (98.5% of the concept's visible horn covered, 2% spill), **but** the evaluated density was **106 faces/dm² against the body's 37** (2.9×). D-015 says no part may be out of proportion. D-053 says Subdivision goes only on a cage that needs it. And SKILL's stack table lists E1's `Chifre` under Mirror and not under Subdivision. Removing Subdivision from the 8-side cage left an octagonal, faceted horn. So:
5. **Rebuilt** with 12 sides and no Subdivision: `start_part(..., vertices=12, subdivision=0)`, `mesh loopcut_slide ring v0-v1 number_cuts=6` → 8 rings (more near the tip, where the curve turns), the same script with 8 ring specs, the Mirror as above. Two more rounds on the tip rings (the upper outer side stuck out 10–15 px). Density now **54 faces/dm²** (1.5× the body's): the edge length of the body, round without Subdivision.
6. `Malha` collection, `Dragão Base` material, Shade Smooth, `set_frame(w=70, d=66, h=143)` so the text's permille fits the horn.

Final rings (concept px after the 25 px shift, radius px, depth y mm), root to tip: (445,395,38,−28) buried · (430,345,50,−26) · (420,300,51,−23) · (415,262,48,−20) · (410,232,35,−15) · (413,210,24,−11) · (422,193,16,−7) · (430,181,10,−4), tip dome 6 mm.

## Look and measures

All from evaluated vertices (the Mirror's result), in world mm:

| measure | model | concept (at body scale, shifted 25 px) |
|---|---|---|
| one horn, x | −157.6 … −88.4 (69.2 wide incl. the buried root) | visible 367…~475 px → −158 … −93 |
| outer edge | px 368 | px 367 |
| tip | px (432, 172) | ≈ (430, 175) |
| z | 441.1 … 583.5 (142.3, of which ~110 above the head) | visible ≈ 109 mm |
| y (depth) | −56.3 … 8.6 (64.9) | not in the concept: round section chosen |

- **Front silhouette over the concept** (`compare_front_zoom.png`, own raster test): the left horn covers **97.3%** of the concept's visible horn pixels, and **1.5%** of the horn's own front area lies over the concept's background. The mirrored right horn gets 95.1% and 3.9%: the concept is not exactly symmetric.
- **On the body**: a BVH test on the evaluated body gives 32 of the 128 horn vertices inside the head (deepest 34.5 mm), and the lowest vertex outside the head is 22 mm above the surface. The root is buried and no seam shows. A horn of the first version poked 0.4 mm out at the outer root; I moved the root ring 10 px lower.
- **Side and top** (`Chifres.views.png`, `compare_side.png`): the horn stands on the head's top a little behind its highest point (y −28 mm, head from −200 to +70), leaning back 24 mm from root to tip. It is round from the top. It matches what I wrote in Reading the concept. 3/4 and back views look whole, with no dents.
- Each object alone and all together: there is one object; the views were drawn with the body in gray.

## Shape map

| form | status | where |
|---|---|---|
| crescent silhouette, bulging outer edge, blunt tip curved inward | **done** | `Chifres` rings L3–L10 |
| width/height proportions against the head | **done** (97% coverage) | whole |
| part under the hat's brim continues to the head | **done** | inner side of rings 2–4 |
| root buried in the head, no gap | **done** | root ring + cap (ring 1) |
| round sections | **done** (12 sides, shade smooth) | all rings |
| side: leans back slightly | **partial**: a guess (no side concept) | ring y values |
| faint line across the lower bulge | **not done**: read as shading | ring 3–4 region, if a human wants it |
| the right horn | **done** by the Mirror | Mirror across `Dragão Corpo` |

## What the user can adjust

- The rings are clean loops (L1 root … L10 tip in the text): scale a ring for thickness, move it for the curve; proportional editing works well on the tube.
- `Mirror`: the pair is live; `mirror_object` is the body, so moving the body's origin moves the mirror plane.
- If the horns should be smoother for a render, a `Subdivision` (level 1) can be added after the Mirror; the cage is dense enough that it will not shrink much (at 12 sides, ~5%).

## Audit

`fofuxo_lib.audit()` does not exist. What I checked in its place, with the sync's validation and my own tests:

- 0 ERROR: every sync reported `issues: []` (quads, no loose geometry, no flipped faces). Scale (1,1,1), rotation 0, stack in canonical order (Mirror only), modifier names default, mesh data name = object name, material present, no cutters.
- WARN, justified: the horns are 1.5× the body's density (54 vs 37 faces/dm²), in the same range; the 8 valence-3 poles are the grid-fill corners of the two caps (D-062, start_part's cap), 4 of them inside the head.
- Not rigged, not parented to `Dragaozinho` (rig out of scope, D-017). No UVs, so `Dragão Base`'s textures will need a UV unwrap from a human (D-018).

## Techniques used

- **A round part with few vertices** (Stated): a 12-side ring is round without Subdivision here. With 8 sides + Subdivision it was also round (the section images showed circles), but denser than the body. Helped. The block's "10 per 1/8 with Subdivision" did not fit a part modeled whole under the density rule; I went by the density.
- **The cage bigger than the result** (pending): used in the first version (radii × 1.15 for the Subdivision's shrink; the first silhouette came out within ~5 px), and then no longer needed without Subdivision. Helped while it applied.
- **Spacing sets how round a turn is** (Stated): the rings are closer together near the tip, where the crescent turns (8 rings, 3 of them in the top quarter). Helped the tip; I measured it only by the silhouette.
- **Loops end on the outline's turning points** (Provisional): I put a ring at the outer bulge (py 262–300) and at the tip's inward turn (py 193–210). It helped fit the crescent with few rings.

## Unsure of

- **The 25 px drop** (D-063): I read the concept's head as taller than the body's at the horns and moved the horns down onto the body. If the modeler instead wants the concept's horn height kept above the body's head, the horns are 15 mm short at the base.
- **Subdivision or not**: I chose none (density, D-053, E1's table). The first version with Subdivision was smoother and just as close to the concept.
- **Depth position and backward lean** (y −28 mm, 24 mm lean): not visible in a front concept. The hat is missing from the file, so I could not check that the horns clear its brim.
- **The faint line** across the horn: shading or a real crease/ring.
- **Material**: `Dragão Base` (the dragon's own, texture-based) rather than a new cream material. No project context said which.
- Name `Chifres` (plural, D-004 for a Mirror pair), though SKILL's table cites E1's object as `Chifre`.

## Tools: what failed or confused me

- `start_part` puts the new object in the Scene Collection, not next to the body; I moved it to `Malha` by hand. It also raises on an existing name (by design), so to rebuild I deleted my own first object and moved its text/state aside (`attempt1_8sides_subdiv/`).
- `sections(..., "h", ...)` on this whole, tilted part reports **n 1.45 or 1.5 on every cut**, while its own image shows circles. It also reports a "waist" (0.35–0.44) that means nothing for a tube, and 0 points for a cut below the frame (`h 300`, after my first frame). I did not trust those numbers; I judged by the image.
- Storing a list of mixed types as an ID property failed (`TypeError: only floats, ints, booleans and dicts are allowed in ID property arrays`). That was my script, not the extension; I moved the data to a scratch JSON so nothing was left in the file.
- There was no op to rotate a ring around its own center, so bending the tube along a curve meant writing the base values of every vertex in the text from a script (positions only, then `sync`). A `rotate <loop> <axis> <deg>` op, or rings placed from a centerline, would do this in the tool.
- `set_frame(w, d, h)` centers the frame on the object's origin. With the origin at the root, the horn's permille runs from about 200 to 1200 on h. Harmless, but it is odd to read.
- `bpy.data.is_dirty` stayed `True` right after `save_mainfile()` (a MeasureIt handler runs on save); a second save printed "Salvo" again. The file on disk is the final one.
- Not called: `review()`, `check_targets` (the prompt's limits).

## Cost

Cost: 10.8 min, 28 syncs, 11 ops, 18 renders, 7 measures, 211,055 tokens
(the subagent's total, 83 tool calls).
