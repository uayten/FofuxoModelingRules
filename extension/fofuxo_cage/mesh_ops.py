"""The mesh op: run Blender's own mesh operators on a selection by cage id.

    mesh <operator> <selection> [key=value ...]
    mesh dissolve_edges seam
    mesh loopcut_slide ring v25-v22 number_cuts=2
    mesh vertices_smooth v24 v25 v26 factor=0.5 repeat=2
    mesh translate seam d=+2% falloff=smooth radius=20%

The selection grammar is in selection.py. Only the operators in OPS run,
with the parameters written there (meaning and unit); anything else is
refused with the list. Running: the object is locked (which leaves Edit
Mode for the human), enters Edit Mode, the selection is set by id, the
operator runs under a 3D View override, the object leaves Edit Mode.
Vertices the operator made get fresh ids. The mesh is checked after (quads
under Subdivision, no loose geometry, mirror planes) and restored if a check
fails. The whole batch runs first on a temporary copy of the object, so a
refused op changes nothing.

Aliases, kept from before the mesh op:
    dissolve <selection>   remove the edge loop: dissolve_edges (a loop that
                           turns at a pole takes the pole's last spoke with it)
    cut <vA-vB> [N]        loopcut_slide with N cuts across the ring of vA-vB
    crease <selection> <value>   set the edges' crease weight

LoopTools (circle, relax, space...) is a Blender extension; ensure_looptools
enables it or installs it from extensions.blender.org.
"""

import math
import random
import re
from contextlib import contextmanager
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

from . import mesh_io, selection, validate
from .lock import PROP as LOCK_PROP, _leave_edit_mode, lock, unlock
from .selection import SelectionError

TAG_ATTR = "fofuxo_cage_tag"
LENGTH_UNITS = {"mm": 0.001, "cm": 0.01, "m": 1.0}
LOOPTOOLS = "looptools"
MAX_DELTAS = 10


class MeshOpError(ValueError):
    pass


# --- LoopTools -----------------------------------------------------------------

def _has_op(op):
    try:
        op.get_rna_type()
        return True
    except (KeyError, AttributeError, RuntimeError):
        return False


def ensure_looptools():
    """Make LoopTools' operators available: enable the extension if it is on
    disk in any repository, else install it from extensions.blender.org
    (online access is turned on for the install and restored after)."""
    import addon_utils

    if _has_op(bpy.ops.mesh.looptools_circle):
        return {"looptools": "enabled"}
    repos = bpy.context.preferences.extensions.repos
    for repo in repos:
        if repo.enabled and repo.directory and (Path(repo.directory) / LOOPTOOLS / "__init__.py").exists():
            addon_utils.enable(f"bl_ext.{repo.module}.{LOOPTOOLS}", default_set=True, handle_error=None)
            if _has_op(bpy.ops.mesh.looptools_circle):
                return {"looptools": f"enabled from {repo.module}"}
    index = next((i for i, r in enumerate(repos) if r.use_remote_url and "extensions.blender.org" in r.remote_url), None)
    if index is None:
        raise MeshOpError("LoopTools is missing and there is no extensions.blender.org repository to install it from")
    system = bpy.context.preferences.system
    was_online = system.use_online_access
    try:
        system.use_online_access = True
        if not bpy.app.online_access:
            raise MeshOpError("LoopTools is missing and Blender runs offline (--offline-mode): install LoopTools "
                              "from Get Extensions")
        bpy.ops.extensions.repo_sync(repo_index=index)
        bpy.ops.extensions.package_install(repo_index=index, pkg_id=LOOPTOOLS, enable_on_install=True)
    finally:
        system.use_online_access = was_online
    if not _has_op(bpy.ops.mesh.looptools_circle):
        raise MeshOpError("LoopTools install did not register its operators")
    return {"looptools": "installed from extensions.blender.org"}


# --- parameters ----------------------------------------------------------------

class P:
    """A parameter the text may set: its Blender property, meaning and unit.

    unit: "bool", "int", "float", "factor" (0 to 1), "enum", "length" (mm, cm,
    m, or % of the frame's largest axis) or "axis" (a move along a frame axis:
    % of that axis or mm; positive away from a mirror plane).
    """

    def __init__(self, prop, unit, meaning):
        self.prop, self.unit, self.meaning = prop, unit, meaning


def _number(raw, key):
    try:
        return float(raw)
    except ValueError:
        raise MeshOpError(f"{key} takes a number, not {raw!r}") from None


def _length(raw, key, frame, axis=None):
    """A length in local units (m) from '2mm' or '12%' (of the frame axis, or its largest one)."""
    m = re.fullmatch(r"([-+]?\d*\.?\d+)\s*(mm|cm|m|%)", raw.lower())
    if not m:
        raise MeshOpError(f"{key} is a length: write it with a unit (2mm) or in % of the frame (5%), not {raw!r}")
    if m[2] != "%":
        return float(m[1]) * LENGTH_UNITS[m[2]]
    if frame is None:
        raise MeshOpError(f"{key} in % needs the frame")
    extent = frame.axes[axis].extent if axis is not None else max(a.extent for a in frame.axes)
    return float(m[1]) / 100 * extent


