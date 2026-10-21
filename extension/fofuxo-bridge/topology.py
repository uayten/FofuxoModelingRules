"""Edge loops, vertex grouping and per-vertex flags on the base mesh (bmesh)."""

import math

import numpy as np

PLANE_TOL = 1e-6  # m; a coordinate this close to 0 lies on the mirror plane
AXES = "XYZ"


def on_planes(co, mirror_axes):
    """Mirror axes whose plane the point lies on."""
    return tuple(a for a in mirror_axes if abs(co[AXES.index(a)]) < PLANE_TOL)


def _next_edge(edge, vert):
    """The edge that continues an edge loop through vert, or None where the loop ends."""
    if vert.is_boundary:
        # Along a boundary (a mirror plane) the loop goes on through valence 3.
        if not edge.is_boundary or len(vert.link_edges) != 3:
            return None
        nxt = [e for e in vert.link_edges if e.index != edge.index and e.is_boundary]
        return nxt[0] if len(nxt) == 1 else None
    if len(vert.link_edges) != 4:
        return None
    faces = {f.index for f in edge.link_faces}
    nxt = [e for e in vert.link_edges
           if e.index != edge.index and not ({f.index for f in e.link_faces} & faces)]
    return nxt[0] if len(nxt) == 1 else None


def edge_loops(bm):
    """Every edge loop as a list of vertex indices. Each edge belongs to one loop."""
    used = set()
    loops = []
    for e0 in bm.edges:
        if e0.index in used:
            continue
        used.add(e0.index)
        verts = [e0.verts[0], e0.verts[1]]
        edge, vert, closed = e0, e0.verts[1], False
        while True:
            nxt = _next_edge(edge, vert)
            if nxt is None:
                break
            if nxt.index == e0.index:
                closed = True
                break
            if nxt.index in used:
                break
            used.add(nxt.index)
            vert = nxt.other_vert(vert)
            edge = nxt
            verts.append(vert)
        if closed:
            if verts[-1].index == verts[0].index:
                verts.pop()
        else:
            edge, vert = e0, e0.verts[0]
            while True:
                nxt = _next_edge(edge, vert)
                if nxt is None or nxt.index in used:
                    break
                used.add(nxt.index)
                vert = nxt.other_vert(vert)
                edge = nxt
                verts.insert(0, vert)
        loops.append([v.index for v in verts])
    return loops


def group_vertices(loops, vert_count, rings=()):
    """Cover every vertex once with pieces of edge loops, longest first.

    rings (from rings(), a whole part only) come first, whole and in their
    order, so a cylinder's labels are its rings and not the longer lines that
    run along it through a grid cap.
    Returns (loop_pieces, rest): rest holds the vertices no piece covers.
    """
    taken = [False] * vert_count
    groups = []
    for loop in rings:
        if not any(taken[i] for i in loop):
            for i in loop:
                taken[i] = True
            groups.append(list(loop))
    while True:
        best = None
        for loop in loops:
            run, cur = [], []
            for i in loop + [None]:
                if i is None or taken[i] or i in cur:  # a loop can pass a pole twice
                    if len(cur) > len(run):
                        run = cur
                    cur = [] if i is None or taken[i] else [i]
                else:
                    cur.append(i)
            if len(run) >= 2 and (best is None or len(run) > len(best)):
                best = run
        if best is None:
            break
        for i in best:
            taken[i] = True
        groups.append(best)
    return groups, [i for i in range(vert_count) if not taken[i]]


def mirrored_valence(vert, mirror_axes):
    """Valence the vertex will have once the Mirror modifier runs.

    An edge lying in k_e of the k mirror planes the vertex sits on is copied
    2 ** (k - k_e) times around it.
    """
    planes = on_planes(vert.co, mirror_axes)
    total = 0
    for e in vert.link_edges:
        other = e.other_vert(vert)
        shared = sum(1 for a in planes if abs(other.co[AXES.index(a)]) < PLANE_TOL)
        total += 2 ** (len(planes) - shared)
    return total


def vertex_flags(vert, mirror_axes):
    flags = list(on_planes(vert.co, mirror_axes))
    valence = mirrored_valence(vert, mirror_axes)
    if vert.link_faces and valence != 4:
        flags.append(f"pole{valence}")
    return tuple(flags)


