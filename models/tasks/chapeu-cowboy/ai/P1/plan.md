# Plan: Chapéu (straw cowboy hat, run P1)

## Read
- Sources read: SKILL.md, PLAN.md, the task's `prompt.md`, `concept.jpg`; from
  the cage README only "New parts", the Mesh op selection and operator rows
  used below (`delete`, `bisect`, `resize`, `translate`, `extrude_scale`),
  the modifier text ops (`add`, `set`, `crease`), `views`, `profile`,
  `sections`, `select`, `round_start`. `models/TECHNIQUES.md` index read; no
  block opened (every block points into `models/example/`; "Spacing sets
  roundness" is used as SKILL states it, D-039).
- Scene (background Blender, print only): metric, centimeters, unit scale 1.
  One object: `Concept` image empty in collection `Referência`, at
  (0, 300, 135) mm, rotation X 90°, display size 0.5 m, image 610 × 610 px
  centered. No body. Naming language: Portuguese (the collection is
  `Referência`, D-001).
- Scale: no body, so the anchor is the head. An adult head opening of 58 cm
  around is an oval of about 200 × 166 mm inside the crown (front-back ×
  side-side; perimeter 576 mm). With 2.5 mm of straw, the crown's outer
  surface at the band is 205 (d) × 171 (w) mm. The photo is a 3/4 view from
  the hat's front-left of the wearer's left side (camera yaw about +50°,
  pitch about +20°; the image's right tip is the back, +X side; the front,
  -Y, faces lower-left). At that yaw the 171 × 205 ellipse projects to
  sqrt((85.5·cos50)² + (102.5·sin50)²) × 2 = 192 mm across; it measures
  242 px (x 188 to 430 at the band), so 0.79 mm/px at the crown's depth
  (the empty's guess is 0.82). Correction: `Concept` display size
  0.5 × 0.79/0.82 = 0.482 m. A perspective photo: it is compared side by
  side with a "50,20" view, never overlaid for silhouette.
- The hat as photographed, in numbers (0.79 mm/px; near parts are about 4%
  larger from perspective):
  - brim tip to tip 512 px = 404 mm projected; with the sides curled the
    flat brim is 105 mm wide all around (crown 171 × 205 + 2 × 105 =
    381 × 415 mm flat, about 365 × 415 mm seen from the top once curled).
  - crown height: 205 px from the band's lower edge (y 345) to the ridge
    (y 140); minus 43 px for the ridge sitting about 100 mm behind
    (100 · sin20°) and divided by cos20°: about 136 mm; taken as 128 mm at the
    side ridges (a 4 7/8" cattleman crown).
  - crown taper: the top is about 93% of the base in w, 95% in d.
  - top crease (cattleman): a trough front to back, about 25 mm deep at the
    center (top center at about 100 mm), opening toward the front
    (front rim of the top about 18 mm lower than the ridges) and less at the
    back (8 mm).
  - front pinch: the crown's upper front third pressed in from both sides to
    about 70% of its width (teardrop from the top, point to the front).
  - brim: flat for the first 30 mm out of the crown; the sides (±X) curl up
    to about +45 mm at the edge's middle, +30 mm at ±30° from it, and move
    in about 12 mm; the front edge dips 12 mm, the back 8 mm, below the
    crown base plane. The crown-brim junction is a sharp fold.
  - band: black ribbon 9 mm tall (11 px) at the crown base, about 2 mm
    proud of the straw.
  - buckle (concho): silver, 11 × 14 mm (14 × 18 px), 3 mm thick, on the
    band at the wearer's left side, 45° toward the back:
    (65, 77.5) mm in plan.
  - tail: one strap 8 mm wide, about 149 mm long (181 px), from under the
    buckle across the brim forward to (135, -55) mm, lying on the brim,
    its end raised about 9 mm by the curl.
  - vent holes: 3 eyelets per side, Ø 5 mm, 12 mm apart, about 60 mm above
    the band toward the front.
- What the 800-face budget keeps: crown with taper, crease and front pinch;
  brim with curl and dips; the sharp junction; straw thickness (D-025); band;
  buckle; tail. What it drops, to texture or normal map: the 6 vent eyelets,
  the straw weave, the brim's bound edge, the band's stitching and the
  buckle's relief.
- What the 3D needs (D-064): the crown is a closed oval tube 171 × 205 mm at
  the base, 159 × 195 at the top; the brim and crown are one sheet (the
  crown's base ring turns into the brim; the head opening is the hole inside
  that ring, not a border). Side view: crown 128 mm at the ridges, top
  dipping to about 100 mm at the center, brim edge from -12 (front) to -8
  (back). Front view: brim edges rising about 45 mm at both sides. Top view:
  brim 365 × 415 mm, crown a teardrop pointing to -Y. Hidden: the crown's
  inside (Solidify gives it), the brim's underside (Solidify), the band all
  the way around behind the crown.

## Parts
| part | primitive, size (mm), vertices | at (mm) | on / parent | collection, material |
|---|---|---|---|---|
| `Chapéu` | cylinder 177 × 212 × 132, 12 vertices, whole (D-061); cap ring + 3×3 grid (D-062) | (0, 0, 0) | none (main) | asset collection (start_part's), `Palha` |
| `Chapéu Fita` | cylinder 181 × 216 × 9, 12 vertices, both caps deleted: a 12-face strip | (0, 0, 0.5) | parent `Chapéu` | parent's, `Fita Preta` |
| `Chapéu Fivela` | cube 11 × 3 × 14, mirror X (half kept, X-) | (65, 77.5, 0.5), rotation Z 130° | parent `Chapéu Fita` | parent's, `Metal` |
| `Chapéu Fita Ponta` | cube 8 × 149 × 1.2, mirror X, 3 bisects along d | (101.5, 11.5, 0.5), rotation Z 26.7° | parent `Chapéu Fita` | parent's, `Fita Preta` |

Cage sizes are larger than the result: Subdivision pulls a 12-gon ring in to
0.966 of its radius, so 177 × 212 cage gives the 171 × 205 crown, and the
brim edge cage 394 × 428 gives 381 × 415 flat.

## Stack
- `Chapéu`: Subdivision (Levels Viewport 1; a 12-side cage needs it for a
  round crown, D-053, D-033) > Solidify (thickness 2.5 mm, offset -1 inward
  and under so the cage is the outer and top surface, use_even_offset on;
  thickness for a game, D-025; after Subdivision, slot 5). No Mirror: a
  cylinder is modeled whole (D-061). Crease 1.0 on the crown-brim ring
  (sharp fold, D-021).
- `Chapéu Fita`: Subdivision (Levels Viewport 1, so its 12 sides follow the
  crown's 24 evaluated sides). No Solidify: its inside lies on the crown and
  is never seen; its outside is the only visible side (D-025 asks volume for
  a part seen from both sides).
- `Chapéu Fivela`: Mirror X (clipping, merge 0.1 mm, D-054, from
  start_part). No Subdivision (subdivision=0): a flat plate at 11 mm.
- `Chapéu Fita Ponta`: Mirror X (same). No Subdivision; it is a thin box
  (its own volume, D-025).
- Smooth by Angle: not added (not an `add` type; see Risks).

## Commands
All through `import fofuxo_cage` in the AI's own Blender (`launcher.py`),
on a copy saved as `models/tasks/chapeu-cowboy/ai/P1/P1.blend`, never
`start.blend`.

Stage 0, round and reference
1. `bpy.ops.wm.save_as_mainfile(filepath=".../ai/P1/P1.blend")` after opening `start.blend`: the run's own file.
2. `fofuxo_cage.round_start("P1 build", plan="models/tasks/chapeu-cowboy/ai/P1/plan.md")`: accepted.
3. `bpy.data.objects["Concept"].empty_display_size = 0.482`: the reference at 0.79 mm/px (D-035; plain bpy, see Risks).

Stage 1, crown cage
4. `fofuxo_cage.start_part("Chapéu", "cylinder", size=(177, 212, 132), vertices=12, at=(0, 0, 0))`: 12 sides, each cap a ring of 12 quads + a 3×3 grid; 54 faces.
5. `fofuxo_cage.edit("Chapéu", "mesh delete faces h<1")`: bottom cap gone, 33 faces, border = the base ring (12 edges).
6. `fofuxo_cage.edit("Chapéu", "mesh bisect all plane=h68", "mesh bisect all plane=h700")`: rings at 9 mm (band top) and 92 mm; 57 faces, all quads.
7. `fofuxo_cage.edit("Chapéu", "mesh resize h>650 w=93% d=95%")`: taper; top 165 × 201 mm cage.
   Check S1.

Stage 2, crease and front pinch
8. `fofuxo_cage.select("Chapéu", "h>990 w>250 w<750 d>250 d<750")`: preview, must name the 4 inner grid vertices of the top cap.
9. `fofuxo_cage.edit("Chapéu", "mesh resize h>990 w>250 w<750 d>250 d<750 w=45% d=140% around=selection", "mesh translate h>990 w>420 w<580 d>250 d<750 h=-32mm")`: the 4 vertices into a 23 × 90 mm line along d, 32 mm down: the crease trough.
10. `fofuxo_cage.edit("Chapéu", "mesh translate h>990 d<150 w>400 w<600 h=-18mm", "mesh translate h>990 d>850 w>400 w<600 h=-8mm")`: 2 vertices each (outer top ring and cap ring at -Y, then at +Y): the crease opens at the front, less at the back.
11. `fofuxo_cage.select("Chapéu", "d<200 h>650")`: preview, must name 9 vertices (3 front vertices of the 92 mm ring, of the top ring, of the cap ring).
12. `fofuxo_cage.edit("Chapéu", "mesh resize d<200 h>650 w=70% around=selection")`: front pinch, the front upper vertices from ±49 to ±34 mm.
   Check S2.

Stage 3, brim
13. `fofuxo_cage.edit("Chapéu", "mesh extrude_scale border w=134% d=128%", "mesh extrude_scale border w=166% d=158%")`: R1 237 × 271 mm (30 mm out), edge ring 394 × 428 mm; 81 faces, one border (the brim edge).
14. `fofuxo_cage.edit("Chapéu", "crease h<5 w>=0 w<=1000 d>=0 d<=1000 1.0")`: crease on the 12 base-ring edges only (R1 and edge vertices fall outside w or d 0..1000).
15. `fofuxo_cage.select("Chapéu", "w>1400 h<50")` and `("Chapéu", "w<-400 h<50")`: 3 edge vertices each (x ±197, ±170.6 mm).
16. `fofuxo_cage.edit("Chapéu", "mesh translate w>1400 h<50 h=+30mm", "mesh translate w>1550 h<400 h=+15mm", "mesh resize w>1400 h<400 w=94%")`: +X side curl: middle +45 mm, ±30° +30 mm, 12 mm in.
17. `fofuxo_cage.edit("Chapéu", "mesh translate w<-400 h<50 h=+30mm", "mesh translate w<-550 h<400 h=+15mm", "mesh resize w<-400 h<400 w=94%")`: -X side, the same.
18. `fofuxo_cage.edit("Chapéu", "mesh translate w>1050 w<1300 d>0 d<1000 h<50 h=+6mm", "mesh translate w<-50 w>-300 d>0 d<1000 h<50 h=+6mm")`: the 3 side vertices of R1 on each side up 6 mm, so the curl starts before the edge.
19. `fofuxo_cage.edit("Chapéu", "mesh translate d<-300 h<50 h=-12mm", "mesh translate d>1300 h<50 h=-8mm")`: 3 front edge vertices -12 mm, 3 back -8 mm.
   Check S3.

Stage 4, thickness
20. `fofuxo_cage.edit("Chapéu", "add SOLIDIFY", "set Solidify thickness 2.5mm", "set Solidify offset -1", "set Solidify use_even_offset on")`: stack Subdivision > Solidify; evaluated 324 × 2 + 24 rim = 672 faces.
   Check S4.

Stage 5, band
21. `fofuxo_cage.start_part("Chapéu Fita", "cylinder", size=(181, 216, 9), vertices=12, at=(0, 0, 0.5), parent="Chapéu")`: 12 sides, 54 faces.
22. `fofuxo_cage.edit("Chapéu Fita", "mesh delete faces h<1", "mesh delete faces h>999")`: a strip of 12 faces, two borders; evaluated 48.
   Check S5.

Stage 6, buckle and tail
23. `fofuxo_cage.start_part("Chapéu Fivela", "cube", size=(11, 3, 14), mirror="X", subdivision=0, at=(65, 77.5, 0.5), parent="Chapéu Fita")`: half box, 5 faces, evaluated 10.
24. `bpy.data.objects["Chapéu Fivela"].rotation_euler.z = math.radians(130)`: faces out of the band (D-014 pose; plain bpy).
25. `fofuxo_cage.start_part("Chapéu Fita Ponta", "cube", size=(8, 149, 1.2), mirror="X", subdivision=0, at=(101.5, 11.5, 0.5), parent="Chapéu Fita")`: half box, 5 faces.
26. `fofuxo_cage.edit("Chapéu Fita Ponta", "mesh bisect all plane=d250", "mesh bisect all plane=d500", "mesh bisect all plane=d750")`: 4 segments; 14 faces, evaluated 28.
27. `bpy.data.objects["Chapéu Fita Ponta"].rotation_euler.z = math.radians(26.7)`: the strap from the buckle (68, 78) to (135, -55) mm.
28. `fofuxo_cage.edit("Chapéu Fita Ponta", "mesh translate d<260 h=+9mm falloff=smooth radius=80mm")`: the free end rises 9 mm with the brim's curl.
   Check S6.

Stage 7, materials, look, save
29. Materials `Palha`, `Fita Preta`, `Metal` created and assigned in plain bpy (gap, see Risks).
30. `fofuxo_cage.views("Chapéu", ["front", "right", "top", "50,20"])` beside `concept.jpg`: final look (each object alone first in Local View, then together, D-042).
31. `bpy.ops.wm.save_mainfile()` on `P1.blend`; `fofuxo_cage.round_end(tokens=<session tokens>)`; `report.md` with the cost line.
   Check S7.

## Checks
- S1 (after 7): sync report `count` base f 57, all quads, no issues; `size`
  base 177 × 212 × 132 mm ±1. Measure only, no render.
- S2 (after 12): `fofuxo_cage.sections("Chapéu", "w", [500])` (the cut at
  the middle, along d): the top at the center 96-108 mm, the cut's height at
  the ridges (`profile("Chapéu", "front")`) 124-131 mm. One render:
  `views("Chapéu", ["front", "right", "top", "50,20"])`: a trough front to
  back, and from the top the front third of the crown at most 70% of the
  back third's width.
- S3 (after 19): sync `size` sub w 355-380, d 405-425 mm;
  `profile("Chapéu", "front")`: brim edge at the sides 38-48 mm above the
  crown base; `profile("Chapéu", "side")`: front edge -9 to -14 mm, back
  -5 to -10 mm; the first 25 mm of brim out of the crown within ±3 mm of the
  base plane. One render: the same 4 views.
- S4 (after 20): evaluated f 672 exactly; `sections("Chapéu", "h", [35])`:
  outer 171 × 205 mm ±4, so the inner opening (minus 2 × 2.5) is about
  166 × 200, 560-590 mm around. No render.
- S5 (after 22): `sections("Chapéu Fita", "h", [500])` 173-178 × 207-212 mm,
  i.e. 1.5-4 mm outside the crown's S4 section; evaluated f 48. One render:
  `views("Chapéu Fita", ["50,20", "front"])` (the parent drawn around it):
  no straw through the band.
- S6 (after 28): `Chapéu Fivela` evaluated f 10, `Chapéu Fita Ponta` f 28.
  One render: `views("Chapéu Fita Ponta", ["50,20", "right", "top"],
  context=["Chapéu"])`: the strap 0-3 mm above the brim along its length,
  never under it, its top end under the buckle.
- S7 (after 31): total evaluated faces 672 + 48 + 10 + 28 = 758, at most 800;
  every scale (1, 1, 1); no `ERROR` in the syncs; the "50,20" view next to the
  photo: crown height to brim width ratio 128/105 = 1.22 ±0.1.

## Budget
```budget
syncs 26
ops 40
renders 6
measures 10
minutes 30
```

## Risks
- Base values on a whole part: the plan assumes the frame stays the
  start_part size (w 177, d 212, h 132, "lo..hi", 0 at -X, -Y and the base)
  and that brim vertices read past 1000 or below 0. Every region op has a
  `select()` preview (steps 8, 11, 15); if the counts differ, rewrite the
  thresholds from the preview's values before running the op, and note it in
  Changes. The side thresholds (1400/1550, -400/-550) have 50+ permille of
  margin.
- `start_part` with `mirror="X"` and `subdivision=0`: the signature has
  both, but the README only documents `mirror="XY"` as default. If refused,
  start with the default and run `set Mirror use_axis X` and
  `remove Subdivision`.
- `at=` for a part with `parent=`: assumed world mm. If it is local to the
  parent, `Chapéu Fita` sits at 0.5 mm, so the offset is 0.5 mm in h only;
  check the buckle and strap positions in S6.
- Gaps, no whitelist call: saving the run's copy (step 1), the `Concept`
  empty's size (step 3),
  object rotation (steps 24, 27), materials (step 29), asset collection
  setup (`setup_asset` is not in the extension), Smooth by Angle (a node
  group, not an `add` type). All in plain bpy on object data, none touching
  a mesh; listed in the report as library gaps. If start_part leaves faces
  flat-shaded, the hat and band get `shade_smooth` in bpy (gap too).
- Band against the crown: Subdivision on an open strip (band) and on an
  interior ring (crown) do not pull in by the same amount. If S5 shows the
  crown through the band, raise the band's cage with
  `mesh resize all w=101% d=101%`; if it floats more than 4 mm, 99%. D-029
  says a part that sits on another starts from its faces (`mesh extract`);
  start_part was chosen because `extract` gives an object that needs a
  rename and a parent outside the whitelist. If the modeler prefers D-029,
  extract `faces h<100` before stage 3, then `mesh shrink_fatten all
  value=1.5mm`.
- 12 sides: the 24-side evaluated brim edge may show facets at 400 mm across
  (about 52 mm per segment). Going to 16 sides costs 672 → 896 faces on the
  hat alone, over budget; the fallback is to keep 12 and judge in S3.
- Crease trough: 4 grid vertices may give a dent too round. If S2 shows less
  than 20 mm depth, move them down 8 mm more and closer in w (`w=70%`), not
  more loops (D-045).
- Strap on a curled brim: a straight box posed by rotation may cross the brim
  between bisects. Fallback: `add SHRINKWRAP at first`, `set Shrinkwrap
  target Chapéu`, offset 0.8 mm, limited to a vertex group of the bottom
  vertices (`mesh vertex_group_assign h<500 group=Contato`) (D-026).
- Concept: a perspective photo, no orthographic sheet. Proportions are
  read at the crown's depth; the near brim is about 4% larger in the photo.

## Changes