def _value(param, raw, key, rna, frame):
    unit = param.unit
    if unit == "bool":
        low = raw.lower()
        if low in ("on", "true", "1", "yes"):
            return True
        if low in ("off", "false", "0", "no"):
            return False
        raise MeshOpError(f"{key} takes on or off, not {raw!r}")
    if unit == "int":
        if not re.fullmatch(r"[-+]?\d+", raw):
            raise MeshOpError(f"{key} takes a whole number, not {raw!r}")
        return int(raw)
    if unit in ("float", "factor"):
        v = _number(raw, key)
        if unit == "factor" and not 0.0 <= v <= 1.0:
            raise MeshOpError(f"{key} takes a factor from 0 to 1, not {raw!r}")
        return v
    if unit == "enum":
        prop = rna.properties[param.prop] if rna is not None else None
        items = [i.identifier for i in prop.enum_items] if prop is not None else []
        chosen = raw.split(",") if prop is not None and prop.is_enum_flag else [raw]
        # Any case: LoopTools' items are lower case, Blender's upper.
        matches = [next((i for i in items if i.lower() == c.lower()), None) for c in chosen]
        if None in matches:
            raise MeshOpError(f"{key} takes {'one or more of' if len(chosen) > 1 or prop.is_enum_flag else 'one of'} "
                              f"{[i.lower() for i in items]}, not {raw!r}")
        return set(matches) if prop.is_enum_flag else matches[0]
    if unit == "angle":
        m = re.fullmatch(r"([-+]?\d*\.?\d+)\s*(deg|rad)", raw.lower())
        if not m:
            raise MeshOpError(f"{key} is an angle: write it with a unit, e.g. 5deg, not {raw!r}")
        return math.radians(float(m[1])) if m[2] == "deg" else float(m[1])
    if unit == "length":
        return _length(raw, key, frame)
    if unit == "percent":
        m = re.fullmatch(r"(\d*\.?\d+)%", raw)
        if not m:
            raise MeshOpError(f"{key} takes a percentage like 150%, not {raw!r}")
        return float(m[1]) / 100
    if unit == "text":
        if not re.fullmatch(r"[\w .-]+", raw):
            raise MeshOpError(f"{key} takes a name, not {raw!r}")
        return raw
    if unit == "choice":
        if raw.lower() not in ("above", "below", "none"):
            raise MeshOpError(f"{key} takes above, below or none, not {raw!r}")
        return raw.lower()
    if unit == "pivot":
        if raw.lower() not in ("origin", "selection"):
            raise MeshOpError(f"{key} takes origin or selection, not {raw!r}")
        return raw.lower()
    if unit == "letter":
        if raw.lower() not in ("w", "d", "h"):
            raise MeshOpError(f"{key} takes a frame axis: w, d or h, not {raw!r}")
        return "wdh".index(raw.lower())
    if unit == "plane":
        m = re.fullmatch(r"([wdh])(-?\d*\.?\d+)(%?)", raw.lower())
        if not m or frame is None:
            raise MeshOpError(f"{key} takes a frame axis and a value in permille or %, e.g. h920 or h92%, "
                              f"not {raw!r}")
        k = "wdh".index(m[1])
        return k, frame.axes[k].to_local(float(m[2]) * (10 if m[3] else 1))
    if unit == "axis":
        k = "wdh".index(key)
        sign = -1.0 if frame is not None and frame.axes[k].side == "-" else 1.0  # + moves away from the plane
        return sign * _length(raw, key, frame, k)
    raise MeshOpError(f"{key}: unknown unit {unit}")


# --- the whitelist -------------------------------------------------------------

class Op:
    """A whitelisted operator. needs: the element kind the selection must
    hold (VERT, EDGE, FACE, SEED for one edge, or None)."""

    def __init__(self, idname, needs, doc, params=None, defaults=None, build=None, rna=None, looptools=False,
                 call=None):
        self.idname, self.needs, self.doc = idname, needs, doc
        self.call = call  # runs several operators in a row (extract)
        self.params = params or {}
        self.defaults = defaults or {}
        self.build = build
        self.rna_of = rna
        self.looptools = looptools

    def op(self):
        area, name = self.idname.split(".")
        return getattr(getattr(bpy.ops, area), name)

    def rna(self):
        if self.rna_of is not None:
            return self.rna_of()
        return self.op().get_rna_type() if _has_op(self.op()) else None

    def kwargs(self, values, sel, obj):
        if self.build is not None:
            return self.build(self, values, sel, obj)
        return _plain(self, values, obj)


def _plain(op, values, obj):
    """The operator's defaults and the parameters, lengths in Blender units."""
    scale = max(obj.matrix_world.to_scale())
    out = dict(op.defaults)
    out.update({op.params[k].prop: v * scale if op.params[k].unit == "length" else v for k, v in values.items()})
    return out


def _loopcut(op, values, sel, obj):
    cut = {"number_cuts": values.get("number_cuts", 1), "smoothness": values.get("smoothness", 0.0),
           "falloff": values.get("falloff", "INVERSE_SQUARE"), "edge_index": sel["seed"], "object_index": 0}
    return {"MESH_OT_loopcut": cut, "TRANSFORM_OT_edge_slide": {"value": values.get("slide", 0.0)}}


def _proportional(values, obj):
    if "falloff" not in values and "radius" not in values:
        return {"use_proportional_edit": False}
    scale = max(obj.matrix_world.to_scale())
    return {"use_proportional_edit": True,
            "proportional_edit_falloff": values.get("falloff", "SMOOTH"),
            "proportional_size": values.get("radius", 0.01) * scale,
            "use_proportional_connected": values.get("connected", False),
            "use_proportional_projected": False}


def _translate(op, values, sel, obj):
    local = Vector([values.get(a, 0.0) for a in "wdh"])
    return {"value": tuple(obj.matrix_world.to_3x3() @ local), "orient_type": "GLOBAL",
            "mirror": False, "snap": False, **_proportional(values, obj)}


def _transform(op, values, sel, obj):
    """A transform operator: its parameters in Blender units, no snapping, and
    proportional editing when the operator takes it."""
    scale = max(obj.matrix_world.to_scale())
    out = {"mirror": False, "snap": False, **op.defaults}
    for key, v in values.items():
        if key not in PROPORTIONAL:
            p = op.params[key]
            out[p.prop] = v * scale if p.unit == "length" else v
    if "falloff" in op.params:
        out.update(_proportional(values, obj))
    return out


def _circle(op, values, sel, obj):
    out = _plain(op, values, obj)
    if "radius" in values:
        out["custom_radius"] = True
    return out


def _axis_world(obj, k):
    """A frame axis (0 w, 1 d, 2 h) as a world direction."""
    return tuple((obj.matrix_world.to_3x3() @ Vector([1.0 if i == k else 0.0 for i in range(3)])).normalized())


def _extrude_move(kind):
    def build(op, values, sel, obj):
        local = Vector([values.get(a, 0.0) for a in "wdh"])
        return {f"MESH_OT_{kind}": {}, "TRANSFORM_OT_translate": {
            "value": tuple(obj.matrix_world.to_3x3() @ local), "orient_type": "GLOBAL", "mirror": False, "snap": False}}
    return build


def _pivot(values, obj):
    """Where a resize or rotate turns: the object's origin (where its mirror
    planes meet) or the middle of the selected vertices (a ring on a horn)."""
    if values.get("around", "origin") == "origin":
        return tuple(obj.matrix_world.translation)
    bm = bmesh.from_edit_mesh(obj.data)
    picked = [v.co for v in bm.verts if v.select]
    if not picked:
        raise MeshOpError("around=selection needs a selection")
    return tuple(obj.matrix_world @ (sum(picked, Vector()) / len(picked)))


def _resize(op, values, sel, obj):
    """Scale along the frame axes around the object's origin or the selection's middle."""
    return {"value": tuple(values.get(a, 1.0) for a in "wdh"), "orient_type": "LOCAL",
            "center_override": _pivot(values, obj), "mirror": False, "snap": False,
            **_proportional(values, obj)}


