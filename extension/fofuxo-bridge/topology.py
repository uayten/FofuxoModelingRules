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
