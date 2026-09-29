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
