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

__all__ = ("delete_faces", "bridge_loops", "cut_between", "weld", "weld_region")


def _open(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"no mesh object named {name!r}")
    mesh = obj.data
    ids, _ = mesh_io.ensure_ids(mesh, write=False)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return obj, bm, ids


def _finish(obj, bm, sync):
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    _ids, fresh = mesh_io.ensure_ids(obj.data, write=True)
    out = {"object": obj.name, "verts": len(obj.data.vertices),
           "faces": len(obj.data.polygons), "fresh_ids": len(fresh)}
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
            raise ValueError("delete_faces needs ids or faces")
        wanted = set(ids)
        targets = [f for f in bm.faces if all(vids[v.index] in wanted for v in f.verts)]
    else:
        targets = [bm.faces[i] for i in faces if i < len(bm.faces)]
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


def bridge_loops(name, loop_a, loop_b, sync=True):
    """Bridge two loops named by ordered vertex ids, never 'all borders'.

    loop_a and loop_b are the ``ids`` lists of ``topology_report``'s border
    loops; the order in that list is the walk order, which is also the pairing
    order the bridge uses.
    """
    assert_ai_access()
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, list(loop_a) + list(loop_b))
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    edges = []
    for loop in (loop_a, loop_b):
        verts = [index_of[i] for i in loop]
        for a, b in zip(verts, verts[1:] + verts[:1]):
            edge = bm.edges.get((a, b))
            if edge is not None:
                edges.append(edge)
    if len(edges) < 4:
        bm.free()
        raise ValueError("the ids do not form two closed loops of edges")
    before = len(bm.faces)
    result = bmesh.ops.bridge_loops(bm, edges=edges, use_pairs=False, use_cyclic=False)
    made = len(result.get("faces", [])) or (len(bm.faces) - before)
    out = _finish(obj, bm, sync)
    out["bridged_faces"] = made
    return out


def cut_between(name, id_a, id_b, sync=True):
    """Cut the faces along the straight segment between two vertices.

    This is Blender's 'connect vertices' (J): a new edge from id_a to id_b that
    splits every face it crosses. Use it on one island: a cut across two
    islands has no surface to walk.
    """
    assert_ai_access()
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, [id_a, id_b])
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    va, vb = index_of[id_a], index_of[id_b]
    before = len(bm.faces)
    bmesh.ops.connect_verts(bm, verts=[va, vb])
    out = _finish(obj, bm, sync)
    out["new_faces"] = len(obj.data.polygons) - before
    return out


def weld(name, id_a, id_b, at="a", sync=True):
    """Merge two vertices. at: 'a' keeps id_a's position, 'b' keeps id_b's,
    'mid' merges at the midpoint."""
    assert_ai_access()
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
    bmesh.ops.pointmerge(bm, verts=[va, vb], merge_co=co)
    out = _finish(obj, bm, sync)
    out["welded"] = [id_a, id_b]
    return out


def weld_region(name, ids_a, ids_b, threshold=0.0005, sync=True):
    """Weld the closest vertex pairs between two id sets, under threshold (m)."""
    assert_ai_access()
    from mathutils import kdtree
    obj, bm, vids = _open(name)
    index_of, missing = _by_id(bm, vids, list(ids_a) + list(ids_b))
    if missing:
        bm.free()
        raise ValueError(f"unknown ids {missing}")
    tree = kdtree.KDTree(len(ids_b))
    for i, vid in enumerate(ids_b):
        tree.insert(index_of[vid].co, i)
    tree.balance()
    pairs = []
    used = set()
    for vid in ids_a:
        _co, i, dist = tree.find(index_of[vid].co)
        if dist <= threshold and ids_b[i] not in used:
            used.add(ids_b[i])
            pairs.append((int(vid), int(ids_b[i])))
    moved = []
    for a_id, b_id in pairs:
        index_of[a_id].co = index_of[b_id].co.copy()
        moved.append(index_of[b_id].co.copy())
    if moved:
        bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if any((v.co - co).length < 1e-9 for co in moved)],
                                 dist=threshold)
    out = _finish(obj, bm, sync)
    out["pairs"] = pairs
    return out