def _rotate(op, values, sel, obj):
    """Turn around a frame axis through the selection's middle (default) or the object's origin."""
    if "angle" not in values:
        raise MeshOpError("rotate needs an angle, e.g. angle=15deg")
    pivot = _pivot({"around": "selection", **values}, obj)
    # Blender's rotate turns clockwise seen from the axis' + end; the op follows the right-hand rule.
    return {"value": -values["angle"], "orient_axis": "XYZ"[values.get("axis", 0)], "orient_type": "LOCAL",
            "center_override": pivot, "mirror": False, "snap": False, **_proportional(values, obj)}


def _extrude_fatten(op, values, sel, obj):
    scale = max(obj.matrix_world.to_scale())
    return {"MESH_OT_extrude_region": {}, "TRANSFORM_OT_shrink_fatten": {
        "value": values.get("value", 0.0) * scale, "use_even_offset": values.get("even", True)}}


def _around(op, values, sel, obj):
    """spin and screw: around a frame axis through the object's origin (where its mirror planes meet)."""
    out = {k: v for k, v in _plain(op, {k: v for k, v in values.items() if k != "axis"}, obj).items()}
    out["axis"] = _axis_world(obj, values.get("axis", 2))
    out["center"] = tuple(obj.matrix_world.translation)
    return out


def _bisect(op, values, sel, obj):
    if "plane" not in values:
        raise MeshOpError("bisect needs a plane: plane=h250 (an axis and a value in permille of the frame)")
    k, c = values["plane"]
    local = Vector([c if i == k else 0.0 for i in range(3)])
    keep = values.get("clear", "none")
    return {"plane_co": tuple(obj.matrix_world @ local), "plane_no": _axis_world(obj, k),
            "use_fill": values.get("fill", False), "clear_inner": keep == "below", "clear_outer": keep == "above"}


def _extrude_scale(kwargs):
    """Extrude the selection, then scale the new part around the object's origin
    (in Blender: E, then S, Shift+Z for X and Y only)."""
    if "FINISHED" not in bpy.ops.mesh.extrude_region(mirror=False):
        return {"CANCELLED"}
    return bpy.ops.transform.resize(**kwargs)


def _symmetric(bm, new_verts, rim, tol=1e-5):
    """Is the filled grid mirror symmetric across the X and Y planes through the rim's center?"""
    import numpy as np

    pts = np.array([tuple(v.co) for v in new_verts] + [tuple(v.co) for v in rim])
    center = np.array([tuple(v.co) for v in rim]).mean(axis=0)
    rel = pts - center
    for k in (0, 1):
        flipped = rel.copy()
        flipped[:, k] = -flipped[:, k]
        d = np.linalg.norm(flipped[:, None, :] - rel[None, :, :], axis=2).min(axis=1)
        if d.max() > tol:
            return False
    return True


def fill_grid_aligned(**kwargs):
    """Grid Fill the selected loop, turned so its lines run through the loop's
    extreme vertices on X and Y: the mesh could be cut in quarters and rebuilt
    with Mirror (the modeler's good practice). Tries each turn of the grid and
    keeps the first mirror symmetric on both; none is: the plain fill. An
    explicit offset is used as given."""
    import bmesh

    if "offset" in kwargs:
        return bpy.ops.mesh.fill_grid(**kwargs)
    obj = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(obj.data)
    rim_keys = [tuple(round(c, 7) for c in v.co) for v in bm.verts if v.select]
    count = len(bm.verts)
    for offset in range(len(rim_keys)):
        result = bpy.ops.mesh.fill_grid(offset=offset, **kwargs)
        if "FINISHED" not in result:
            return result
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        keys = set(rim_keys)
        rim = [v for v in bm.verts if tuple(round(c, 7) for c in v.co) in keys]
        if _symmetric(bm, list(bm.verts)[count:], rim):
            return result
        bpy.ops.mesh.delete(type="FACE")  # the fill's faces (still selected) and its inner vertices
        _select_rim(obj, rim_keys)
    return bpy.ops.mesh.fill_grid(offset=0, **kwargs)


def _select_rim(obj, rim_keys):
    import bmesh

    bm = bmesh.from_edit_mesh(obj.data)
    keys = set(rim_keys)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select_set(False)
    for e in bm.edges:
        if all(tuple(round(c, 7) for c in v.co) in keys for v in e.verts) and len(e.link_faces) < 2:
            e.select_set(True)
    bmesh.update_edit_mesh(obj.data)

def _vertex_group(assign):
    def call(kwargs):
        """Put the selected vertices in (or take them out of) a vertex group, made if missing."""
        obj = bpy.context.edit_object
        name = kwargs.get("group", "Group")
        group = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        obj.vertex_groups.active_index = group.index
        if not assign:
            return bpy.ops.object.vertex_group_remove_from()
        bpy.context.tool_settings.vertex_group_weight = kwargs.get("weight", 1.0)
        return bpy.ops.object.vertex_group_assign()
    return call


def _extract(kwargs):
    """Duplicate the selection and separate the copy into a new object (D-029)."""
    if "FINISHED" not in bpy.ops.mesh.duplicate():
        return {"CANCELLED"}
    return bpy.ops.mesh.separate(type="SELECTED")


PROPORTIONAL = {
    "falloff": P("proportional_edit_falloff", "enum", "proportional editing falloff (turns it on): smooth, sphere, "
                                                      "root, inverse_square, sharp, linear, constant, random"),
    "radius": P("proportional_size", "length", "proportional editing radius (turns it on); default 10 mm"),
    "connected": P("use_proportional_connected", "bool", "falloff only through connected geometry"),
}