RING_MIN = 6  # vertices: a shorter closed loop is not read as a ring
RING_TURN = math.radians(70)  # the largest turn from one edge to the next along a ring
RING_FLAT = 0.2  # the farthest a ring's vertex may lie from its plane, in ring radii


def _ring_from(a0, b0, nbrs, co):
    """The closed loop that starts along a0-b0 and at each vertex takes the edge
    that turns least (a grid fill's valence-3 corners do not stop it), or None."""
    loop, prev, cur = [a0], a0, b0
    while cur != a0 and len(loop) <= 256:
        d0 = co[cur] - co[prev]
        best, best_ang = None, RING_TURN
        for nxt in nbrs[cur]:
            if nxt == prev:
                continue
            d1 = co[nxt] - co[cur]
            den = np.linalg.norm(d0) * np.linalg.norm(d1)
            if den < 1e-12:
                continue
            ang = math.acos(max(-1.0, min(1.0, float(d0 @ d1) / den)))
            if ang < best_ang:
                best, best_ang = nxt, ang
        if best is None or best in loop[1:]:
            return None
        loop.append(cur)
        prev, cur = cur, best
    return loop if cur == a0 and len(loop) >= RING_MIN else None


def _once_around(pts):
    """The loop's plane normal if it lies flat and goes once around, else None."""
    c = pts - pts.mean(axis=0)
    _, _, vt = np.linalg.svd(c)
    normal = vt[2]
    radius = np.linalg.norm(c, axis=1).mean()
    if radius < 1e-9 or np.abs(c @ normal).max() > RING_FLAT * radius:
        return None
    u, v = c @ vt[0], c @ vt[1]
    ang = np.arctan2(v, u)
    turn = np.diff(np.append(ang, ang[0]))
    turn = (turn + math.pi) % (2 * math.pi) - math.pi
    return normal if abs(abs(turn.sum()) - 2 * math.pi) < 0.3 else None


def rings(edges, co):
    """Cylinder loops: closed loops that lie in a plane (any tilt) and go once
    around. edges: vertex index pairs; co: positions (n x 3).
    Returns [(vertex indices in order, axis index or None)], the axis when the
    plane lies across X, Y or Z (within 0.1 mm), in order along the part.
    Where candidates share vertices (the lines over a horn's tip cross every
    ring) the ones that cross the fewest others are kept."""
    co = np.asarray(co, dtype=float)
    nbrs = [[] for _ in range(len(co))]
    for a, b in edges:
        nbrs[a].append(b)
        nbrs[b].append(a)
    found = {}
    for a, b in edges:
        for s, t in ((a, b), (b, a)):
            loop = _ring_from(s, t, nbrs, co)
            if loop is None or frozenset(loop) in found:
                continue
            normal = _once_around(co[loop])
            if normal is not None:
                found[frozenset(loop)] = (loop, normal)
    cands = list(found.items())
    crossings = [sum(1 for other, _ in cands if other is not key and other & key) for key, _ in cands]
    taken, out = set(), []
    for n, (key, (loop, normal)) in sorted(zip(crossings, cands), key=lambda x: (x[0], len(x[1][0]))):
        if key & taken:
            continue
        taken |= key
        k = int(np.argmax(np.abs(normal)))
        flat = np.ptp(co[loop, k]) < 1e-4
        out.append((loop, k if flat else None, co[loop].mean(axis=0)))
    if len(out) > 1:
        centers = np.array([c for _, _, c in out])
        axis = np.linalg.svd(centers - centers.mean(axis=0))[2][0]
        axis = axis if axis[int(np.argmax(np.abs(axis)))] > 0 else -axis
        out.sort(key=lambda r: float(r[2] @ axis))
    return [(loop, k) for loop, k, _ in out]


def _islands(bm):
    """Connected vertex islands of a bmesh, largest first."""
    seen = set()
    islands = []
    for vert in bm.verts:
        if vert.index in seen:
            continue
        stack = [vert]
        seen.add(vert.index)
        island = []
        while stack:
            cur = stack.pop()
            island.append(cur)
            for edge in cur.link_edges:
                other = edge.other_vert(cur)
                if other.index not in seen:
                    seen.add(other.index)
                    stack.append(other)
        islands.append(island)
    return sorted(islands, key=len, reverse=True)


