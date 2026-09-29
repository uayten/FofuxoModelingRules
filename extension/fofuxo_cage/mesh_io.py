"""Read the base mesh and the evaluated mesh; write vertex positions back.

Writes touch only vertex positions and the stable id attribute. Modifiers,
materials, parent and every other mesh attribute stay as they are.
"""

import bmesh
import bpy

from . import modifier_info, topology
from .cage_format import Cage, Vertex, fmt, normalize_face
from .frame import Frame

ID_ATTR = "fofuxo_cage_id"
# Modifiers that keep base vertex i at evaluated index i (checked: Mirror > Subdivision).
INDEX_SAFE = {"MIRROR", "SUBSURF"}
EDGE_FLOAT_ATTRS = (("crease_edge", "crease"), ("bevel_weight_edge", "bevel"))
EDGE_BOOL_ATTRS = (("uv_seam", "seam"), ("sharp_edge", "sharp"))


def ensure_ids(mesh, snapshot_co=None, next_id=0, write=True):
    """Stable id of each vertex index, repairing missing or duplicated ids.

    New vertices made in Blender copy or interpolate the id of their source.
    A duplicated id stays with the copy closest to its last synced position;
    the others get fresh ids, never reusing one from the last sync.
    Returns (ids, fresh_ids).
    """
    n = len(mesh.vertices)
    attr = mesh.attributes.get(ID_ATTR)
    if attr is None or attr.domain != "POINT" or attr.data_type != "INT":
        ids = list(range(n))
        if write:
            if attr is not None:
                mesh.attributes.remove(attr)
            mesh.attributes.new(ID_ATTR, "INT", "POINT").data.foreach_set("value", ids)
        return ids, []
    ids = [0] * n
    attr.data.foreach_get("value", ids)
    by_id = {}
    for i, vid in enumerate(ids):
        by_id.setdefault(vid, []).append(i)
    known = list(snapshot_co or ())
    nxt = max([next_id - 1, *ids, *known], default=-1) + 1
    fresh = []
    for vid, idxs in by_id.items():
        if len(idxs) < 2 and vid >= 0:
            continue
        keep = None
        if vid >= 0:
            if snapshot_co and vid in snapshot_co:
                ref = snapshot_co[vid]
                keep = min(idxs, key=lambda i: sum((a - b) ** 2 for a, b in zip(mesh.vertices[i].co, ref)))
            else:
                keep = idxs[0]
        for i in idxs:
            if i != keep:
                ids[i] = nxt
                fresh.append(nxt)
                nxt += 1
    if fresh and write:
        mesh.attributes[ID_ATTR].data.foreach_set("value", ids)
    return ids, fresh


def mesh_state(mesh, ids):
    """Exact positions (m) by id and faces as id tuples."""
    return {
        "co": {vid: tuple(v.co) for vid, v in zip(ids, mesh.vertices)},
        "faces": sorted(normalize_face([ids[i] for i in p.vertices]) for p in mesh.polygons),
    }


def mirror_setup(obj):
    """Mirror axes (without a mirror object) and the largest merge threshold per axis."""
    axes = {}
    for m in obj.modifiers:
        if m.type == "MIRROR" and m.show_viewport and m.mirror_object is None:
            for a, on in zip(topology.AXES, m.use_axis):
                if on:
                    merge = m.merge_threshold if m.use_mirror_merge else 0.0
                    axes[a] = max(axes.get(a, 0.0), merge)
    return axes


def kept_sides(mesh, mirror_axes):
    """Side of each mirror plane the base mesh lives on: '+', '-', '?' (both) or '0'."""
    sides = {}
    for a in mirror_axes:
        k = topology.AXES.index(a)
        vals = [v.co[k] for v in mesh.vertices if abs(v.co[k]) >= topology.PLANE_TOL]
        pos = any(c > 0 for c in vals)
        neg = any(c < 0 for c in vals)
        sides[a] = "?" if pos and neg else "+" if pos else "-" if neg else "0"
    return sides


def stack_label(obj):
    parts = []
    for m in obj.modifiers:
        label = m.name
        if m.type == "MIRROR":
            label += "(" + "".join(a for a, on in zip(topology.AXES, m.use_axis) if on) + ")"
        elif m.type == "SUBSURF":
            label += f"({m.levels}/{m.render_levels})"
        if not m.show_viewport:
            label += "[off]"
        parts.append(label)
    return " > ".join(parts) or "none"