OPS = {
    "dissolve_edges": Op("mesh.dissolve_edges", "EDGE", "remove the edges; the faces on both sides merge", {
        "use_verts": P("use_verts", "bool", "also dissolve vertices left with two edges (default on)"),
        "use_face_split": P("use_face_split", "bool", "split off faces around the dissolved vertices"),
    }, defaults={"use_verts": True}),
    "dissolve_verts": Op("mesh.dissolve_verts", "VERT", "remove the vertices; their faces merge", {
        "use_face_split": P("use_face_split", "bool", "split off faces around the dissolved vertices"),
        "use_boundary_tear": P("use_boundary_tear", "bool", "split off boundary faces"),
    }),
    "delete_edgeloop": Op("mesh.delete_edgeloop", "EDGE", "delete an edge loop, sliding its neighbours together", {
        "use_face_split": P("use_face_split", "bool", "split off faces around the dissolved vertices"),
    }),
    "loopcut_slide": Op("mesh.loopcut_slide", "SEED", "cut new loops across the ring of the first edge named", {
        "number_cuts": P("number_cuts", "int", "how many loops (default 1)"),
        "smoothness": P("smoothness", "float", "bulge of the new loops (default 0, flat)"),
        "falloff": P("falloff", "enum", "profile of the smoothness"),
        "slide": P("value", "float", "edge slide after the cut, -1 to 1 (default 0, halfway)"),
    }, build=_loopcut, rna=lambda: bpy.ops.mesh.loopcut.get_rna_type()),
    "subdivide_edgering": Op("mesh.subdivide_edgering", "EDGE", "cut loops across a selected edge ring", {
        "number_cuts": P("number_cuts", "int", "how many loops (default 1)"),
        "smoothness": P("smoothness", "float", "bulge of the new loops (default 0)"),
        "interpolation": P("interpolation", "enum", "path, surface or linear"),
    }, defaults={"number_cuts": 1, "smoothness": 0.0}),
    "vertices_smooth": Op("mesh.vertices_smooth", "VERT", "move the vertices toward their neighbours' average", {
        "factor": P("factor", "factor", "how far per pass, 0 to 1 (default 0.5)"),
        "repeat": P("repeat", "int", "passes (default 1)"),
        "xaxis": P("xaxis", "bool", "smooth along X (w)"),
        "yaxis": P("yaxis", "bool", "smooth along Y (d)"),
        "zaxis": P("zaxis", "bool", "smooth along Z (h)"),
    }),
    "translate": Op("transform.translate", "VERT", "move the selection along the frame axes, optionally with "
                                                   "proportional editing (the neighbours follow with a falloff)", {
        "w": P("value", "axis", "move along w: % of the frame's w or mm, + away from the mirror plane"),
        "d": P("value", "axis", "move along d, as w"),
        "h": P("value", "axis", "move along h, as w"),
        **PROPORTIONAL,
    }, build=_translate),
    # Phase 2: shaping a region the way a modeler would.
    "edge_slide": Op("transform.edge_slide", "EDGE", "slide an edge loop along the faces beside it: the loop moves, "
                                                     "the surface it rests on stays", {
        "factor": P("value", "float", "how far, -1 to 1 (toward one neighbour loop or the other)"),
        "even": P("use_even", "bool", "keep the loop's shape (even) instead of a fraction per edge"),
        "flipped": P("flipped", "bool", "measure even from the other side"),
        "clamp": P("use_clamp", "bool", "stay between the neighbour loops (default on)"),
    }, build=_transform),
    "vert_slide": Op("transform.vert_slide", "VERT", "slide vertices along one of their edges", {
        "factor": P("value", "float", "how far along the edge, -1 to 1"),
        "even": P("use_even", "bool", "even distance"),
        "flipped": P("flipped", "bool", "measure from the other end"),
        "clamp": P("use_clamp", "bool", "stay on the edge (default on)"),
    }, build=_transform),
    "shrink_fatten": Op("transform.shrink_fatten", "VERT", "move the selection along its normals: inflate (+) "
                                                           "or thin (-) a region evenly", {
        "value": P("value", "length", "how far, mm or % of the frame's largest axis; + outward"),
        "even": P("use_even_offset", "bool", "keep the thickness even at corners"),
        **PROPORTIONAL,
    }, build=_transform),
    "push_pull": Op("transform.push_pull", "VERT", "move the selection toward (-) or away from (+) its center", {
        "value": P("value", "length", "how far, mm or % of the frame's largest axis"),
        **PROPORTIONAL,
    }, build=_transform),
    "tosphere": Op("transform.tosphere", "VERT", "round the selection toward a sphere around its center", {
        "factor": P("value", "factor", "0 (as is) to 1 (a sphere)"),
        **PROPORTIONAL,
    }, build=_transform),
    "looptools_circle": Op("mesh.looptools_circle", "EDGE", "make a closed loop round (LoopTools): a round "
                                                              "section; a loop cut by a mirror plane is not a circle", {
        "fit": P("fit", "enum", "best (a circle through the loop) or inside"),
        "flatten": P("flatten", "bool", "also flatten the loop onto a plane (default on)"),
        "influence": P("influence", "float", "how far, 0 to 100 (%)"),
        "radius": P("radius", "length", "a set radius, mm or %"),
        "regular": P("regular", "bool", "spread the vertices evenly on the circle"),
        "lock_x": P("lock_x", "bool", "keep X (w)"), "lock_y": P("lock_y", "bool", "keep Y (d)"),
        "lock_z": P("lock_z", "bool", "keep Z (h)"),
    }, build=_circle, looptools=True),
    "looptools_relax": Op("mesh.looptools_relax", "EDGE", "even out a loop's curvature (LoopTools)", {
        "iterations": P("iterations", "enum", "1, 3, 5, 10 or 25"),
        "interpolation": P("interpolation", "enum", "cubic or linear"),
        "regular": P("regular", "bool", "spread the vertices evenly"),
    }, defaults={"input": "selected"}, looptools=True),
    "looptools_space": Op("mesh.looptools_space", "EDGE", "space a loop's vertices evenly along it (LoopTools)", {
        "influence": P("influence", "float", "how far, 0 to 100 (%)"),
        "interpolation": P("interpolation", "enum", "cubic or linear"),
        "lock_x": P("lock_x", "bool", "keep X (w)"), "lock_y": P("lock_y", "bool", "keep Y (d)"),
        "lock_z": P("lock_z", "bool", "keep Z (h)"),
    }, defaults={"input": "selected"}, looptools=True),
    "symmetrize": Op("mesh.symmetrize", None, "copy one side of the mesh onto the other (a part modeled whole)", {
        "direction": P("direction", "enum", "negative_x, positive_x, ... (the side copied from, to the other)"),
        "threshold": P("threshold", "length", "merge distance on the plane"),
    }),
    "symmetry_snap": Op("mesh.symmetry_snap", None, "snap vertices to their mirror counterparts", {
        "direction": P("direction", "enum", "negative_x, positive_x, ..."),
        "threshold": P("threshold", "length", "how far a counterpart may be"),
        "factor": P("factor", "factor", "0 to 1: how far toward the mirrored position"),
        "use_center": P("use_center", "bool", "snap middle vertices onto the plane"),
    }),
    # Phase 1: the rest of the topology tools.
    "offset_edge_loops_slide": Op("mesh.offset_edge_loops_slide", "EDGE", "two new loops on either side of the "
                                  "selected one, slid apart (a loop that ends on a mirror plane leaves triangles: "
                                  "refused)", {
        "cap": P("use_cap_endpoint", "bool", "extend the loop's open ends"),
        "slide": P("value", "float", "how far apart, -1 to 1"),
    }, build=lambda op, values, sel, obj: {
        "MESH_OT_offset_edge_loops": {"use_cap_endpoint": values.get("cap", False)},
        "TRANSFORM_OT_edge_slide": {"value": values.get("slide", 0.5)}},
        rna=lambda: _merged_rna(bpy.ops.mesh.offset_edge_loops, bpy.ops.transform.edge_slide)),
    "space_edge_loops_evenly": Op("mesh.space_edge_loops_evenly", "EDGE", "space parallel loops evenly between "
                                  "the outer two: select the rings across them, two or more deep "
                                  "(ring vA-vB ring vB-vC), not the loops", {
        "factor": P("factor", "float", "how far toward even, 0 to 1"),
        "interpolation": P("interpolation", "enum", "the curve along the ring"),
        "lock": P("lock", "bool", "keep the loops' shape"),
    }),
    "dissolve_limited": Op("mesh.dissolve_limited", None, "dissolve edges and vertices flatter than an angle: a "
                           "lighter cage where it carries no shape (D-045)", {
        "angle_limit": P("angle_limit", "angle", "the angle below which an edge goes, e.g. 5deg"),
        "use_dissolve_boundaries": P("use_dissolve_boundaries", "bool", "also on open borders"),
        "delimit": P("delimit", "enum", "keep edges that are normal, material, seam, sharp or uv borders "
                                        "(comma-separated)"),
    }),
    "unsubdivide": Op("mesh.unsubdivide", None, "undo a grid's subdivisions", {
        "iterations": P("iterations", "int", "how many times (default 2)"),
    }),
    "edge_collapse": Op("mesh.edge_collapse", "EDGE", "collapse each edge to one vertex at its middle"),
    "merge": Op("mesh.merge", "VERT", "merge the selected vertices into one", {
        "type": P("type", "enum", "center, first, last or collapse (each connected group)"),
    }, defaults={"type": "CENTER"}),
    "remove_doubles": Op("mesh.remove_doubles", "VERT", "merge vertices closer than a distance (Merge by Distance)", {
        "threshold": P("threshold", "length", "the distance, mm or %"),
        "use_centroid": P("use_centroid", "bool", "merge at the middle"),
        "use_unselected": P("use_unselected", "bool", "also onto unselected vertices"),
    }),
    "edge_rotate": Op("mesh.edge_rotate", "EDGE", "turn an edge inside its two faces (flow, poles)", {
        "use_ccw": P("use_ccw", "bool", "counter-clockwise"),
    }),
    "tris_convert_to_quads": Op("mesh.tris_convert_to_quads", "FACE", "join triangles into quads", {
        "face_threshold": P("face_threshold", "angle", "largest angle between the faces, e.g. 40deg"),
        "shape_threshold": P("shape_threshold", "angle", "largest shape error, e.g. 40deg"),
    }),
    "bridge_edge_loops": Op("mesh.bridge_edge_loops", "EDGE", "join two open edge loops with faces (list their "
                            "edges: a loop walker on a border takes the whole border)", {
        "number_cuts": P("number_cuts", "int", "loops across the bridge"),
        "interpolation": P("interpolation", "enum", "linear, path or surface"),
        "smoothness": P("smoothness", "float", "bulge of the new loops"),
        "twist_offset": P("twist_offset", "int", "turn one loop by this many edges"),
        "use_merge": P("use_merge", "bool", "merge the loops instead of bridging"),
        "merge_factor": P("merge_factor", "factor", "where they merge, 0 to 1"),
    }),
    "fill_grid": Op("mesh.fill_grid", "EDGE", "fill a hole with a grid of quads from its border edges, turned "
                    "to run through the loop's extreme vertices on X and Y (it could be cut in quarters and "
                    "mirrored) unless an offset is given", {
        "span": P("span", "int", "rows of the grid"),
        "offset": P("offset", "int", "turn the grid by this many edges"),
        "use_interp_simple": P("use_interp_simple", "bool", "simple interpolation"),
    }, call=lambda kwargs: fill_grid_aligned(**kwargs)),
    "delete": Op("mesh.delete", None, "delete the selection (a hole left for bridge_edge_loops or fill_grid)", {
        "type": P("type", "enum", "face (default: the faces and what only they used), vert, edge, edge_face or "
                                  "only_face (leaves their edges: loose, refused)"),
    }, defaults={"type": "FACE"}),
    "edge_face_add": Op("mesh.edge_face_add", "VERT", "a face from the selected vertices (the F key)"),
    # Phase 4: normals, vertex groups, UV.
    "normals_make_consistent": Op("mesh.normals_make_consistent", None, "turn every face outward (the sync warns "
                                  "when the result is inside out)", {
        "inside": P("inside", "bool", "turn them inward instead"),
    }),
    "flip_normals": Op("mesh.flip_normals", None, "flip the selected faces"),
    "vertex_group_assign": Op("object.vertex_group_assign", "VERT", "put the selected vertices in a vertex group "
                              "(made if missing): for Shrinkwrap, Displace, a later rig", {
        "group": P("group", "text", "the group's name"),
        "weight": P("weight", "factor", "0 to 1 (default 1)"),
    }, build=lambda op, values, sel, obj: dict(values), call=_vertex_group(True)),
    "vertex_group_remove_from": Op("object.vertex_group_remove_from", "VERT", "take the selected vertices out of "
                                   "a vertex group", {
        "group": P("group", "text", "the group's name"),
    }, build=lambda op, values, sel, obj: dict(values), call=_vertex_group(False)),
    "unwrap": Op("uv.unwrap", None, "unwrap the selected faces along their seams (mark_seam first, e.g. "
                 "mesh mark_seam sharp)", {
        "method": P("method", "enum", "angle_based, conformal or minimum_stretch"),
        "margin": P("margin", "float", "space between islands, 0 to 1"),
    }),
    # Phase 4/5: marks, so the AI can clear the modeler's once acted on (or mark for the modeler).
    "mark_seam": Op("mesh.mark_seam", "EDGE", "mark the edges as seams", {
        "clear": P("clear", "bool", "clear the mark instead"),
    }),
    "mark_sharp": Op("mesh.mark_sharp", "EDGE", "mark the edges sharp", {
        "clear": P("clear", "bool", "clear the mark instead"),
    }),
    # Phase 3: growing, cutting and splitting parts.
    "resize": Op("transform.resize", "VERT", "scale the selection along the frame axes around the object's "
                 "origin (the mirror planes' meeting point): a ring pulled out into a brim, a part made wider", {
        "w": P("value", "percent", "scale along w, e.g. 150%"), "d": P("value", "percent", "along d"),
        "h": P("value", "percent", "along h"),
        "around": P("around", "pivot", "origin (default: the mirror planes' meeting point) or selection "
                    "(its own middle: a ring made wider where it is)"),
        **PROPORTIONAL,
    }, build=_resize),
    "rotate": Op("transform.rotate", "VERT", "turn the selection around a frame axis through its own middle: "
                 "a ring tilted to follow a horn's curve (R)", {
        "angle": P("value", "angle", "how far, e.g. 15deg; + turns counterclockwise seen from the axis' + end (axis=w: the top tips to the front, -d)"),
        "axis": P("orient_axis", "letter", "w, d or h (default w)"),
        "around": P("around", "pivot", "selection (default) or origin"),
        **PROPORTIONAL,
    }, build=_rotate),
    "extrude_scale": Op("transform.resize", None, "extrude the selection and scale the new part around the object's "
                        "origin: a loop closing toward the center (E, S, Shift+Z), a flare", {
        "w": P("value", "percent", "scale along w, e.g. 80%"), "d": P("value", "percent", "along d"),
        "h": P("value", "percent", "along h (leave it out to keep the height: Shift+Z)"),
    }, build=_resize, call=_extrude_scale),
    "extrude_region_shrink_fatten": Op("mesh.extrude_region_shrink_fatten", None, "extrude the selected faces "
                                       "out along their normals (a brim, a rim, a thickness)", {
        "value": P("value", "length", "how far, mm or % of the frame's largest axis; + outward"),
        "even": P("use_even_offset", "bool", "keep the thickness even (default on)"),
    }, build=_extrude_fatten),
    "extrude_region_move": Op("mesh.extrude_region_move", None, "extrude the selection as one region and move "
                              "it along the frame axes", {
        "w": P("value", "axis", "move along w: % of the frame's w or mm"),
        "d": P("value", "axis", "along d"), "h": P("value", "axis", "along h"),
    }, build=_extrude_move("extrude_region")),
    "extrude_context_move": Op("mesh.extrude_context_move", None, "extrude what is selected as it is (faces, "
                               "edges or vertices) and move it", {
        "w": P("value", "axis", "move along w"), "d": P("value", "axis", "along d"),
        "h": P("value", "axis", "along h"),
    }, build=_extrude_move("extrude_context")),
    "inset": Op("mesh.inset", "FACE", "inset the selected faces: a ring of new faces inside their border", {
        "thickness": P("thickness", "length", "how far in, mm or %"),
        "depth": P("depth", "length", "raise (+) or sink (-) the inner faces"),
        "use_even_offset": P("use_even_offset", "bool", "even thickness at corners"),
        "use_individual": P("use_individual", "bool", "each face on its own"),
        "use_boundary": P("use_boundary", "bool", "inset open borders too (default on)"),
    }),
    "spin": Op("mesh.spin", None, "sweep the selection around a frame axis through the object's origin", {
        "steps": P("steps", "int", "how many copies along the sweep"),
        "angle": P("angle", "angle", "how far, e.g. 90deg"),
        "axis": P("axis", "letter", "w, d or h (default h)"),
    }, build=_around),
    "screw": Op("mesh.screw", None, "sweep the selection around a frame axis, rising each turn", {
        "steps": P("steps", "int", "steps per turn"),
        "turns": P("turns", "int", "how many turns"),
        "axis": P("axis", "letter", "w, d or h (default h)"),
    }, build=_around),
    "bevel": Op("mesh.bevel", None, "bevel edges (or vertices): the edge becomes a strip of faces", {
        "width": P("offset", "length", "the bevel's width, mm or %"),
        "segments": P("segments", "int", "faces across the bevel"),
        "affect": P("affect", "enum", "edges or vertices"),
        "profile": P("profile", "factor", "0.5 round, higher boxier"),
    }),
    "bisect": Op("mesh.bisect", None, "cut the selection with a plane across a frame axis", {
        "plane": P("plane_co", "plane", "the plane: an axis and a value in permille, e.g. h250"),
        "clear": P("clear", "choice", "above, below or none: the side of the plane to delete"),
        "fill": P("use_fill", "bool", "fill the cut"),
    }, build=_bisect),
    "separate": Op("mesh.separate", None, "move the selection into a new object (by selection, material or "
                   "loose parts)", {
        "type": P("type", "enum", "selected (default), material or loose"),
    }, defaults={"type": "SELECTED"}),
    "extract": Op("mesh.separate", None, "copy the selection into a new object, the original kept: a part that "
                  "sits on another (D-029); then add SHRINKWRAP and set its target", call=_extract),
}


