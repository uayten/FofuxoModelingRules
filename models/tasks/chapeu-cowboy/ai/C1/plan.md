# Plan: Chapéu (straw cowboy hat, run C1, built in the conversation)

## Read
- Scale: no body; the head opening anchors it: an adult oval about 200 (d) ×
  165 (w) mm. The rest as proportions of the photo, not pixels (D-066).
- Other references: none. The photo shows the crown's crease and front
  pinch, the brim's curl and the band; the hidden back and underside mirror
  what is seen.
- The form: crown about 125 mm tall, a little narrower at the top, a teardrop
  from above (front pinched high up), a crease front to back, deeper at the
  front. Brim about as wide as the crown is tall (100 mm), flat by the
  crown, curling up at the sides almost to the band's height, pointed and
  dipping a little at the front and back. A sharp fold where crown meets
  brim. Band 10 mm at the crown's base; a buckle on the wearer's left side,
  a tail from it lying on the brim.
- Dropped to texture: vent eyelets, weave, the brim's bound edge.

## Parts
| part | primitive, size (mm), vertices | at (mm) | on / parent | collection, material |
|---|---|---|---|---|
| `Chapéu` | cylinder 170 × 205 × 125, 12 vertices, whole | (0, 0, 0) | none | `Chapéu`, `Palha` |
| `Chapéu Fita` | extracted from the crown's band row | (0, 0, 0) | parent `Chapéu` | `Chapéu`, `Fita` |
| `Chapéu Broche` | cube 12 × 4 × 14, mirror X | on the band, left side | parent `Chapéu Fita` | `Chapéu`, `Metal` |
| `Chapéu Fita Rabo` | cube 8 × 120 × 1.5, mirror X | from the buckle onto the brim | parent `Chapéu Fita` | `Chapéu`, `Fita` |

Route: the band is extracted from the crown's faces, so it sits on it from the
start; the other route is a new cylinder (D-070). The modeler chose this one.

## Stack
- `Chapéu`: Subdivision 1 > Solidify 2 mm (offset -1, even). Crease 1 on the
  crown-brim ring.
- `Chapéu Fita`: Subdivision 1 (as the hat) > Solidify 1.5 mm, outward.
- `Chapéu Broche`, `Chapéu Fita Rabo`: Mirror X > Subdivision 1 (D-068).

## Commands
Stage 1, crown and brim
1. `start_part("Chapéu", "cylinder", size=(170, 205, 125), vertices=12)`
2. `edit("Chapéu", "mesh delete faces h<1")`: the bottom cap gone.
3. `edit("Chapéu", "mesh bisect all plane=h80")`: the band's top loop (10 mm).
4. `edit("Chapéu", "mesh extrude_scale border w=135% d=129%", "mesh extrude_scale border w=160% d=150%")`: brim ring 30 mm out and the edge about 100 mm out.
5. `crease` on the crown-brim ring, 1.0.
   Check: render 1.
Stage 2, brim shape
6. `mesh translate` the edge's side vertices up with `falloff=smooth`, front and back down, sides in.
   Check: render 2. A ring between the two only if the curl shows a kink.
Stage 3, crown shape
7. `mesh resize` the top ring narrower at the sides; front top vertices pinched; the cap's middle down for the crease.
   Check: render 3. A loop near the top only if the pinch does not hold.
Stage 4, band, buckle, tail
8. `mesh extract` the band row; rename, parent, Solidify.
9. `start_part` the buckle and the tail; pose; Subdivision.
   Check: render 4, everything together.
Stage 5, thickness and close
10. `add SOLIDIFY` on the hat; materials; count; save; `round_end`.

## Checks
- After 4: base faces about 69, all quads; brim edge about 360-400 mm across.
- Renders after stages 1, 2, 3, 4 (D-069); stage 5 by measures only.
- End: evaluated faces at most 800, head opening 560-600 mm around.

## Budget
```budget
syncs 25
ops 35
renders 6
measures 40
minutes 30
```

## Risks
- Region thresholds on a part that grows past its frame: `select()` first.
- `extract` leaves an object that needs a rename and a parent (plain bpy).
- Materials, collection, rotations of the small parts: plain bpy (gaps).

## Changes
- Stage 1-2: the budget's measures (8) were too low: every `select()`
  preview counts as one (24 by stage 2). Budget raised to measures 40.
- Stage 2: `resize ... around=selection` pulls the three side vertices
  toward their own middle, not toward the crown; the sides' move inward needs
  `translate w=`. The falloff radius of 110 mm also lifted the crown's base
  0.8 mm (proportional editing works by distance, not along the brim).
