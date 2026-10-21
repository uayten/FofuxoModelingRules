"""Weld the small leaf into the stem: snap the leaf's closest border vertices
onto the stem's vertices and merge them. No modifier is applied.

The leaf (12 v) sits at the tip of the stem (51 v); they overlap without
sharing a vertex. Welding the two closest pairs makes the mesh one connected
surface at the junction, which is where the modeler then cleans the faces.
"""
import bpy
import bmesh
import mathutils
import llm_modeling_bridge as b

OBJ = "Plane.001"
PAIRS = 3
TOL = 1e-4

obj = bpy.data.objects[OBJ]
me = obj.data
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()

# islands
seen = set()
islands = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack = [v]
    seen.add(v.index)
    comp = []
    while stack:
        cur = stack.pop()
        comp.append(cur)
        for e in cur.link_edges:
            other = e.other_vert(cur)
            if other.index not in seen:
                seen.add(other.index)
                stack.append(other)
    islands.append(comp)
islands.sort(key=len)
leaf, stem = islands[0], islands[1]

kd = mathutils.kdtree.KDTree(len(stem))
for i, v in enumerate(stem):
    kd.insert(v.co, i)
kd.balance()

candidates = []
for v in leaf:
    co, i, dist = kd.find(v.co)
    candidates.append((dist, v, stem[i]))
candidates.sort(key=lambda c: c[0])

welded = []
for dist, src, dst in candidates[:PAIRS]:
    if dist > 0.02:
        continue
    welded.append({"dist": round(dist, 5), "from": [round(c, 4) for c in src.co],
                   "to": [round(c, 4) for c in dst.co]})
    src.co = dst.co.copy()

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=TOL)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=TOL)
bm.to_mesh(me)
bm.free()
me.update()

# connectivity + non-manifold check
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
seen = set()
components = 0
for v in bm.verts:
    if v.index in seen:
        continue
    components += 1
    stack = [v]
    seen.add(v.index)
    while stack:
        cur = stack.pop()
        for e in cur.link_edges:
            other = e.other_vert(cur)
            if other.index not in seen:
                seen.add(other.index)
                stack.append(other)
non_manifold = sum(1 for e in bm.edges if len(e.link_faces) > 2)
boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
bm.free()

bpy.ops.wm.save_mainfile()
result = {"welded": welded, "verts": len(me.vertices), "faces": len(me.polygons),
          "components": components, "non_manifold_edges": non_manifold,
          "boundary_edges": boundary}