def _merged_rna(*ops):
    """The properties of a macro's operators, for checking its parameters."""
    class Merged:
        properties = {p.identifier: p for op in ops for p in op.get_rna_type().properties}
    return Merged


def help_text():
    """The whitelist as text: one block per operator with its parameters."""
    lines = []
    for name, op in OPS.items():
        lines.append(f"{name} ({op.idname}{', LoopTools' if op.looptools else ''}): {op.doc}")
        for key, p in op.params.items():
            lines.append(f"    {key}: {p.meaning}")
    return "\n".join(lines)


# --- running -------------------------------------------------------------------

def _view3d_context():
    wm = bpy.context.window_manager
    win = bpy.context.window or (wm.windows[0] if wm.windows else None)
    ctx = {"window": win} if win else {}
    if win is not None:
        area = next((a for a in win.screen.areas if a.type == "VIEW_3D"), None)
        if area is not None:
            ctx["area"] = area
            ctx["region"] = next(r for r in area.regions if r.type == "WINDOW")
    return ctx


_TOOL_SETTINGS = ("mesh_select_mode", "use_proportional_edit", "proportional_edit_falloff", "proportional_size",
                  "use_proportional_connected", "use_proportional_projected", "use_mesh_automerge", "use_snap")


@contextmanager
def editing(obj, take_lock=True):
    """Edit Mode on obj alone, under a 3D View override; everything the
    human had (lock, active object, selection, tool settings) comes back."""
    was_locked = LOCK_PROP in obj
    if take_lock and not was_locked:
        lock(obj.name, ui=False)
    else:
        _leave_edit_mode()
    view_layer = bpy.context.view_layer
    active = view_layer.objects.active
    selected = [o for o in view_layer.objects if o.select_get()]
    ts = bpy.context.tool_settings
    saved = {k: tuple(v) if k == "mesh_select_mode" else v for k in _TOOL_SETTINGS for v in [getattr(ts, k)]}
    ctx = _view3d_context()
    # Edit Mode operators skip an object outside the 3D View's Local View (the
    # human's `/`): bring it in for the op.
    space = ctx["area"].spaces.active if "area" in ctx else None
    local = space is not None and space.local_view is not None and not obj.local_view_get(space)
    try:
        if local:
            obj.local_view_set(space, True)
        for o in selected:
            o.select_set(False)
        view_layer.objects.active = obj
        ts.use_mesh_automerge = False
        ts.use_snap = False
        ctx.update(active_object=obj, object=obj)
        with bpy.context.temp_override(**ctx):
            bpy.ops.object.mode_set(mode="EDIT")
        ctx["edit_object"] = obj
        yield ctx
    finally:
        if obj.mode == "EDIT":
            with bpy.context.temp_override(**{k: v for k, v in ctx.items() if k != "edit_object"}):
                bpy.ops.object.mode_set(mode="OBJECT")
        for k, v in saved.items():
            setattr(ts, k, v)
        view_layer.objects.active = active
        for o in selected:
            if o.name in view_layer.objects:
                o.select_set(True)
        if local and obj.name in bpy.data.objects:
            obj.local_view_set(space, False)
        if take_lock and not was_locked:
            unlock(obj.name)


