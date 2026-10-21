"""Topology surgery on the base mesh, addressed by stable id.

The modeler's Edit Mode moves, in calls the AI can run and check: delete the
faces that a weld would hide, bridge the two loops of a junction, cut between
two vertices, weld pairs. Every call edits the cage, repairs the stable ids and
syncs, so the next call sees the same ids it returned here.

Ids are the values of the ``llm_modeling_bridge_id`` point attribute (the ones
``topology_report`` and ``views(focus=...)`` print as ``v12``).
"""

import bmesh
import bpy

from . import mesh_io
from .instance import assert_ai_access

__all__ = ("delete_faces", "bridge_loops", "cut_between", "fill_notch", "intersect", "make_face", "weld", "weld_region")


def state_ids(obj, write):
    """The stable ids sync would give, repaired against the last sync state.

    Without the state a fresh id can reuse the id of a vertex deleted since the
    last sync; sync then reads it as stale and renumbers it, and the ids a call
    returned no longer name the same vertices.
    """
    from .sync import SyncError, _load_state, paths
    try:
        state = _load_state(paths(obj)["state"])
    except SyncError:
        state = None  # an unsaved file has no sync state
    return mesh_io.ensure_ids(obj.data, state and state["co"], state["next_id"] if state else 0, write=write)


def _open(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"no mesh object named {name!r}")
    # Repair first, so the ids the bmesh carries are the ids the caller sees.
    ids, _ = state_ids(obj, write=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return obj, bm, ids


def _finish(obj, bm, sync):
    counts = {"non_manifold": sum(1 for e in bm.edges if len(e.link_faces) > 2),
              "boundary": sum(1 for e in bm.edges if len(e.link_faces) == 1),
              "wire": sum(1 for e in bm.edges if not e.link_faces)}
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    _ids, fresh = state_ids(obj, write=True)
    out = {"object": obj.name, "verts": len(obj.data.vertices),
           "faces": len(obj.data.polygons), **counts, "new_ids": sorted(fresh)}
    if sync:
        from .sync import sync as sync_fn
        r = sync_fn(obj.name, render=False)
        out["action"] = r.get("action")
        out["issues"] = [f"{i['level']} {i['code']}" for i in r.get("issues", [])]
    return out


def _by_id(bm, vids, wanted):
    """Map stable id to bmesh vertex; report the ids that no vertex carries."""
    index_of = {vids[v.index]: v for v in bm.verts}
    missing = [i for i in wanted if i not in index_of]
    return index_of, missing


def delete_faces(name, ids=None, faces=None, sync=True):
    """Delete faces by stable vertex id or by face index.

    ids: the faces deleted are the ones whose every vertex id is in the list
    (the faces the modeler painted). faces: face indices, when known.
    """
    assert_ai_access()
    obj, bm, vids = _open(name)
    if faces is None:
        if not ids:
            bm.free()
            raise ValueError("delete_faces needs ids or faces")
        wanted = set(ids)
        targets = [f for f in bm.faces if all(vids[v.index] in wanted for v in f.verts)]
    else:
        bad = [i for i in faces if not 0 <= i < len(bm.faces)]
        if bad:
            bm.free()
            raise ValueError(f"no faces {bad} (the mesh has {len(bm.faces)})")
        targets = [bm.faces[i] for i in faces]
    if not targets:
        bm.free()
        return {"object": name, "deleted": 0, "note": "no face matched"}
    bmesh.ops.delete(bm, geom=targets, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces and not v.link_edges]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    out = _finish(obj, bm, sync)
    out["deleted"] = len(targets)
    return out


def _chain_edges(bm, index_of, loop):
    """The edges along an ordered id list, and whether the list closes on itself.

    Every consecutive pair must share an edge: a gap means the ids are not one
    border (a truncated list, or ids from two loops), and bridging a part of it
    would silently leave the rest open.
    """
    verts = [index_of[i] for i in loop]
    edges, gaps = [], []
    for (ia, a), (ib, b) in zip(zip(loop, verts), zip(loop[1:], verts[1:])):
        edge = bm.edges.get((a, b))
        if edge is None:
            gaps.append((ia, ib))
        else:
            edges.append(edge)
    closing = bm.edges.get((verts[-1], verts[0])) if len(verts) > 2 else None
    if closing is not None:
        edges.append(closing)
    return edges, closing is not None, gaps


def bridge_loops(name, loop_a, loop_b, sync=True):
    """Bridge two loops named by ordered vertex ids, never 'all borders'.

    loop_a and loop_b are walks along a border: the full ``ids`` lists of
    ``topology_report``'s border loops, or an open run of one (the junction's
    side). Both must be closed or both open. Blender picks which vertices face
    each other; check the result with ``views(focus=...)``.
    """
    assert_ai_access()
    loop_a, loop_b = list(loop_a), list(loop_b)
    if len(loop_a) < 2 or len(loop_b) < 2:
        raise ValueError("each loop needs two ids at least")
    if set(loop_a) & set(loop_b):
        raise ValueError(f"the loops share ids {sorted(set(loop_a) & set(loop_b))}")
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, loop_a + loop_b)
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    edges_a, closed_a, gaps_a = _chain_edges(bm, index_of, loop_a)
    edges_b, closed_b, gaps_b = _chain_edges(bm, index_of, loop_b)
    if gaps_a or gaps_b:
        bm.free()
        raise ValueError(f"no edge between consecutive ids {gaps_a + gaps_b}: pass each loop's full walk")
    if closed_a != closed_b:
        bm.free()
        raise ValueError("one loop is closed and the other open")
    result = bmesh.ops.bridge_loops(bm, edges=edges_a + edges_b, use_pairs=False, use_cyclic=False)
    made = len(result.get("faces", []))
    out = _finish(obj, bm, sync)
    out["bridged_faces"] = made
    return out


