"""Checks run on every sync. Each issue: {level, code, msg, verts}."""

import bmesh

from . import topology

MAX_VERTS = 255
MAX_LISTED = 20


def _issue(level, code, msg, vids=()):
    vids = sorted(vids)
    listed = [f"v{v}" for v in vids[:MAX_LISTED]]
    if len(vids) > MAX_LISTED:
        listed.append(f"+{len(vids) - MAX_LISTED}")
    return {"level": level, "code": code, "msg": msg, "verts": listed}


def check_positions(co_by_id, mirror, sides):
    """Plane and side rules for positions (m) about to be written."""
    issues = []
    for a, merge in mirror.items():
        k = topology.AXES.index(a)
        side = sides.get(a)
        wrong = [vid for vid, co in co_by_id.items()
                 if (side == "+" and co[k] < -topology.PLANE_TOL) or (side == "-" and co[k] > topology.PLANE_TOL)]
        if wrong:
            issues.append(_issue("ERROR", "wrong_side",
                                 f"crosses the {a} mirror plane to the mirrored side ({a}{side} is kept)", wrong))
        near = [vid for vid, co in co_by_id.items() if topology.PLANE_TOL <= abs(co[k]) <= merge]
        if near:
            issues.append(_issue("WARN", "near_plane",
                                 f"off the {a} plane but within the Mirror merge distance ({merge * 1000:.2f} mm): will weld",
                                 near))
    return issues


def check_mesh(obj, ids, mirror, sides, has_subsurf):
    mesh = obj.data
    issues = []
    if len(mesh.vertices) > MAX_VERTS:
        issues.append(_issue("ERROR", "too_many_verts", f"{len(mesh.vertices)} vertices, the limit is {MAX_VERTS}"))
    issues += check_positions({vid: tuple(v.co) for vid, v in zip(ids, mesh.vertices)}, mirror, sides)

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        non_quad = [ids[v.index] for f in bm.faces if len(f.verts) != 4 for v in f.verts]
        if non_quad:
            issues.append(_issue("ERROR" if has_subsurf else "WARN", "non_quad",
                                 "triangles or n-gons" + (" under Subdivision" if has_subsurf else ""), set(non_quad)))
        loose_v = [ids[v.index] for v in bm.verts if not v.link_edges]
        loose_e = [ids[v.index] for e in bm.edges if not e.link_faces for v in e.verts]
        if loose_v or loose_e:
            issues.append(_issue("ERROR", "loose", "vertices or edges without faces", set(loose_v + loose_e)))
        flipped = [ids[v.index] for e in bm.edges if len(e.link_loops) == 2
                   and e.link_loops[0].vert.index == e.link_loops[1].vert.index for v in e.verts]
        if flipped:
            issues.append(_issue("ERROR", "flipped", "neighbour faces with opposite winding", set(flipped)))
        non_manifold = [ids[v.index] for e in bm.edges if len(e.link_faces) > 2 for v in e.verts]
        if non_manifold:
            issues.append(_issue("ERROR", "non_manifold", "edges with more than two faces", set(non_manifold)))
        holes = []
        for e in bm.edges:
            if not e.is_boundary:
                continue
            shared = set(topology.on_planes(e.verts[0].co, mirror)) & set(topology.on_planes(e.verts[1].co, mirror))
            if not shared:
                holes += [ids[v.index] for v in e.verts]
        if holes:
            issues.append(_issue("WARN", "open_edge", "open edges off the mirror planes (a hole)", set(holes)))
    finally:
        bm.free()
    return issues


DIP_TOL = 1e-4  # m: 0.1 mm of concavity before a dip counts


def _reflections(co, planes):
    """co and its reflections across every subset of the given plane axes."""
    out = [tuple(co)]
    for a in planes:
        k = topology.AXES.index(a)
        out += [tuple(-c if i == k else c for i, c in enumerate(p)) for p in out]
    return out


def check_editability(obj, ids, depsgraph, mirror):
    """Vertices where the cage dips inward while the result bulges outward.

    Such a vertex sits inside the average of its neighbours (mirror copies
    included) although the surface over it is convex: dragging it moves the
    surface in a way that is hard to predict, which makes the cage hard to
    edit (D-043). Concave cage over a concave surface (a groove) is fine.
    Needs the stack to be Mirror and Subdivision (base vertex i is evaluated
    vertex i); otherwise returns no issue.
    """
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        n = len(obj.data.vertices)
        if len(me.vertices) < n:
            return []
        sub = [tuple(me.vertices[i].co) for i in range(n)]
        nor = [tuple(me.vertices[i].normal) for i in range(n)]
    finally:
        ev.to_mesh_clear()
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        dips = []
        for v in bm.verts:
            planes = topology.on_planes(v.co, mirror)
            nb_base, nb_sub = [], []
            for e in v.link_edges:
                u = e.other_vert(v)
                own = [a for a in planes if a not in topology.on_planes(u.co, mirror)]
                nb_base += _reflections(u.co, own)
                nb_sub += _reflections(sub[u.index], own)
            if not nb_base:
                continue
            i = v.index
            lap_c = [sum(p[k] for p in nb_base) / len(nb_base) - v.co[k] for k in range(3)]
            lap_s = [sum(p[k] for p in nb_sub) / len(nb_sub) - sub[i][k] for k in range(3)]
            conc_c = sum(a * b for a, b in zip(lap_c, nor[i]))
            conc_s = sum(a * b for a, b in zip(lap_s, nor[i]))
            if conc_c > DIP_TOL and conc_s < -DIP_TOL:
                dips.append(ids[i])
    finally:
        bm.free()
    if not dips:
        return []
    return [_issue("WARN", "cage_dips", "the cage dips inward under a convex surface: hard to edit "
                                        "(move the vertex out and let its neighbours carry the shape)", dips)]
