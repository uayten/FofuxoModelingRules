"""Topology ops: remove an edge loop, cut a new one.

    dissolve <edges>       remove the loop the edges belong to; the faces on
                           both sides merge, the loop's vertices go away
    cut <vA-vB> [N]        cut N new loops (default 1) across the edge ring
                           that holds edge vA-vB, halfway (evenly for N > 1)

Edges are named as for crease: vA-vB pairs, loop labels, plane-x/y/z, or
sharp (every edge marked sharp in Blender: the human can mark a loop there
and the AI dissolves it). Vertices that stay keep their ids; new ones get
fresh ids at the sync. A dissolve that would leave anything but quads is
refused before anything changes.
"""

import bmesh

from .topology import PLANE_TOL

SHARP_ATTR = "sharp_edge"


class MeshOpError(ValueError):
    pass


def _ids(mesh):
    from .mesh_io import ID_ATTR
    return [d.value for d in mesh.attributes[ID_ATTR].data]


def edge_indices(mesh, specs):
    """Indices of the mesh edges named by specs (see object_ops._edge_pairs)."""
    ids = _ids(mesh)
    wanted = {frozenset((a, b)) for kind, *rest in specs if kind == "pair" for a, b in [rest]}
    planes = [rest[0] for kind, *rest in specs if kind == "plane"]
    sharp = any(kind == "sharp" for kind, *_ in specs)
    sharp_attr = mesh.attributes.get(SHARP_ATTR) if sharp else None
    out = []
    for e in mesh.edges:
        a, b = e.vertices
        on_plane = any(abs(mesh.vertices[a].co[k]) < PLANE_TOL and abs(mesh.vertices[b].co[k]) < PLANE_TOL
                       for k in planes)
        marked = sharp_attr is not None and sharp_attr.data[e.index].value
        if on_plane or marked or frozenset((ids[a], ids[b])) in wanted:
            out.append(e.index)
    return out


def _dissolve_bm(mesh, specs):
    edges = set(edge_indices(mesh, specs))
    if not edges:
        raise MeshOpError("no edges matched")
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()
    before = len(bm.verts)
    chosen = {bm.edges[i] for i in edges}
    # A loop that turns at a pole leaves the pole one edge: take that spoke too,
    # so the pole goes away with the loop.
    for v in {v for e in chosen for v in e.verts}:
        rest = [e for e in v.link_edges if e not in chosen]
        if len(rest) == 1 and not v.is_boundary:
            chosen.add(rest[0])
    loop_verts = {v for e in chosen for v in e.verts}
    bmesh.ops.dissolve_edges(bm, edges=list(chosen), use_verts=True, use_face_split=False)
    # Loop vertices left with two edges carry nothing (inside, or at the end of
    # the loop on a mirror plane): dissolve them too.
    leftovers = [v for v in loop_verts if v.is_valid and len(v.link_edges) == 2]
    if leftovers:
        bmesh.ops.dissolve_verts(bm, verts=leftovers)
    bad = [f for f in bm.faces if len(f.verts) != 4]
    return bm, before - len(bm.verts), len(bad)


def check_dissolve(mesh, specs):
    bm, removed, bad = _dissolve_bm(mesh, specs)
    bm.free()
    if bad:
        raise MeshOpError(f"would leave {bad} faces that are not quads; dissolve a whole loop")
    return removed


def dissolve(obj, specs):
    bm, removed, bad = _dissolve_bm(obj.data, specs)
    try:
        if bad:
            raise MeshOpError(f"would leave {bad} faces that are not quads")
        bm.to_mesh(obj.data)
    finally:
        bm.free()
    obj.data.update()
    return f"{removed} vertices removed"


def _ring(edge):
    """The edge ring through edge: across each quad to the opposite edge, both ways."""
    ring = [edge]
    for first in list(edge.link_faces)[:2]:
        cur, f = edge, first
        while f is not None and len(f.verts) == 4:
            loops = list(f.loops)
            k = next(i for i, lp in enumerate(loops) if lp.edge is cur)
            nxt = loops[(k + 2) % 4].edge
            if nxt is edge:
                return ring  # a closed ring
            if nxt in ring:
                break
            ring.append(nxt)
            others = [g for g in nxt.link_faces if g is not f]
            f = others[0] if others else None
            cur = nxt
    return ring


def cut(obj, pair, cuts=1):
    ids = _ids(obj.data)
    index = {vid: i for i, vid in enumerate(ids)}
    a, b = pair
    if a not in index or b not in index:
        raise MeshOpError(f"no vertex v{a if a not in index else b}")
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        va, vb = bm.verts[index[a]], bm.verts[index[b]]
        edge = next((e for e in va.link_edges if e.other_vert(va) is vb), None)
        if edge is None:
            raise MeshOpError(f"v{a} and v{b} share no edge")
        ring = _ring(edge)
        before = len(bm.verts)
        bmesh.ops.subdivide_edges(bm, edges=ring, cuts=cuts, use_grid_fill=True)
        bm.to_mesh(obj.data)
        added = len(bm.verts) - before
    finally:
        bm.free()
    obj.data.update()
    return f"{added} vertices added across {len(ring)} edges"


def check_cut(mesh, pair):
    ids = _ids(mesh)
    index = {vid: i for i, vid in enumerate(ids)}
    a, b = pair
    for v in (a, b):
        if v not in index:
            raise MeshOpError(f"no vertex v{v}")
    ea = {frozenset(e.vertices) for e in mesh.edges}
    if frozenset((index[a], index[b])) not in ea:
        raise MeshOpError(f"v{a} and v{b} share no edge")