def _edge_loops(edges):
    """Walk boundary edges into loops, one step per vertex (two edges at most).

    Returns [(edges in walk order, closed)]. An open run is walked from one of
    its ends, so it comes out whole and not as two halves.
    """
    by_vert = {}
    for edge in edges:
        for vert in edge.verts:
            by_vert.setdefault(vert.index, []).append(edge)
    # Ends first: a walk that starts mid-run only reaches one end.
    order = sorted(edges, key=lambda e: min(len(by_vert[v.index]) for v in e.verts) != 1)
    seen = set()
    loops = []
    for start in order:
        if start.index in seen:
            continue
        vert = next((v for v in start.verts if len(by_vert[v.index]) == 1), start.verts[0])
        loop = []
        edge = start
        while edge is not None and edge.index not in seen:
            seen.add(edge.index)
            loop.append((edge, vert))
            vert = edge.other_vert(vert)
            nxt = [e for e in by_vert.get(vert.index, ()) if e.index not in seen]
            edge = nxt[0] if len(nxt) == 1 else None
        closed = len(loop) > 2 and vert.index == loop[0][1].index
        loops.append((loop, closed))
    return loops


def report(name, limit_ids=None):
    """What an edit needs before cutting: islands, border loops, where two
    islands cross, and their closest vertices.

    Read-only. Every id is a stable id of the base mesh
    (`llm_modeling_bridge_id`), so the numbers can be fed to a later op: a
    border loop's ``ids`` go to ``bridge_loops`` as they are, in walk order.
    limit_ids shortens each id list for reading only; a shortened list cannot
    be bridged.
    """
    import bmesh
    import bpy
    from mathutils import kdtree
    from mathutils.bvhtree import BVHTree
    from .surgery import state_ids

    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"no mesh object named {name!r}")
    mesh = obj.data
    ids, _ = state_ids(obj, write=False)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    islands = _islands(bm)
    out = {"object": name, "verts": len(bm.verts), "faces": len(bm.faces),
           "islands": [], "border_loops": [], "folds": [], "crossings": [], "nearest": []}

    # A border vertex whose faces turn more than a full circle: the border
    # folds over itself, as at a fork left open (D-081). fill_notch closes it.
    # A degree or two over is a flap's root, the lobe above lying over the one
    # it grows from (D-088): look before closing it.
    for vert in bm.verts:
        if vert.is_boundary and vert.link_faces:
            fan = math.degrees(sum(loop.calc_angle() for loop in vert.link_loops))
            if fan > 360:
                out["folds"].append({"id": int(ids[vert.index]), "fan_deg": round(fan)})

    # A fold (crease line) that stops inside the surface: at a junction the
    # branch's rib must run on into the stem's rib (D-084). A fold that ends
    # on the border (a leaf's tip) is not listed.
    out["fold_ends"] = []
    layer = bm.edges.layers.float.get("crease_edge")
    if layer is not None:
        for vert in bm.verts:
            if vert.is_boundary:
                continue
            creased = [e for e in vert.link_edges if e[layer] >= 0.99]
            if len(creased) == 1:
                out["fold_ends"].append({"id": int(ids[vert.index]),
                                         "from": int(ids[creased[0].other_vert(vert).index])})

    # A fold is crease and sharp together (D-085): a creased inner edge without
    # sharp is a mark left half done. sharpen_folds completes them. A border's
    # crease holds the outline (D-089) and needs no sharp.
    out["unsharp_folds"] = []
    if layer is not None:
        for edge in bm.edges:
            if edge[layer] >= 0.99 and edge.smooth and not edge.is_boundary:  # BMesh keeps sharp as smooth == False
                out["unsharp_folds"].append(sorted(int(ids[v.index]) for v in edge.verts))

    # Every border carries crease, or Subdivision shrinks the outline (D-089).
    # crease_border completes them.
    out["uncreased_border"] = [sorted(int(ids[v.index]) for v in edge.verts) for edge in bm.edges
                               if edge.is_boundary and (layer is None or edge[layer] < 0.99)]

    # Sharp on an inner edge without crease shades hard: a choice, or a border
    # mark (only a visual aid there) that a junction turned inward. Ask (D-085).
    out["sharp_only"] = [sorted(int(ids[v.index]) for v in edge.verts) for edge in bm.edges
                         if not edge.smooth and not edge.is_boundary and len(edge.link_faces) == 2
                         and (layer is None or edge[layer] < 0.99)]

    # Tips: an end row (border corner, middle, border corner). A leaf's tip
    # lies on the base (D-086): depth_mm is how far the middle stands off it.
    from .surgery import _depth_axis
    axis = _depth_axis(obj)
    out["tips"] = []
    for vert in bm.verts:
        if len(vert.link_faces) != 2 or not vert.is_boundary:
            continue
        corners = [e.other_vert(vert) for e in vert.link_edges
                   if e.is_boundary and len(e.other_vert(vert).link_faces) == 1]
        if len(corners) == 2:
            base = (corners[0].co[axis] + corners[1].co[axis]) / 2
            out["tips"].append({"row": [int(ids[corners[0].index]), int(ids[vert.index]), int(ids[corners[1].index])],
                                "depth_mm": round(abs(vert.co[axis] - base) * 1000, 2)})

    for index, island in enumerate(islands):
        co = [vert.co for vert in island]
        lo = [min(c[i] for c in co) for i in range(3)]
        hi = [max(c[i] for c in co) for i in range(3)]
        faces = {f for v in island for f in v.link_faces}
        out["islands"].append({
            "index": index,
            "verts": len(island),
            "faces": len(faces),
            "bbox_mm": [round((hi[i] - lo[i]) * 1000, 2) for i in range(3)],
            "min_mm": [round(v * 1000, 2) for v in lo],
        })

    for index, island in enumerate(islands):
        member = {vert.index for vert in island}
        border = [e for e in bm.edges if len(e.link_faces) == 1
                  and e.verts[0].index in member and e.verts[1].index in member]
        for loop, closed in _edge_loops(border):
            verts = [vert.index for _edge, vert in loop]
            if not closed:
                verts.append(loop[-1][0].other_vert(loop[-1][1]).index)
            keep = len(verts) if limit_ids is None else limit_ids
            out["border_loops"].append({
                "island": index,
                "closed": closed,
                "edges": len(loop),
                "verts": len(verts),
                "length_mm": round(sum(e.calc_length() for e, _vert in loop) * 1000, 2),
                "ids": [int(ids[i]) for i in verts[:keep]],
                "ids_truncated": max(0, len(verts) - keep),
            })

    if len(islands) > 1:
        coords = [vert.co.copy() for vert in bm.verts]
        trees, island_faces = [], []
        for island in islands:
            faces = sorted({f for v in island for f in v.link_faces}, key=lambda f: f.index)
            island_faces.append(faces)
            trees.append(BVHTree.FromPolygons(coords, [[v.index for v in f.verts] for f in faces],
                                              all_triangles=False))
        for a in range(len(islands)):
            for b in range(a + 1, len(islands)):
                hits = trees[a].overlap(trees[b])
                # The vertex ids of the faces that pass through each other: what
                # an intersect cuts and what delete_faces is likely to remove.
                ids_a = sorted({int(ids[v.index]) for fa, _fb in hits for v in island_faces[a][fa].verts})
                ids_b = sorted({int(ids[v.index]) for _fa, fb in hits for v in island_faces[b][fb].verts})
                out["crossings"].append({"islands": [a, b], "face_pairs": len(hits),
                                         "ids_a": ids_a, "ids_b": ids_b})
                kd = kdtree.KDTree(len(islands[b]))
                for i, vert in enumerate(islands[b]):
                    kd.insert(vert.co, i)
                kd.balance()
                best = (1e9, None, None)
                for vert in islands[a]:
                    _co, i, dist = kd.find(vert.co)
                    if dist < best[0]:
                        best = (dist, vert.index, islands[b][i].index)
                if best[1] is not None:
                    out["nearest"].append({"islands": [a, b], "mm": round(best[0] * 1000, 2),
                                           "a": int(ids[best[1]]), "b": int(ids[best[2]])})
    bm.free()
    return out
