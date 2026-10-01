"""Measure shapes and fit cages to them, in numbers rather than images.

    capture(name)              keep the object's current surface (dense) to fit or compare to later
    fit(name, surface)         write target ops that put each vertex's result on that surface, and sync
    deviation(name, surface)   how far the object's surface is from it (mm)
    profile(name, "top")       the outline seen from a view, band by band (mm)
    sections(name, "w", [...]) cuts across the model: points, superellipse exponent, an image
    compare(name, ref)         sizes, profiles and deviation against a reference object or .blend
    rebuild(name, source, s)   take another object's topology (e.g. the modeler's), fit it to s

Surfaces are measured on a dense copy of the result (Subdivision raised to 3
levels for the measure, then restored), so they are close to the limit
surface whatever the viewport level. Captured surfaces live in memory for the
Blender session; capture(..., path=...) also saves one to a .npz file.
"""

import math
import sys
from contextlib import contextmanager
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import mesh_io, topology

DENSE_LEVELS = 3
AXES = "wdh"
_surfaces = {}


class ShapeError(RuntimeError):
    pass


def _sync_mod():
    # The package exports the function sync under the module's name.
    return sys.modules[f"{__package__}.sync"]


class Surface:
    def __init__(self, co, tris, name):
        self.co = np.asarray(co, dtype=float)
        self.tris = np.asarray(tris, dtype=int)
        self.name = name
        self.bvh = BVHTree.FromPolygons([Vector(c) for c in self.co], self.tris.tolist())

    def size_mm(self):
        return [round(float(np.ptp(self.co[:, k])) * 1000, 1) for k in range(3)]


# --- evaluation ----------------------------------------------------------------

def _depsgraph():
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


@contextmanager
def _levels(obj, levels):
    """Raise every viewport Subdivision of obj to `levels` for the duration."""
    mods = [m for m in obj.modifiers if m.type == "SUBSURF" and m.show_viewport]
    old = [m.levels for m in mods]
    try:
        for m in mods:
            m.levels = max(m.levels, levels)
        yield
    finally:
        for m, lv in zip(mods, old):
            m.levels = lv
        _depsgraph()


def _mesh_arrays(obj):
    # A part mirrored across another object is measured on its own side.
    with mesh_io.one_side(obj):
        ev = obj.evaluated_get(_depsgraph())
        me = ev.to_mesh()
        try:
            me.calc_loop_triangles()
            co = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            nor = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get("normal", nor)
            tris = np.empty(len(me.loop_triangles) * 3, dtype=int)
            me.loop_triangles.foreach_get("vertices", tris)
        finally:
            ev.to_mesh_clear()
    return co.reshape(-1, 3), nor.reshape(-1, 3), tris.reshape(-1, 3)


def dense(obj, levels=DENSE_LEVELS):
    sys.modules[f"{__package__}.rounds"].count("measures")
    with _levels(obj, levels):
        co, _, tris = _mesh_arrays(obj)
    return co, tris


