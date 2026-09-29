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
        items = [i.identifier for i in rna.properties[param.prop].enum_items] if rna is not None else []
        if raw.upper() not in items:
            raise MeshOpError(f"{key} takes one of {[i.lower() for i in items]}, not {raw!r}")
        return raw.upper()
    if unit == "length":
        return _length(raw, key, frame)
    if unit == "axis":
        k = "wdh".index(key)
        sign = -1.0 if frame is not None and frame.axes[k].side == "-" else 1.0  # + moves away from the plane
        return sign * _length(raw, key, frame, k)
    raise MeshOpError(f"{key}: unknown unit {unit}")


# --- the whitelist -------------------------------------------------------------

def _falloff_rna():
    return bpy.ops.transform.translate.get_rna_type()


class Op:
    """A whitelisted operator. needs: the element kind the selection must
    hold (VERT, EDGE, FACE, SEED for one edge, or None)."""

    def __init__(self, idname, needs, doc, params=None, defaults=None, build=None, rna=None, looptools=False):
        self.idname, self.needs, self.doc = idname, needs, doc
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
            return self.build(values, sel, obj)
        out = dict(self.defaults)
        out.update({self.params[k].prop: v for k, v in values.items()})
        return out


def _loopcut(values, sel, obj):
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


def _translate(values, sel, obj):
    local = Vector([values.get(a, 0.0) for a in "wdh"])
    return {"value": tuple(obj.matrix_world.to_3x3() @ local), "orient_type": "GLOBAL",
            "mirror": False, "snap": False, **_proportional(values, obj)}


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
}


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
    try:
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
            co, tris = shape.dense(obj)
            surface = shape.Surface(co, tris, "before")
        backup = bmesh.new()
        backup.from_mesh(mesh)
        try:
            by_tag = _tag(mesh)
            with editing(obj, take_lock) as ctx:
                try:
                    sel = selection.resolve(obj, self.terms, ctx)
                except SelectionError as e:
                    raise MeshOpError(str(e)) from None
                self._needs(sel)
                kwargs = self.op.kwargs(self.values, sel, obj)
                with bpy.context.temp_override(**ctx):
                    result = self.op.op()(**kwargs)
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
            raise
        finally:
            backup.free()
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
            dev = shape.deviation(obj.name, surface)
            if dev:
                parts.append(f"surface moved: max {max(abs(dev['min']), abs(dev['max'])):.2f} mm, "
                             f"mean {dev['mean_abs']:.2f} mm")
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
        if "=" in t:
            k, _, v = t.partition("=")
            params[k.lower()] = v
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


def crease(obj, terms, value):
    """Set the crease weight of the selected edges; returns how many."""
    with editing(obj) as ctx:
        try:
            sel = selection.resolve(obj, terms, ctx)
        except SelectionError as e:
            raise MeshOpError(str(e)) from None
        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
        bm.edges.ensure_lookup_table()
        for i in sel["edges"]:
            bm.edges[i][layer] = value
        bmesh.update_edit_mesh(obj.data)
    return len(sel["edges"])


def precheck(obj, runners):
    """Run the batch's mesh ops on a temporary copy; the first failure is raised."""
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
        mesh = copy.data
        bpy.data.objects.remove(copy)
        bpy.data.meshes.remove(mesh)


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