def _ids(mesh):
    return [d.value for d in mesh.attributes[mesh_io.ID_ATTR].data]


def _tag(mesh):
    """A random float per vertex: a vertex the operator made carries an
    interpolated tag that matches none, a kept one its own."""
    ids = _ids(mesh)
    rng = random.Random(len(ids))
    attr = mesh.attributes.new(TAG_ATTR, "FLOAT", "POINT")
    while True:
        attr.data.foreach_set("value", [rng.random() for _ in ids])
        stored = [d.value for d in attr.data]  # read back: the attribute keeps float32
        if len(set(stored)) == len(ids):
            return dict(zip(stored, ids))


def _retag(mesh, by_tag):
    attr = mesh.attributes[TAG_ATTR]
    ids = [by_tag.get(d.value, -1) for d in attr.data]
    mesh.attributes[mesh_io.ID_ATTR].data.foreach_set("value", ids)
    mesh.attributes.remove(mesh.attributes[TAG_ATTR])


def _restore(mesh, backup):
    backup.to_mesh(mesh)
    mesh.update()


def _span(vids):
    vids = sorted(vids)
    if not vids:
        return ""
    if vids == list(range(vids[0], vids[-1] + 1)) and len(vids) > 2:
        return f" (v{vids[0]}..v{vids[-1]})"
    return " (" + " ".join(f"v{v}" for v in vids) + ")"