- Stage 2, the modeler's review: one more brim ring (`loopcut_slide ring
  v71-v83`, L3 between the flat ring and the edge) and the curve made sharper
  near the bend: the flat ring's sides down to about 2 mm, the new ring's
  sides to 9 mm, the edge's sides up to 46 mm and 7.6 mm in. Values written
  in the cage text, one sync.
- Stage 3: the crown's base ring and the band ring had been lifted by the
  brim's falloff; set back to h 0 and h 80. Taper, front pinch and crease
  written in the cage text from one rule (width factor 0.70 at the front to
  0.93 at the back; crease 26 mm deep at the front to 14 mm at the back,
  fading 32 mm either side of the middle; the outer top ring at 60%). The
  wall's single span made the pinch linear from the band: a loop at h 600
  (75 mm) added, as the plan allowed, kept nearly full width.
- Stage 3, the modeler's review: no face count to worry about; the hat goes
  to half and Mirror now (D-071). The cap's grid (a diamond off the plane)
  was refilled with `fill_grid span=2 offset=11` so its middle row runs on
  x = 0, then `delete faces w>=500` (four grid faces with vertices a hair
  under 500 stayed and went with a `faces` list) and `add MIRROR`.
  `add MIRROR` put Mirror last, as Blender adds every new modifier; the line
  should have been `add MIRROR at first` (or `before Subdivision`). Moved
  with `modifier_move_to_index` in plain bpy.
- Stage 3, corrections: crown 10 mm lower, front pinch to about 56% at the
  top and 90% at mid wall, crease 6 mm deeper at the front, the shoulders
  5 mm up, the brim 10 mm longer at the front and back.
- Renders: the sheet's panels are too small to judge a crown; a Workbench
  render (a temporary camera, 3/4, front, side, top) to `renders/`.
- Stage 2 again (brim): the side edge up 20 mm more and 4 mm in, the bend
  ring up 8 mm; the flat ring back to the base height at the front and back,
  the bend ring there at -2 mm: the drop is the edge's alone.
- Stage 3, the modeler's review: three dents on the top, the middle crease
  and one half-oval dent on each side (the far one hidden in the photo,
  deduced from symmetry). Missed in the reading: the side dent. A loop
  between the mid wall and the top ring (`loopcut_slide ring v113-v19`),
  its vertex at the front side (v128) pushed in about 18 mm, its neighbours
  and the top ring above less. Faces set smooth (plain bpy, a gap).
- Stage 3 rebuilt, the modeler's method: the top is three dents (a middle
  one like a cylinder's boolean, two side ones like an egg's) parted by two
  mountains. Copy before it: `C1_top_v1.blend`. Done so far: `delete faces
  h>500` (the top down to the mid wall ring), the ring extruded 40 mm up as
  the rim (`extrude_region_move h>500 w>-100`; `h>500` alone also took the
  brim's side tip, v89), the rim extruded inward as the mountain
  (`extrude_scale ... w=55% d=85%`) and raised 12 mm. The middle stays open
  between the mountain and the plane.
- Top, the modeler's next steps: face on v125 v126 v128 v129 (the mountain
  top, front to back; v127 left out, on the side dent's side); `bisect
  plane=d500`, `delete faces d>=495` and `add MIRROR at first` + `set
  Mirror.001 use_axis Y`: a temporary Y mirror, to apply once the side dent
  is good; a loop between v127 and v126 (`loopcut_slide ring v126-v127`,
  down the whole crown and brim), the face v126 v139 v127 v130 closing the
  gap, v127 and v139 10 mm out and 12 mm down.
- Top, the modeler's edit in the review (absorbed): Ctrl+R on v125-v126 (a
  loop from the brim up to the mountain), Delete > Edges on v126-v130 (the
  patch and half the mountain top gone: the side dent's hole), two cuts on
  v125-v131 (the ridge now v125 v147 v150 v131, the inner row v146 v151
  v130 v148) and the ridge raised 13-19 mm, highest on the Y plane. The AI
  had read "delete" as dissolve (D-073).
- Tooling during the round: the sheet labels only what mesh attributes ask
  (fofuxo_show_vertex, fofuxo_loop, fofuxo_show_face, in levels); collect()
  saves and closes the review Blender (D-072).
- The side dent (egg) and the middle dent built by the modeler in the review,
  watched: the egg as a center quad, a ring of quads around it and a ring to
  the mountain; the middle dent as the ridge extruded in place and pulled to
  the X plane, holes closed with F2, then about 10 minutes of small moves.
  The full operator log (343 lines) is `C1.cage/ops_central.json`; the
  render `renders/sheet_central.png`.