def evaluated(obj, depsgraph):
    """Evaluated positions of the base vertices (or None) and of the whole result.

    Base vertex i is evaluated vertex i only while the stack is Mirror and
    Subdivision; any other enabled modifier makes the per-vertex column
    unavailable.
    """
    blocking = sorted({
        m.type for m in obj.modifiers
        if m.show_viewport and (m.type not in INDEX_SAFE or (
            m.type == "MIRROR" and (any(m.use_bisect_axis) or m.mirror_object is not None)))
    })
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        all_co = [tuple(v.co) for v in me.vertices]
        faces = len(me.polygons)
    finally:
        ev.to_mesh_clear()
    n = len(obj.data.vertices)
    per_vertex = None if blocking or len(all_co) < n else all_co[:n]
    return per_vertex, all_co, faces, blocking


def _extent(coords, k, mirrored):
    vals = [c[k] for c in coords]
    if not vals:
        return 0.0
    if mirrored:
        return 2 * max(abs(v) for v in vals)
    return max(vals) - min(vals)


def _size(coords, mirrored_axes):
    return " x ".join(fmt(_extent(coords, k, a in mirrored_axes) * 1000) for k, a in enumerate(topology.AXES))


def edge_data_lines(mesh, ids):
    lines = []
    pairs = [tuple(sorted((ids[e.vertices[0]], ids[e.vertices[1]]))) for e in mesh.edges]

    def fmt_pairs(sel):
        return " ".join(f"v{a}-v{b}" for a, b in sorted(sel))

    for name, label in EDGE_FLOAT_ATTRS:
        attr = mesh.attributes.get(name)
        if attr is None or attr.domain != "EDGE":
            continue
        by_value = {}
        for pair, d in zip(pairs, attr.data):
            if d.value > 0:
                by_value.setdefault(round(d.value, 2), []).append(pair)
        for value in sorted(by_value):
            lines.append(f"{label} {value}  {fmt_pairs(by_value[value])}")
    for name, label in EDGE_BOOL_ATTRS:
        attr = mesh.attributes.get(name)
        if attr is None or attr.domain != "EDGE":
            continue
        sel = [pair for pair, d in zip(pairs, attr.data) if d.value]
        if sel:
            lines.append(f"{label}  {fmt_pairs(sel)}")
    return lines


def default_frame(obj, depsgraph):
    """Frame that just holds the evaluated result (what the concept is compared with)."""
    mirror = mirror_setup(obj)
    _, all_co, _, _ = evaluated(obj, depsgraph)
    return Frame.around(all_co, kept_sides(obj.data, mirror))


def _fresh_depsgraph():
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


def build_cage(obj, ids, depsgraph, frame, forms=()):
    """The cage text model of the object's current mesh, measured in frame."""
    mesh = obj.data
    mirror = mirror_setup(obj)
    per_vertex, all_co, eval_faces, blocking = evaluated(obj, depsgraph)

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        flags = [topology.vertex_flags(v, mirror) for v in bm.verts]
        groups = topology.group_vertices(topology.edge_loops(bm), len(bm.verts))
    finally:
        bm.free()

    cage = Cage()
    base_co = [tuple(v.co) for v in mesh.vertices]
    sub_note = "" if per_vertex is not None else f"   (sub unavailable: {', '.join(blocking)})"
    cage.header = {
        "object": obj.name,
        "frame": frame.text(),
        "stack": stack_label(obj),
        "size": f"base {_size(base_co, mirror)}   sub {_size(all_co, ())}   (mm, w x d x h)",
        "count": f"v {len(mesh.vertices)}  f {len(mesh.polygons)}   evaluated v {len(all_co)} f {eval_faces}{sub_note}",
    }
    for i, v in enumerate(mesh.vertices):
        sub = frame.to_values(per_vertex[i]) if per_vertex else None
        cage.verts[ids[i]] = Vertex(ids[i], frame.to_values(v.co), sub, flags[i])
    loops, rest = groups
    for n, grp in enumerate(loops, 1):
        cage.groups.append((f"L{n}", [ids[i] for i in grp]))
    if rest:
        cage.groups.append(("rest", [ids[i] for i in rest]))
    cage.faces = [tuple(ids[i] for i in p.vertices) for p in mesh.polygons]
    cage.edges = edge_data_lines(mesh, ids)
    cage.modifiers = modifier_info.describe(obj, _fresh_depsgraph, lambda co: _size(co, ()))
    cage.forms = list(forms)
    return cage


def write_positions(obj, ids, new_co):
    """Move vertices by id to new positions (m). Only positions change."""
    index = {vid: i for i, vid in enumerate(ids)}
    verts = obj.data.vertices
    for vid, co in new_co.items():
        verts[index[vid]].co = co
    obj.data.update()