def _deltas(frame, before, after):
    out = []
    for vid, co in after.items():
        if vid in before:
            a, b = frame.to_values(before[vid]), frame.to_values(co)
            parts = [f"{n}{(y - x) / 10:+.1f}%" for n, x, y in zip("wdh", a, b) if abs(y - x) >= 0.5]
            if parts:
                out.append((max(abs(y - x) for x, y in zip(a, b)), f"v{vid} " + " ".join(parts)))
    out.sort(reverse=True)
    listed = [text for _, text in out[:MAX_DELTAS]]
    return listed + ([f"+{len(out) - MAX_DELTAS} more"] if len(out) > MAX_DELTAS else [])


def _failure(issues):
    words = []
    for i in issues:
        if i["code"] == "non_quad":
            words.append(f"would leave faces that are not quads ({' '.join(i['verts'])})")
        else:
            words.append(f"{i['msg']} ({' '.join(i['verts'])})")
    return "; ".join(words)


def _adopt(obj):
    """A part split off by an op: selectable, no AI lock, no tag; its ids are its own."""
    if LOCK_PROP in obj:
        obj.hide_select = bool(obj[LOCK_PROP])
        del obj[LOCK_PROP]
    if obj.type == "MESH" and TAG_ATTR in obj.data.attributes:
        obj.data.attributes.remove(obj.data.attributes[TAG_ATTR])


def _remove_objects(objects):
    for o in objects:
        data = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)


class Runner:
    """One mesh op, checked and ready to run on an object."""

    def __init__(self, obj, line, op, name, terms, values, frame, counter):
        self.obj, self.line, self.op, self.name, self.terms, self.values = obj, line, op, name, terms, values
        self.frame, self.counter = frame, counter

    def __call__(self, obj=None, measure=True, take_lock=True):
        obj = obj or self.obj
        mesh = obj.data
        if self.op.looptools:
            ensure_looptools()
        ids0 = _ids(mesh)
        co0 = {vid: tuple(v.co) for vid, v in zip(ids0, mesh.vertices)}
        faces0 = len(mesh.polygons)
        mirror = mesh_io.mirror_setup(obj)
        sides = mesh_io.kept_sides(mesh, mirror)
        surface = None
        if measure:
            from . import shape
            dense0, tris = shape.dense(obj)
            surface = shape.Surface(dense0, tris, "before")
        backup = bmesh.new()
        backup.from_mesh(mesh)
        objects0 = set(bpy.data.objects)
        try:
            by_tag = _tag(mesh)
            with editing(obj, take_lock) as ctx:
                try:
                    sel = selection.resolve(obj, self.terms, ctx, self.frame)  # the copy has no sync state
                except SelectionError as e:
                    raise MeshOpError(str(e)) from None
                self._needs(sel)
                kwargs = self.op.kwargs(self.values, sel, obj)
                with bpy.context.temp_override(**ctx):
                    result = self.op.call(kwargs) if self.op.call else self.op.op()(**kwargs)
                if "FINISHED" not in result:
                    raise MeshOpError(f"Blender refused {self.op.idname} ({result})")
            _retag(mesh, by_tag)
            ids, fresh = mesh_io.ensure_ids(mesh, co0, self.counter["next_id"])
            has_subsurf = any(m.type == "SUBSURF" and m.show_viewport for m in obj.modifiers)
            errors = [i for i in validate.check_mesh(obj, ids, mirror, sides, has_subsurf) if i["level"] == "ERROR"]
            if errors:
                raise MeshOpError(_failure(errors))
        except Exception:
            _restore(mesh, backup)
            _remove_objects(set(bpy.data.objects) - objects0)
            raise
        finally:
            backup.free()
        created = [o for o in bpy.data.objects if o not in objects0]
        for o in created:
            _adopt(o)
        self.counter["next_id"] = max([self.counter["next_id"], *[i + 1 for i in ids]])
        co1 = {vid: tuple(v.co) for vid, v in zip(ids, mesh.vertices)}
        added, removed = sorted(set(co1) - set(co0)), sorted(set(co0) - set(co1))
        moved = {vid: co for vid, co in co1.items() if vid in co0 and (Vector(co) - Vector(co0[vid])).length > 1e-7}
        quads = all(len(p.vertices) == 4 for p in mesh.polygons)
        parts = [f"+{len(added)} v{_span(added)}", f"-{len(removed)} v{_span(removed)}",
                 f"faces {faces0} -> {len(mesh.polygons)}" + (", all quads" if quads else "")]
        if moved:
            parts.append(f"moved {len(moved)} v")
        if not (added or removed or moved) and len(mesh.polygons) == faces0:
            parts.append("nothing changed")
        if surface is not None:
            from . import shape
            dense1, _ = shape.dense(obj)
            dev = shape.deviation_of(dense1, surface)
            if dev:
                parts.append(f"surface moved: max {max(abs(dev['min']), abs(dev['max'])):.2f} mm, "
                             f"mean {dev['mean_abs']:.2f} mm")
            # The outline from each view, measured: how a shaping op changed the form.
            profiles = shape.profile_change(dense0, dense1)
            if profiles:
                parts.append("profile " + ", ".join(profiles))
        if created:
            parts.append("new object " + ", ".join(o.name for o in created) + " (sync it for its own text)")
        note = ", ".join(parts)
        if moved and self.frame is not None:
            note += "; " + " ".join(_deltas(self.frame, co0, moved))
        return note

    def _needs(self, sel):
        need = self.op.needs
        if need == "EDGE" and not sel["edges"]:
            raise MeshOpError(f"{self.name} needs edges in the selection")
        if need == "FACE" and not sel["faces"]:
            raise MeshOpError(f"{self.name} needs faces in the selection")
        if need == "SEED" and sel["seed"] is None:
            raise MeshOpError(f"{self.name} needs an edge to cut across: vA-vB or ring vA-vB")


