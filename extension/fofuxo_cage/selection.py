"""The selection grammar shared by the mesh, crease and dissolve ops.

    v25                  a vertex
    v25-v22              an edge
    L3                   a loop label from the verts section: the edges
                         between its consecutive vertices
    plane-x/y/z          every edge on that mirror plane
    sharp, seam, crease  every edge with that mark (crease: weight above 0)
    loop vA-vB           the edge loop through edge vA-vB (Blender's
                         select_edge_loop_multi)
    ring vA-vB           the edge ring through edge vA-vB (select_edge_ring_multi)
    path vA vB           the shortest path of edges from vA to vB
                         (shortest_path_select)
    faces vA vB vC ...   every face whose vertices are all in the list
    all                  everything

Terms add up. parse() and check() run in Object Mode before anything
changes; resolve() runs in Edit Mode and selects the elements, calling
Blender's own walkers for loop, ring and path.
"""

import re

import bmesh
import bpy

from .topology import PLANE_TOL

ID_ATTR = "fofuxo_cage_id"
MARKS = {"sharp": "sharp_edge", "seam": "uv_seam", "crease": "crease_edge"}
_VID = re.compile(r"v(\d+)")
_PAIR = re.compile(r"v(\d+)-v(\d+)")


class SelectionError(ValueError):
    pass


def parse(tokens, cage):
    """Terms from selection tokens; loop labels are expanded with the cage."""
    groups = {label.lower(): ids for label, ids in cage.groups if label} if cage is not None else {}
    terms = []
    toks = [t.lower() for t in tokens]
    i = 0

    def pair_at(k, word):
        m = _PAIR.fullmatch(toks[k]) if k < len(toks) else None
        if not m:
            raise SelectionError(f"'{word}' takes an edge vA-vB")
        return int(m[1]), int(m[2])

    while i < len(toks):
        t = toks[i]
        if t in ("loop", "ring"):
            terms.append(("walk", t, *pair_at(i + 1, t)))
            i += 2
            continue
        if t == "path":
            ends = [_VID.fullmatch(x) for x in toks[i + 1:i + 3]]
            if len(ends) != 2 or not all(ends):
                raise SelectionError("'path' takes two vertices: path vA vB")
            terms.append(("path", int(ends[0][1]), int(ends[1][1])))
            i += 3
            continue
        if t == "faces":
            ids = []
            i += 1
            while i < len(toks) and _VID.fullmatch(toks[i]):
                ids.append(int(toks[i][1:]))
                i += 1
            if len(ids) < 3:
                raise SelectionError("'faces' takes the vertices of the faces: faces vA vB vC vD")
            terms.append(("faces", tuple(ids)))
            continue
        m = _PAIR.fullmatch(t)
        if m:
            terms.append(("edge", int(m[1]), int(m[2])))
        elif _VID.fullmatch(t):
            terms.append(("vert", int(t[1:])))
        elif t in groups:
            ids = groups[t]
            terms += [("edge", a, b) for a, b in zip(ids, ids[1:])]
        elif t in ("plane-x", "plane-y", "plane-z"):
            terms.append(("plane", "xyz".index(t[-1])))
        elif t in MARKS:
            terms.append(("mark", t))
        elif t == "all":
            terms.append(("all",))
        else:
            raise SelectionError(f"unknown selection {tokens[i]!r}; use vN, vA-vB, a loop label, plane-x/y/z, "
                                 "sharp, seam, crease, loop vA-vB, ring vA-vB, path vA vB, faces vA vB vC vD or all")
        i += 1
    if not terms:
        raise SelectionError("nothing selected")
    return terms


def check(mesh, terms):
    """Refuse unknown vertices, pairs that share no edge and marks nobody made."""
    ids = [d.value for d in mesh.attributes[ID_ATTR].data]
    known = set(ids)
    edges = {frozenset((ids[a], ids[b])) for a, b in (e.vertices for e in mesh.edges)}
    for term in terms:
        kind = term[0]
        vids = []
        if kind == "vert":
            vids = [term[1]]
        elif kind in ("edge", "walk"):
            vids = list(term[-2:])
        elif kind in ("path", "faces"):
            vids = list(term[1]) if kind == "faces" else list(term[1:])
        for v in vids:
            if v not in known:
                raise SelectionError(f"no vertex v{v}")
        if kind in ("edge", "walk") and frozenset(term[-2:]) not in edges:
            raise SelectionError(f"v{term[-2]} and v{term[-1]} share no edge")
        if kind == "mark":
            attr = mesh.attributes.get(MARKS[term[1]])
            if attr is None or not any(d.value for d in attr.data):
                raise SelectionError(f"no edge is marked {term[1]}")


def _clear(bm):
    for seq in (bm.faces, bm.edges, bm.verts):
        for el in seq:
            el.select_set(False)
    bm.select_history.clear()