def cut_between(name, id_a, id_b, sync=True):
    """Cut the faces along the surface path between two vertices.

    This is Blender's 'connect vertex path' (J): new edges from id_a to id_b
    that split every face on the way, with a new vertex wherever the path
    crosses an edge (their ids are in ``new_ids``). Both ids must be on the
    same island: two islands have no surface between them.
    """
    assert_ai_access()
    if id_a == id_b:
        raise ValueError("cut_between needs two different ids")
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, [id_a, id_b])
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    before = len(bm.faces)
    result = bmesh.ops.connect_vert_pair(bm, verts=[index_of[id_a], index_of[id_b]])
    if not result.get("edges"):
        bm.free()
        raise ValueError(f"no cut between {id_a} and {id_b}: no surface path (another island, or already an edge)")
    new_edges = len(result["edges"])
    out = _finish(obj, bm, sync)
    out["new_edges"] = new_edges
    out["new_faces"] = out["faces"] - before
    return out


def _island_faces(bm, start):
    """Indices of the faces of the island that holds vertex `start`."""
    seen, stack = {start.index}, [start]
    while stack:
        cur = stack.pop()
        for edge in cur.link_edges:
            other = edge.other_vert(cur)
            if other.index not in seen:
                seen.add(other.index)
                stack.append(other)
    return {f.index for f in bm.faces if f.verts[0].index in seen}


def intersect(name, island_id, sync=True):
    """Cut the island holding vertex island_id against the rest of the mesh,
    with one shared cut line (Edit Mode's Intersect (Knife), Merge).

    Where two plates cross, each edge of the line has 4 faces until the flaps
    are deleted; ``cut_ids`` are the line's vertex ids, ``non_manifold`` its
    edges. Pick the flaps to delete from a ``views(focus=cut_ids)``.
    """
    assert_ai_access()
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, [island_id])
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    faces = _island_faces(bm, index_of[island_id])
    total = len(bm.faces)
    bm.free()
    if len(faces) == total:
        raise ValueError(f"{name} is one island: nothing to cut against")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.mesh.select_all(action="DESELECT")
        edit = bmesh.from_edit_mesh(obj.data)
        edit.faces.ensure_lookup_table()
        for index in faces:
            edit.faces[index].select_set(True)
        edit.select_flush(True)
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.mesh.intersect(mode="SELECT_UNSELECT", separate_mode="NONE", solver="EXACT")
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    line = [e for e in bm.edges if len(e.link_faces) > 2]
    cut = {v.index for e in line for v in e.verts}
    out = _finish(obj, bm, sync)
    ids, _ = state_ids(obj, write=False)
    out["cut_ids"] = sorted(int(ids[i]) for i in cut)
    if not line:
        out["note"] = "no edge of the cut has more than 2 faces: the islands may only touch, or not meet"
    return out


def make_face(name, ids, sync=True):
    """Blender's Make Face (F): one face through the vertices, in the order
    given (walk the outline). Refuses a face that already exists."""
    assert_ai_access()
    ids = list(ids)
    if len(ids) < 3 or len(set(ids)) != len(ids):
        raise ValueError("make_face needs three different ids at least")
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, ids)
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    verts = [index_of[i] for i in ids]
    if bm.faces.get(verts) is not None:
        bm.free()
        raise ValueError(f"the face {ids} exists")
    face = bm.faces.new(verts)
    bm.normal_update()
    # Match the neighbours' winding, or Subdivision shades the new face inverted.
    neighbour = next((f for e in face.edges for f in e.link_faces if f is not face), None)
    if neighbour is not None:
        shared = next(e for e in face.edges if neighbour in e.link_faces)
        a, b = shared.verts
        def runs(f):
            loop = next(l for l in f.loops if l.vert is a)
            return loop.link_loop_next.vert is b
        if runs(face) == runs(neighbour):
            face.normal_flip()
    out = _finish(obj, bm, sync)
    out["made"] = ids
    return out