def _split(tokens):
    params, rest = {}, []
    for t in tokens:
        m = re.fullmatch(r"([A-Za-z_]+)=(.*)", t)  # a region like h>=900 is a selection, not a parameter
        if m:
            params[m[1].lower()] = m[2]
        else:
            rest.append(t)
    return rest, params


def _terms(tokens, cage, mesh):
    try:
        terms = selection.parse(tokens, cage)
        selection.check(mesh, terms)
    except SelectionError as e:
        raise MeshOpError(str(e)) from None
    return terms


def check_line(obj, verb, args, line, cage, frame, counter):
    """A Runner for a mesh, dissolve or cut line, or MeshOpError."""
    if verb == "dissolve":
        if not args:
            raise MeshOpError("expected 'dissolve <edges>'")
        terms = _terms(args, cage, obj.data)
        return Runner(obj, line, OPS["dissolve_edges"], "dissolve", terms, {}, frame, counter)
    if verb == "cut":
        m = re.fullmatch(r"v(\d+)-v(\d+)", args[0].lower()) if args else None
        if not m or len(args) > 2 or (len(args) == 2 and not args[1].isdigit()):
            raise MeshOpError("expected 'cut <vA-vB> [N]'")
        terms = _terms(args[:1], cage, obj.data)
        values = {"number_cuts": int(args[1]) if len(args) == 2 else 1}
        return Runner(obj, line, OPS["loopcut_slide"], "cut", terms, values, frame, counter)
    if not args:
        raise MeshOpError(f"expected 'mesh <operator> <selection> [key=value ...]'; operators: {', '.join(OPS)}")
    name = args[0].lower()
    op = OPS.get(name)
    if op is None:
        raise MeshOpError(f"unknown operator {args[0]!r}; the list: {', '.join(OPS)} (help: fofuxo_cage.mesh_help())")
    tokens, raw = _split(args[1:])
    if not tokens:
        raise MeshOpError(f"{name} needs a selection")
    terms = _terms(tokens, cage, obj.data)
    rna = op.rna()
    values = {}
    for key, text in raw.items():
        p = op.params.get(key)
        if p is None:
            raise MeshOpError(f"{name} has no parameter {key!r}; it takes {', '.join(op.params) or 'none'}")
        values[key] = _value(p, text, key, rna, frame)
    return Runner(obj, line, op, name, terms, values, frame, counter)


EDGE_WEIGHTS = {"crease": "crease_edge", "bevel_weight": "bevel_weight_edge"}


def crease(obj, terms, value, kind="crease"):
    """Set the crease (or bevel weight) of the selected edges; returns how many."""
    with editing(obj) as ctx:
        try:
            sel = selection.resolve(obj, terms, ctx)
        except SelectionError as e:
            raise MeshOpError(str(e)) from None
        bm = bmesh.from_edit_mesh(obj.data)
        name = EDGE_WEIGHTS[kind]
        layer = bm.edges.layers.float.get(name) or bm.edges.layers.float.new(name)
        bm.edges.ensure_lookup_table()
        for i in sel["edges"]:
            bm.edges[i][layer] = value
        bmesh.update_edit_mesh(obj.data)
    return len(sel["edges"])


def precheck(obj, runners):
    """Run the batch's mesh ops on a temporary copy; the first failure is raised."""
    objects0 = set(bpy.data.objects)
    copy = obj.copy()
    copy.data = obj.data.copy()
    if LOCK_PROP in copy:
        del copy[LOCK_PROP]
    for coll in obj.users_collection:
        coll.objects.link(copy)
    counter = None
    try:
        for runner in runners:
            counter = dict(runner.counter) if counter is None else counter
            saved, runner.counter = runner.counter, counter
            try:
                runner(copy, measure=False, take_lock=False)
            except (MeshOpError, RuntimeError) as e:
                raise MeshOpError(f"{runner.line!r}: {e}") from None
            finally:
                runner.counter = saved
    finally:
        _remove_objects(set(bpy.data.objects) - objects0)  # the copy and any part split off it


def select(name, text, cage=None):
    """Preview a selection: the ids it names, without changing the mesh."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise MeshOpError(f"no mesh object named {name!r}")
    if cage is None:
        from . import cage_format
        from .sync import paths
        path = paths(obj)["text"]
        cage = cage_format.parse(path.read_text("utf-8")) if path.exists() else None
    terms = _terms(text.split(), cage, obj.data)
    with editing(obj) as ctx:
        try:
            selection.resolve(obj, terms, ctx)
        except SelectionError as e:
            raise MeshOpError(str(e)) from None
        verts, edges, faces = selection.selected_ids(obj)
    out = {"verts": [f"v{v}" for v in verts], "edges": [f"v{a}-v{b}" for a, b in edges]}
    if faces:
        out["faces"] = [" ".join(f"v{v}" for v in f) for f in faces]
    return out