def _object(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ShapeError(f"no mesh object named {name!r}")
    return obj


def _surface(surface):
    if isinstance(surface, Surface):
        return surface
    if surface in _surfaces:
        return _surfaces[surface]
    if isinstance(surface, str) and Path(surface).suffix == ".npz" and Path(surface).exists():
        data = np.load(surface)
        return Surface(data["co"], data["tris"], Path(surface).stem)
    if isinstance(surface, str) and surface in bpy.data.objects:
        co, tris = dense(bpy.data.objects[surface])
        return Surface(co, tris, surface)
    raise ShapeError(f"no captured surface, .npz file or object named {surface!r}")


def capture(name, key=None, path=None, levels=DENSE_LEVELS):
    """Keep the current surface of object `name` under `key` (default: the name)."""
    co, tris = dense(_object(name), levels)
    surf = Surface(co, tris, key or name)
    _surfaces[key or name] = surf
    if path:
        np.savez_compressed(path, co=surf.co, tris=surf.tris)
    return {"key": key or name, "verts": len(co), "tris": len(tris), "size_mm": surf.size_mm()}


# --- measures ------------------------------------------------------------------

def _stats(values):
    v = np.sort(np.asarray(values, dtype=float))
    if not len(v):
        return {}
    pick = lambda q: round(float(v[min(int(q * len(v)), len(v) - 1)]), 2)
    return {"min": round(float(v[0]), 2), "p5": pick(0.05), "median": pick(0.5), "p95": pick(0.95),
            "max": round(float(v[-1]), 2), "mean_abs": round(float(np.abs(v).mean()), 2)}


def deviation(name, surface, levels=DENSE_LEVELS):
    """Signed distance (mm) from the object's dense surface to `surface`:
    positive = outside it. Returns percentiles."""
    co, _ = dense(_object(name), levels)
    return deviation_of(co, surface)


def deviation_of(co, surface):
    """deviation() for points already taken (a dense copy's vertices)."""
    surf = _surface(surface)
    out = []
    for c in co:
        hit, normal, _, dist = surf.bvh.find_nearest(Vector(c))
        if hit is None:
            continue
        sign = 1.0 if (Vector(c) - hit).dot(normal) >= 0 else -1.0
        out.append(sign * dist * 1000)
    return _stats(out)


VIEWS = {"top": (0, 1), "front": (0, 2), "side": (2, 1)}  # (along, measured) axis indices


def profile(name, view="top", bands=20, levels=DENSE_LEVELS, co=None):
    """The outline from a view, band by band along the long axis.

    top: half depth along the width; front: half height along the width;
    side: half depth along the height. Each row: [fraction of the extent,
    largest |measured| in mm, the same near the middle plane of the third
    axis (within 6% of its extent: e.g. the depth at h 0 from the top)].
    Coordinates are taken from the mirror planes, so a mirrored object reads
    the same on either side.
    """
    if co is None:
        co, _ = dense(_object(name), levels)
    along, meas = VIEWS[view]
    third = 3 - along - meas
    a = np.abs(co[:, along])
    m = np.abs(co[:, meas])
    t = np.abs(co[:, third])
    top = a.max()
    rows = []
    for i in range(bands + 1):
        f = i / bands
        sel = np.abs(a / top - f) <= 0.5 / bands
        if not sel.any():
            continue
        mid = sel & (t < 0.06 * t.max())
        rows.append([round(f, 2), round(float(m[sel].max()) * 1000, 1),
                     round(float(m[mid].max()) * 1000, 1) if mid.any() else 0.0])
    return {"view": view, "extent_mm": round(float(top) * 2000, 1), "rows": rows}


def profile_change(co0, co1, min_mm=0.05):
    """How each view's outline changed between two dense copies: per view the
    band that moved most, e.g. "top +0.4 mm at 0.85" (at 85% of the width).
    Views that moved less than min_mm are left out."""
    out = []
    for view in VIEWS:
        a = {f: m for f, m, _ in profile(None, view, co=co0)["rows"]}
        b = {f: m for f, m, _ in profile(None, view, co=co1)["rows"]}
        common = [f for f in a if f in b]
        if not common:
            continue
        f = max(common, key=lambda k: abs(b[k] - a[k]))
        if abs(b[f] - a[f]) >= min_mm:
            out.append(f"{view} {b[f] - a[f]:+.1f} mm at {f:.2f}")
    return out


def superellipse_n(u, v):
    """Exponent n of the superellipse |u/a|^n + |v/b|^n = 1 that best fits the
    points (a, b = the largest |u|, |v|), and the rms radial error."""
    u, v = np.abs(np.asarray(u, float)), np.abs(np.asarray(v, float))
    a, b = u.max(), v.max()
    if a <= 0 or b <= 0:
        return None, None
    best = (None, math.inf)
    for n in np.arange(1.2, 10.01, 0.05):
        r = (np.power(u / a, n) + np.power(v / b, n)) ** (1 / n)
        err = float(np.sqrt(np.mean((r - 1) ** 2)))
        if err < best[1]:
            best = (round(float(n), 2), err)
    return best[0], round(best[1], 3)


def _cut(tris3d, k, c):
    """Segments where the triangles cross the plane coordinate k = c."""
    segs = []
    d = tris3d[:, :, k] - c
    for tri, dd in zip(tris3d, d):
        pts = []
        for i in range(3):
            j = (i + 1) % 3
            if (dd[i] > 0) != (dd[j] > 0):
                t = dd[i] / (dd[i] - dd[j])
                pts.append(tri[i] + t * (tri[j] - tri[i]))
        if len(pts) == 2:
            segs.append(pts)
    return np.array(segs).reshape(-1, 2, 3)


def sections(name, axis="w", at=(250, 500, 750), render=True, levels=DENSE_LEVELS):
    """Cuts across the model at frame values `at` (permille) of `axis`.

    Per cut: the result's superellipse exponent and size in the two other
    axes (permille), the waist (the first other axis where the second one is
    0, e.g. the depth at h 0, and its ratio to the largest), and the base
    vertices within 3% of the plane. With
    render, writes <object>.sections.png: one panel per cut with the result's
    section (orange), the cage's section (dark) and those vertices labeled.
    """
    from . import render as render_mod
    sync_mod = _sync_mod()

    obj = _object(name)
    frame = _frame(obj)
    k = AXES.index(axis)
    others = [i for i in range(3) if i != k]
    co, tris = dense(obj, levels)
    ev_tris = co[tris]
    scene = render_mod.Scene(obj, _ids(obj), _depsgraph())
    out, panels = [], []
    for value in at:
        c = frame.axes[k].to_local(value)
        segs = _cut(ev_tris, k, c)
        cage_segs = _cut(scene.cage_tris, k, c)
        entry = {"at": value, "points": len(segs)}
        if len(segs):
            pts = segs.reshape(-1, 3)
            n, rms = superellipse_n(pts[:, others[0]], pts[:, others[1]])
            vals = np.array([frame.to_values(p) for p in pts])
            entry.update(n=n, rms=rms, size={AXES[i]: int(round(float(np.abs(vals[:, i]).max()))) for i in others})
            # The waist: the first other axis where the second crosses its mirror
            # plane (e.g. the depth at h 0 across w: how deep the pinch goes).
            u, v = np.abs(vals[:, others[0]]), np.abs(vals[:, others[1]])
            near_mid = v < 0.03 * v.max()
            if near_mid.any():
                entry["waist"] = {AXES[others[0]]: int(round(float(u[near_mid].max()))),
                                  "ratio": round(float(u[near_mid].max() / u.max()), 2)}
        near = [vid for vid, base in zip(scene.labels, scene.base) if abs(base[k] - c) < frame.axes[k].extent * 0.03]
        entry["cage_vertices"] = [int(v) for v in near]
        out.append(entry)
        if render:
            panels.append(render_mod.section_panel(scene, axis, c, segs, cage_segs, frame, entry))
    report = {"object": name, "axis": axis, "sections": out}
    if render and panels:
        path = sync_mod.paths(obj)["render"].with_name(f"{sync_mod.paths(obj)['render'].stem}.sections.png")
        title = f"{obj.name}   sections across {axis}"
        report["render"] = str(render_mod.compose_row(panels, title, path))
    return report


def _frame(obj):
    sync_mod = _sync_mod()
    state = sync_mod._load_state(sync_mod.paths(obj)["state"])
    if state is None or state["frame"] is None:
        raise ShapeError(f"sync {obj.name} first: the frame lives in its sync state")
    return state["frame"]


def _ids(obj):
    ids, _ = mesh_io.ensure_ids(obj.data, write=False)
    return ids


# --- fitting -------------------------------------------------------------------

def _evaluated_with_normals(obj):
    co, nor, _ = _mesh_arrays(obj)
    return co, nor


def fit_lines(obj, surface, mode="normal", vids=None, reach=0.25):
    """Target op lines that put each vertex's result on the surface.

    mode normal: along the result's normal at the vertex (the nearest hit
    either way, within `reach` of the frame's largest extent); radial: along
    the ray from the object's center; nearest: the closest surface point.
    Axes across a mirror plane the vertex lies on are left out.
    """
    from . import cage_format
    sync_mod = _sync_mod()

    surf = _surface(surface)
    frame = _frame(obj)
    p = sync_mod.paths(obj)
    cage = cage_format.parse(p["text"].read_text("utf-8"))
    ids = _ids(obj)
    index = {vid: i for i, vid in enumerate(ids)}
    co, nor = _evaluated_with_normals(obj)
    span = max(a.extent for a in frame.axes) * 2 * reach
    lines = []
    for vid, v in cage.verts.items():
        if vids is not None and vid not in vids:
            continue
        i = index[vid]
        c = Vector(co[i])
        hit = None
        if mode == "radial":
            d = c.normalized()
            hit = surf.bvh.ray_cast(d * span * 4, -d)[0]
        elif mode == "normal":
            n = Vector(nor[i]).normalized()
            hits = [surf.bvh.ray_cast(c, n * s, span)[0] for s in (1, -1)]
            hits = [h for h in hits if h is not None]
            hit = min(hits, key=lambda h: (h - c).length) if hits else None
        if hit is None:
            hit = surf.bvh.find_nearest(c)[0]
        if hit is None:
            continue
        vals = frame.to_values(hit)
        planes = "".join(v.flags)
        pairs = [f"{a} {vals[k]:.1f}" for k, a in enumerate(AXES) if "XYZ"[k] not in planes]
        if pairs:
            lines.append(f"target v{vid} " + " ".join(pairs))
    return lines


def fit(name, surface, mode="normal", vids=None, passes=3):
    """Fit the cage to a surface: target ops written to the text and synced,
    `passes` times (each pass re-aims from the new result). Returns the last
    sync report's issues and the deviation from the surface."""
    sync_mod = _sync_mod()

    obj = _object(name)
    p = sync_mod.paths(obj)
    log = []
    for _ in range(passes):
        lines = fit_lines(obj, surface, mode, vids)
        text = p["text"].read_text("utf-8")
        p["text"].write_text(text.replace("\nops\n", "\nops\n" + "".join(f"  {l}\n" for l in lines), 1), "utf-8")
        r = sync_mod.sync(name, render=False)
        if r["action"] in ("error", "conflict"):
            return {"error": r.get("error") or r["action"], "report": r}
        log.append([i for i in r["issues"] if i["code"] != "target_not_reached"])
    sync_mod.sync(name)  # render the sheet once at the end
    return {"passes": passes, "targets": len(lines), "issues": log[-1] if log else [],
            "deviation_mm": deviation(name, surface)}


# --- comparing with a reference -----------------------------------------------

@contextmanager
def _borrowed(ref, blend=None):
    """The reference object, appended from `blend` for the duration if given."""
    if blend is None:
        yield _object(ref)
        return
    before = set(bpy.data.objects)
    libs_before = set(bpy.data.libraries)
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        if ref not in src.objects:
            raise ShapeError(f"no object {ref!r} in {blend}")
        dst.objects = [ref]
    obj = dst.objects[0]
    bpy.context.scene.collection.objects.link(obj)
    try:
        yield obj
    finally:
        for o in set(bpy.data.objects) - before:
            mesh = o.data if o.type == "MESH" else None
            bpy.data.objects.remove(o)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for lib in set(bpy.data.libraries) - libs_before:  # appending leaves the library behind
            bpy.data.libraries.remove(lib)


def compare(name, ref, blend=None):
    """Numbers against a reference: sizes, the top / front / side profiles
    side by side and the deviation of this object's surface from the
    reference's. ref: an object name, from `blend` if given."""
    obj = _object(name)
    mine, _ = dense(obj)
    with _borrowed(ref, blend) as other:
        theirs, their_tris = dense(other)
    surf = Surface(theirs, their_tris, ref)
    out = {"size_mm": {"this": [round(float(np.ptp(mine[:, k])) * 1000, 1) for k in range(3)],
                       "ref": surf.size_mm()}}
    for view in VIEWS:
        a, b = profile(None, view, co=mine), profile(None, view, co=theirs)
        rows = [[ra[0], ra[1], rb[1], ra[2], rb[2]] for ra, rb in zip(a["rows"], b["rows"]) if ra[0] == rb[0]]
        out[view] = {"columns": "fraction, this, ref, this at mid plane, ref at mid plane (mm)", "rows": rows}
    out["deviation_mm"] = deviation(name, surf)
    return out


# --- rebuilding from another topology ----------------------------------------------

def rebuild(name, source, surface, blend=None, mode="normal", passes=3):
    """Replace the mesh of `name` with the topology of `source` and fit it to `surface`.

    The source's vertices are mirrored to this object's kept sides and scaled
    so the source's result spans the surface; faces are rewound when an odd
    number of axes flip; the source's UVs come along; materials stay. The next
    sync pulls the new mesh (fresh ids), then fit() runs.
    """
    sync_mod = _sync_mod()

    obj = _object(name)
    surf = _surface(surface)
    mirror = mesh_io.mirror_setup(obj)
    sides = mesh_io.kept_sides(obj.data, mirror)
    with _borrowed(source, blend) as src:
        src_mirror = mesh_io.mirror_setup(src)
        src_sides = mesh_io.kept_sides(src.data, src_mirror)
        src_co, _ = dense(src)
        verts = [tuple(v.co) for v in src.data.vertices]
        faces = [list(pl.vertices) for pl in src.data.polygons]
        uv = src.data.uv_layers.active
        uvs = [[tuple(uv.data[li].uv) for li in pl.loop_indices] for pl in src.data.polygons] if uv else None
    flip = [1.0] * 3
    for k, a in enumerate(topology.AXES):
        if sides.get(a) in "+-" and src_sides.get(a) in "+-" and sides[a] != src_sides[a]:
            flip[k] = -1.0
    ratio = [float(np.ptp(surf.co[:, k]) / max(np.ptp(src_co[:, k]), 1e-9)) for k in range(3)]
    rewind = np.prod(flip) < 0
    bm = bmesh.new()
    try:
        layer = bm.loops.layers.uv.new("UVMap") if uvs else None
        bv = [bm.verts.new(tuple(c * f * r for c, f, r in zip(v, flip, ratio))) for v in verts]
        for f, fuv in zip(faces, uvs or [None] * len(faces)):
            order = f[::-1] if rewind else f
            face = bm.faces.new([bv[i] for i in order])
            if layer is not None:
                for loop, t in zip(face.loops, fuv[::-1] if rewind else fuv):
                    loop[layer].uv = t
        bm.normal_update()
        bm.to_mesh(obj.data)
    finally:
        bm.free()
    obj.data.update()
    pulled = sync_mod.sync(name, render=False)
    result = fit(name, surf, mode=mode, passes=passes)
    result["pulled"] = pulled["action"]
    result["count"] = f"{len(obj.data.vertices)} vertices, {len(obj.data.polygons)} faces per part"
    return result
