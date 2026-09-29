"""Edge loops, vertex grouping and per-vertex flags on the base mesh (bmesh)."""

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


def group_vertices(loops, vert_count):
    """Cover every vertex once with pieces of edge loops, longest first.

    Returns (loop_pieces, rest): rest holds the vertices no piece covers.
    """
    taken = [False] * vert_count
    groups = []
    while True:
        best = None
        for loop in loops:
            run, cur = [], []
            for i in loop + [None]:
                if i is None or taken[i]:
                    if len(cur) > len(run):
                        run = cur
                    cur = []
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