def _border_next(vert, prev):
    """The border vertex after vert, walking away from prev."""
    nxt = [e.other_vert(vert) for e in vert.link_edges if e.is_boundary and e.other_vert(vert) is not prev]
    return nxt[0] if len(nxt) == 1 else None


def fill_notch(name, vertex_id, sync=True):
    """Close the wedge at a border vertex with one quad: the vertex, its two
    border neighbours and the next border vertex on one side (F2 there).

    The modeler's move at a fork (D-081): the faces around the split vertex
    must close, so the vertex ends inside the surface. The side whose closing
    edge is shorter is taken; ``topology_report``'s ``folds`` names the
    vertices that need it.
    """
    assert_ai_access()
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, [vertex_id])
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    v = index_of[vertex_id]
    sides = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
    if len(sides) != 2:
        bm.free()
        raise ValueError(f"v{vertex_id} has {len(sides)} border edges, not 2: not a notch")
    a, b = sides
    options = []
    for first, other in ((a, b), (b, a)):
        far = _border_next(first, v)
        if far is not None and far is not other:
            quad = [v, first, far, other]
            # Try it on a copy: the right side leaves no new fold behind (the
            # wrong one moves the fold to the next border vertex).
            trial = bm.copy()
            trial.verts.ensure_lookup_table()
            trial.faces.new([trial.verts[x.index] for x in quad])
            folds = sum(1 for x in quad if trial.verts[x.index].is_boundary
                        and sum(loop.calc_angle() for loop in trial.verts[x.index].link_loops) > 6.2832)
            trial.free()
            options.append((folds, (far.co - other.co).length, quad))
    if not options:
        bm.free()
        raise ValueError(f"no border vertex to close the notch at v{vertex_id}")
    folds, closing, quad = min(options, key=lambda o: (o[0], o[1]))
    quad_ids = [int(vids[x.index]) for x in quad]
    bm.free()
    out = make_face(name, quad_ids, sync=sync)
    out["closing_mm"] = round(closing * 1000, 2)
    out["folds_left"] = folds
    return out


def weld(name, id_a, id_b, at="a", sync=True):
    """Weld id_a onto id_b: id_b survives. at: 'a' keeps id_a's position,
    'b' keeps id_b's, 'mid' merges at the midpoint."""
    assert_ai_access()
    if id_a == id_b:
        raise ValueError("weld needs two different ids")
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, [id_a, id_b])
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    va, vb = index_of[id_a], index_of[id_b]
    if at == "a":
        co = va.co.copy()
    elif at == "b":
        co = vb.co.copy()
    elif at == "mid":
        co = (va.co + vb.co) / 2
    else:
        bm.free()
        raise ValueError("at must be 'a', 'b' or 'mid'")
    # id_b survives, wherever the vertex lands: weld a onto b.
    vb.co = co
    bmesh.ops.weld_verts(bm, targetmap={va: vb})
    out = _finish(obj, bm, sync)
    out["welded"] = [id_a, id_b]
    return out


def weld_region(name, ids_a, ids_b, threshold=0.0005, sync=True):
    """Weld the closest vertex pairs between two id sets, under threshold (m).

    Each vertex of ids_a moves onto its partner in ids_b, which keeps its
    position. Pairs are taken closest first, each vertex in one pair at most,
    so the result does not depend on the order of the lists. The sets must not
    share ids: a vertex is always closest to itself.
    """
    assert_ai_access()
    from mathutils import kdtree
    ids_a, ids_b = list(ids_a), list(ids_b)
    if not ids_a or not ids_b:
        raise ValueError("weld_region needs two non-empty id sets")
    shared = set(ids_a) & set(ids_b)
    if shared:
        raise ValueError(f"the sets share {len(shared)} ids: pass the two sides of the seam, not one set twice")
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, ids_a + ids_b)
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    tree = kdtree.KDTree(len(ids_b))
    for i, vid in enumerate(ids_b):
        tree.insert(index_of[vid].co, i)
    tree.balance()
    candidates = sorted((dist, a_id, ids_b[i]) for a_id in ids_a
                        for _co, i, dist in tree.find_range(index_of[a_id].co, threshold))
    pairs, used_a, used_b = [], set(), set()
    for dist, a_id, b_id in candidates:
        if a_id not in used_a and b_id not in used_b:
            used_a.add(a_id)
            used_b.add(b_id)
            pairs.append((int(a_id), int(b_id), round(dist * 1000, 3)))
    if pairs:
        bmesh.ops.weld_verts(bm, targetmap={index_of[a]: index_of[b] for a, b, _mm in pairs})
    out = _finish(obj, bm, sync)
    out["pairs"] = [[a, b] for a, b, _mm in pairs]
    out["pairs_mm"] = [mm for _a, _b, mm in pairs]
    out["unpaired_a"] = len(ids_a) - len(pairs)
    return out
