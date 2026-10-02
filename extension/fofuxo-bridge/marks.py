"""The modeler points, the AI answers: marks and annotations read on every sync.

Marks are the edges the modeler marks in Blender (sharp, seam, crease). Every
sync reports the ones new since the last sync, and the ones cleared, so none
goes unseen. The readings (D-060, confirmed by the modeler): sharp or seam on
a loop = "this loop" (remove it, move it, look at it); crease = "pinch here".
Once acted on, the AI clears its marks (mesh mark_seam <edges> clear=on,
mark_sharp ... clear=on, crease <edges> 0) and says so.

Annotations are the strokes drawn with Blender's Annotate tool in the 3D
View. Each 3D stroke reads as points; the sync names the base vertices whose
result (the sub column) lies under it, a stroke on the mirrored side counting
for the side that is modeled. Strokes drawn in screen space have no depth and
are listed without vertices.
"""

import re

import bpy
import numpy as np
from mathutils import Vector

from . import mesh_io, topology

READING = "sharp or seam on a loop = 'this loop'; crease = 'pinch here' (D-060)"
NEAR = 0.06  # of the frame's largest axis: how far from a stroke a vertex is still under it
_LINE = re.compile(r"(crease|bevel)\s+([\d.]+)\s+(.*)|(seam|sharp)\s+(.*)")


def _parse(lines):
    """{"seam": {pairs}, "crease 0.5": {pairs}, ...} from the edges section."""
    out = {}
    for line in lines or ():
        m = _LINE.fullmatch(line.strip())
        if not m:
            continue
        key, pairs = (f"{m[1]} {m[2]}", m[3]) if m[1] else (m[4], m[5])
        out[key] = set(pairs.split())
    return out


def diff(before_lines, after_lines):
    """Marks new and cleared between two edges sections, or None."""
    a, b = _parse(before_lines), _parse(after_lines)
    new = {k: sorted(b[k] - a.get(k, set())) for k in b}
    gone = {k: sorted(a[k] - b.get(k, set())) for k in a}
    new = {k: v for k, v in new.items() if v and not k.startswith("bevel")}
    gone = {k: v for k, v in gone.items() if v and not k.startswith("bevel")}
    if not new and not gone:
        return None
    out = {"reading": READING}
    if new:
        out["new"] = new
    if gone:
        out["cleared"] = gone
    return out


def _strokes():
    """(layer name, index, display mode, points as an (n, 3) array in world space)."""
    data = bpy.context.scene.annotation
    if data is None:
        return []
    out = []
    for layer in data.layers:
        frame = layer.active_frame or (layer.frames[0] if len(layer.frames) else None)
        if frame is None or layer.annotation_hide:
            continue
        for k, stroke in enumerate(frame.strokes):
            co = np.array([tuple(p.co) for p in stroke.points], dtype=float).reshape(-1, 3)
            out.append((layer.info, k, stroke.display_mode, co))
    return out


def signature(layer, k, co):
    first, last = (co[0], co[-1]) if len(co) else ((0, 0, 0), (0, 0, 0))
    return f"{layer}|{k}|{len(co)}|" + ",".join(f"{c:.5f}" for c in (*first, *last))


def read(obj, ids, depsgraph, frame, seen=()):
    """Strokes and the vertices under each; only the ones not in `seen`
    (signatures from the last sync) unless seen is None. Returns (list, all signatures)."""
    strokes = _strokes()
    if not strokes:
        return [], []
    mirror = mesh_io.mirror_setup(obj)
    sides = mesh_io.kept_sides(obj.data, mirror)
    per_vertex = mesh_io.evaluated(obj, depsgraph)[0]
    pos = np.array(per_vertex if per_vertex is not None else [tuple(v.co) for v in obj.data.vertices], dtype=float)
    reach = NEAR * max(a.extent for a in frame.axes)
    inv = obj.matrix_world.inverted()
    out, sigs = [], []
    for layer, k, mode, co in strokes:
        sig = signature(layer, k, co)
        sigs.append(sig)
        if seen is not None and sig in seen:
            continue
        entry = {"layer": layer, "stroke": k + 1, "points": len(co)}
        if mode != "3DSPACE" or not len(co):
            entry["verts"] = []
            entry["note"] = "drawn in screen space: no depth, no vertices"
            out.append(entry)
            continue
        local = np.array([tuple(inv @ Vector(c)) for c in co])
        for a in mirror:  # a stroke on the mirrored copy points at the modeled side
            k_ax = topology.AXES.index(a)
            if sides.get(a) == "-":
                local[:, k_ax] = -np.abs(local[:, k_ax])
            elif sides.get(a) == "+":
                local[:, k_ax] = np.abs(local[:, k_ax])
        d = np.linalg.norm(pos[:, None, :] - local[None, :, :], axis=2)  # vertex x point
        near = np.where(d.min(axis=1) <= reach)[0]
        if len(near):
            order = near[np.argsort(d[near].argmin(axis=1))]  # along the stroke
            entry["verts"] = [f"v{ids[i]}" for i in order]
        else:
            nearest = int(np.linalg.norm(pos - local.mean(axis=0), axis=1).argmin())
            gap = float(np.linalg.norm(pos[nearest] - local.mean(axis=0)))
            entry["verts"] = []
            entry["nearest"] = f"v{ids[nearest]} ({gap * 1000:.1f} mm from the stroke's middle)"
        out.append(entry)
    return out, sigs


def clear_annotations(layer=None):
    """Remove the strokes the AI acted on: every layer's, or one layer's."""
    from .instance import assert_ai_access
    assert_ai_access()
    data = bpy.context.scene.annotation
    if data is None:
        return 0
    n = 0
    for lay in data.layers:
        if layer is not None and lay.info != layer:
            continue
        for frame in lay.frames:
            for stroke in list(frame.strokes):
                frame.strokes.remove(stroke)
                n += 1
    return n
