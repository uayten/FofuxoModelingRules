"""How easy a cage is to edit, measured, next to a reference cage (the modeler's).

    editability("Laço", ref="Laço", blend="models/example/laco/human/Laço.blend")

- offset: how far each cage vertex sits from where it lands after the stack
  (mm). An even margin is a cage that drags predictably: cv is the spread
  (standard deviation over the mean; 0 = perfectly even). Vertices on a fully
  creased edge are pinned to the surface on purpose and left out (counted).
  The vertices farthest and closest are named.
- poles: vertices whose valence, mirror copies included, is not 4: how many
  of each valence, and where, in fractions of the part's half size from its
  mirror planes (w, d, h), so two cages of different sizes compare.
- dips: the cage_dips check (a vertex inside its neighbours under a convex
  surface, D-043).
- counts: vertices and faces of the cage.

Needs the Mirror > Subdivision stack for the offset (base vertex i is
evaluated vertex i); without it the offset is left out.
"""

import bmesh
import bpy
import numpy as np

from . import mesh_io, topology, validate

AXES = "wdh"


def _depsgraph():
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


def _ids(obj):
    attr = obj.data.attributes.get(mesh_io.ID_ATTR)
    if attr is None or attr.domain != "POINT":
        return list(range(len(obj.data.vertices)))
    return [d.value for d in attr.data]


def _pinned(obj):
    """Indices of vertices on an edge with crease 1."""
    attr = obj.data.attributes.get("crease_edge")
    if attr is None or attr.domain != "EDGE":
        return set()
    return {i for e, c in zip(obj.data.edges, attr.data) if c.value >= 0.99 for i in e.vertices}


def measure(obj):
    """The editability numbers of one object."""
    dg = _depsgraph()
    ids = _ids(obj)
    mirror = mesh_io.mirror_setup(obj)
    per_vertex, all_co, _, _ = mesh_io.evaluated(obj, dg)
    half = np.abs(np.array(all_co, dtype=float)).max(axis=0) if all_co else np.ones(3)
    half[half == 0] = 1.0
    base = np.array([tuple(v.co) for v in obj.data.vertices], dtype=float)
    out = {"object": obj.name, "verts": len(base), "faces": len(obj.data.polygons)}
    if per_vertex is not None:
        d = np.linalg.norm(base - np.array(per_vertex, dtype=float), axis=1) * 1000
        # A vertex on a fully creased edge is pinned to the surface on purpose:
        # it says nothing about how even the margin is.
        pinned = _pinned(obj)
        free = np.array([i for i in range(len(d)) if i not in pinned], dtype=int)
        f = d[free] if len(free) else d
        order = free[np.argsort(f)] if len(free) else np.argsort(d)
        out["offset_mm"] = {"median": round(float(np.median(f)), 2), "p10": round(float(np.percentile(f, 10)), 2),
                            "p90": round(float(np.percentile(f, 90)), 2),
                            "cv": round(float(f.std() / f.mean()), 2) if f.mean() > 1e-6 else None,
                            "pinned": len(pinned),
                            "farthest": [f"v{ids[i]} {d[i]:.1f}" for i in order[::-1][:3]],
                            "closest": [f"v{ids[i]} {d[i]:.1f}" for i in order[:3]]}
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        poles = {}
        for v in bm.verts:
            if not v.link_faces:
                continue
            valence = topology.mirrored_valence(v, mirror)
            if valence == 4:
                continue
            where = " ".join(f"{a}{abs(v.co[k]) / half[k]:.2f}" for k, a in enumerate(AXES))
            poles.setdefault(str(valence), []).append(f"v{ids[v.index]} at {where}")
    finally:
        bm.free()
    out["poles"] = {k: {"count": len(v), "at": v} for k, v in sorted(poles.items())}
    dips = validate.check_editability(obj, ids, dg, mirror)
    out["dips"] = dips[0]["verts"] if dips else []
    return out


def editability(name, ref=None, blend=None):
    """Editability of object `name`, and of `ref` (from `blend` if given) beside it."""
    from .shape import _borrowed, _object

    out = {"this": measure(_object(name))}
    if ref is not None:
        with _borrowed(ref, blend) as other:
            out["ref"] = measure(other)
        a, b = out["this"], out["ref"]
        notes = [f"verts {a['verts']} vs {b['verts']}, faces {a['faces']} vs {b['faces']}"]
        if "offset_mm" in a and "offset_mm" in b:
            notes.append(f"offset median {a['offset_mm']['median']} vs {b['offset_mm']['median']} mm, "
                         f"cv {a['offset_mm']['cv']} vs {b['offset_mm']['cv']}")
        pa = {k: v["count"] for k, v in a["poles"].items()}
        pb = {k: v["count"] for k, v in b["poles"].items()}
        notes.append(f"poles {pa or 'none'} vs {pb or 'none'}")
        notes.append(f"dips {len(a['dips'])} vs {len(b['dips'])}")
        out["compare"] = notes
    return out
