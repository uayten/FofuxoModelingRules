# Operator card

One line per checked Blender operator. Read parameter meanings only for the operation you need with
`mesh_help("translate", compact=False)`. Sizes use mm, m or frame percentages as documented.

## Contents

- [Operations](#operations)
- [Selections](#selections)
- [Other calls](#other-calls)

## Operations

| Operation | Parameters | Purpose |
|---|---|---|
| `dissolve_edges` | use_verts, use_face_split | remove the edges; the faces on both sides merge |
| `dissolve_verts` | use_face_split, use_boundary_tear | remove the vertices; their faces merge |
| `delete_edgeloop` | use_face_split | delete an edge loop, sliding its neighbours together |
| `loopcut_slide` | number_cuts, smoothness, falloff, slide | cut new loops across the ring of the first edge named |
| `subdivide_edgering` | number_cuts, smoothness, interpolation | cut loops across a selected edge ring |
| `vertices_smooth` | factor, repeat, xaxis, yaxis, zaxis | move the vertices toward their neighbours' average |
| `translate` | w, d, h, falloff, radius, connected | move the selection along the frame axes, optionally with proportional editing (the neighbours follow with a falloff) |
| `edge_slide` | factor, even, flipped, clamp | slide an edge loop along the faces beside it: the loop moves, the surface it rests on stays |
| `vert_slide` | factor, even, flipped, clamp | slide vertices along one of their edges |
| `shrink_fatten` | value, even, falloff, radius, connected | move the selection along its normals: inflate (+) or thin (-) a region evenly |
| `push_pull` | value, falloff, radius, connected | move the selection toward (-) or away from (+) its center |
| `tosphere` | factor, falloff, radius, connected | round the selection toward a sphere around its center |
| `looptools_circle` | fit, flatten, influence, radius, regular, lock_x, lock_y, lock_z | make a closed loop round (LoopTools): a round section; a loop cut by a mirror plane is not a circle |
| `looptools_relax` | iterations, interpolation, regular | even out a loop's curvature (LoopTools) |
| `looptools_space` | influence, interpolation, lock_x, lock_y, lock_z | space a loop's vertices evenly along it (LoopTools) |
| `symmetrize` | direction, threshold | copy one side of the mesh onto the other (a part modeled whole) |
| `symmetry_snap` | direction, threshold, factor, use_center | snap vertices to their mirror counterparts |
| `offset_edge_loops_slide` | cap, slide | two new loops on either side of the selected one, slid apart (a loop that ends on a mirror plane leaves triangles: refused) |
| `space_edge_loops_evenly` | factor, interpolation, lock | space parallel loops evenly between the outer two: select the rings across them, two or more deep (ring vA-vB ring vB-vC), not the loops |
| `dissolve_limited` | angle_limit, use_dissolve_boundaries, delimit | dissolve edges and vertices flatter than an angle: a lighter cage where it carries no shape (D-045) |
| `unsubdivide` | iterations | undo a grid's subdivisions |
| `edge_collapse` | none | collapse each edge to one vertex at its middle |
| `merge` | type | merge the selected vertices into one |
| `remove_doubles` | threshold, use_centroid, use_unselected | merge vertices closer than a distance (Merge by Distance) |
| `edge_rotate` | use_ccw | turn an edge inside its two faces (flow, poles) |
| `tris_convert_to_quads` | face_threshold, shape_threshold | join triangles into quads |
| `bridge_edge_loops` | number_cuts, interpolation, smoothness, twist_offset, use_merge, merge_factor | join two open edge loops with faces (list their edges: a loop walker on a border takes the whole border) |
| `fill_grid` | span, offset, use_interp_simple | fill a hole with a grid of quads from its border edges, turned to run through the loop's extreme vertices on X and Y (it could be cut in quarters and mirrored) unless an offset is given |
| `delete` | type | delete the selection (a hole left for bridge_edge_loops or fill_grid) |
| `edge_face_add` | none | a face from the selected vertices (the F key) |
| `normals_make_consistent` | inside | turn every face outward (the sync warns when the result is inside out) |
| `flip_normals` | none | flip the selected faces |
| `vertex_group_assign` | group, weight | put the selected vertices in a vertex group (made if missing): for Shrinkwrap, Displace, a later rig |
| `vertex_group_remove_from` | group | take the selected vertices out of a vertex group |
| `unwrap` | method, margin | unwrap the selected faces along their seams (mark_seam first, e.g. mesh mark_seam sharp) |
| `mark_seam` | clear | mark the edges as seams |
| `mark_sharp` | clear | mark the edges sharp |
| `resize` | w, d, h, around, falloff, radius, connected | scale the selection along the frame axes around the object's origin (the mirror planes' meeting point): a ring pulled out into a brim, a part made wider |
| `rotate` | angle, axis, around, falloff, radius, connected | turn the selection around a frame axis through its own middle: a ring tilted to follow a horn's curve (R) |
| `extrude_scale` | w, d, h | extrude the selection and scale the new part around the object's origin: a loop closing toward the center (E, S, Shift+Z), a flare |
| `extrude_region_shrink_fatten` | value, even | extrude the selected faces out along their normals (a brim, a rim, a thickness) |
| `extrude_region_move` | w, d, h | extrude the selection as one region and move it along the frame axes |
| `extrude_context_move` | w, d, h | extrude what is selected as it is (faces, edges or vertices) and move it |
| `inset` | thickness, depth, use_even_offset, use_individual, use_boundary | inset the selected faces: a ring of new faces inside their border |
| `spin` | steps, angle, axis | sweep the selection around a frame axis through the object's origin |
| `screw` | steps, turns, axis | sweep the selection around a frame axis, rising each turn |
| `bevel` | width, segments, affect, profile | bevel edges (or vertices): the edge becomes a strip of faces |
| `bisect` | plane, clear, fill | cut the selection with a plane across a frame axis |
| `separate` | type | move the selection into a new object (by selection, material or loose parts) |
| `extract` | none | copy the selection into a new object, the original kept: a part that sits on another (D-029); then add SHRINKWRAP and set its target |

## Selections

`vN`, `vA-vB`, `L1`, `region Upper`, `loop vA-vB`, `ring vA-vB`,
`path vA vB`, `faces vA vB vC vD`, `h>500`, `faces h>500`, `border`,
`plane-x/y/z`, `sharp`, `seam`, `crease`, `all`.

Preview with `select(name, selection)`. Quote a region name containing spaces.

## Other calls

See [Session tools](README.md#session-tools) for absolute positions, regions, Workbench,
recordings, examples, cost receipts, handover and stage checkpoints.