def _walk(obj, bm, op, ctx):
    """Run a Blender selection walker from the current selection; return what it selected."""
    bmesh.update_edit_mesh(obj.data)
    with bpy.context.temp_override(**ctx):
        if "FINISHED" not in op():
            raise SelectionError(f"Blender refused {op.idname_py()}")
    bm = bmesh.from_edit_mesh(obj.data)
    return bm, {e.index for e in bm.edges if e.select}


def resolve(obj, terms, ctx):
    """Select what the terms name in Edit Mode. Returns {"verts", "edges",
    "faces": sets of indices, "seed": index of the first edge named}."""
    ts = bpy.context.tool_settings
    bm = bmesh.from_edit_mesh(obj.data)
    lay = bm.verts.layers.int.get(ID_ATTR)
    by_id = {v[lay]: v for v in bm.verts}

    def edge(a, b):
        va, vb = by_id[a], by_id[b]
        return next(e for e in va.link_edges if e.other_vert(va) is vb)

    verts, edges, faces = set(), set(), set()
    seed = None
    for term in terms:
        kind = term[0]
        if kind == "vert":
            verts.add(by_id[term[1]].index)
        elif kind == "edge":
            e = edge(*term[1:])
            edges.add(e.index)
            seed = e.index if seed is None else seed
        elif kind == "plane":
            k = term[1]
            edges |= {e.index for e in bm.edges if all(abs(v.co[k]) < PLANE_TOL for v in e.verts)}
        elif kind == "mark":
            if term[1] == "sharp":
                edges |= {e.index for e in bm.edges if not e.smooth}
            elif term[1] == "seam":
                edges |= {e.index for e in bm.edges if e.seam}
            else:
                layer = bm.edges.layers.float.get(MARKS["crease"])
                edges |= {e.index for e in bm.edges if layer is not None and e[layer] > 0}
        elif kind == "walk":
            e = edge(*term[2:])
            seed = e.index if seed is None else seed
            ts.mesh_select_mode = (False, True, False)
            _clear(bm)
            e.select_set(True)
            op = bpy.ops.mesh.select_edge_loop_multi if term[1] == "loop" else bpy.ops.mesh.select_edge_ring_multi
            bm, found = _walk(obj, bm, op, ctx)
            edges |= found
        elif kind == "path" and by_id[term[2]] in [e.other_vert(by_id[term[1]]) for e in by_id[term[1]].link_edges]:
            # Neighbours: the path is their edge (Blender's walker selects nothing then).
            edges.add(edge(*term[1:]).index)
        elif kind == "path":
            ts.mesh_select_mode = (True, False, False)
            _clear(bm)
            for vid in term[1:]:
                v = by_id[vid]
                v.select_set(True)
                bm.select_history.add(v)
            bm, _ = _walk(obj, bm, bpy.ops.mesh.shortest_path_select, ctx)
            bm.select_flush(True)
            edges |= {e.index for e in bm.edges if e.select}
        elif kind == "faces":
            want = {by_id[v] for v in term[1]}
            faces |= {f.index for f in bm.faces if set(f.verts) <= want}
        elif kind == "all":
            faces |= {f.index for f in bm.faces}
            edges |= {e.index for e in bm.edges}
            verts |= {v.index for v in bm.verts}
        bm = bmesh.from_edit_mesh(obj.data)
        lay = bm.verts.layers.int.get(ID_ATTR)
        by_id = {v[lay]: v for v in bm.verts}
    if not (verts or edges or faces):
        raise SelectionError("the selection is empty")
    apply(obj, {"verts": verts, "edges": edges, "faces": faces})
    return {"verts": verts, "edges": edges, "faces": faces, "seed": seed}


def apply(obj, sel):
    """Select exactly sel's elements (and what they imply) in Edit Mode."""
    bm = bmesh.from_edit_mesh(obj.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    bpy.context.tool_settings.mesh_select_mode = (bool(sel["verts"]) or not (sel["edges"] or sel["faces"]),
                                                  bool(sel["edges"]), bool(sel["faces"]))
    _clear(bm)
    for i in sel["verts"]:
        bm.verts[i].select_set(True)
    for i in sel["edges"]:
        bm.edges[i].select_set(True)
    for i in sel["faces"]:
        bm.faces[i].select_set(True)
    bmesh.update_edit_mesh(obj.data)


def selected_ids(obj):
    """Ids of the selected vertices and edges, in Edit Mode."""
    bm = bmesh.from_edit_mesh(obj.data)
    lay = bm.verts.layers.int.get(ID_ATTR)
    verts = sorted(v[lay] for v in bm.verts if v.select)
    edges = sorted(tuple(sorted((e.verts[0][lay], e.verts[1][lay]))) for e in bm.edges if e.select)
    faces = sorted(tuple(sorted(v[lay] for v in f.verts)) for f in bm.faces if f.select)
    return verts, edges, faces
