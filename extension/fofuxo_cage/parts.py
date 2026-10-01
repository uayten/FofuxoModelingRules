"""Start a new part from one of Blender's primitives, ready to edit as text.

    start_part("Hat", "cylinder", size=(60, 60, 40), vertices=16)

The primitive is added with Blender's operator and sized in mm (full width,
depth, height). A cylinder stays whole (D-061: edited with extrudes and loops
cut around it, not cut and mirrored), each cap a ring of quads (the rim
extruded and scaled in X and Y toward the axis) around a grid of quads
(`fill_grid`), no fan of triangles. Other primitives are cut on the mirror planes with
bisect so only the modeled side stays (D-034; kept sides X-, Y-, Z+ by
default: the front view sees -Y, D-055) and get Mirror (merge 0.1 mm,
clipping, D-054). Then Subdivision, the frame set to the size, and a sync.
From there it is edited with the ops of the text (`mesh ...`).
"""

import bpy
from mathutils import Vector

from .mesh_ops import editing, fill_grid_aligned, _view3d_context

PRIMITIVES = {
    # name: (operator, its settings; the shape spans -1..1 before sizing)
    "cylinder": ("primitive_cylinder_add", {"vertices": 16, "radius": 1.0, "depth": 2.0, "end_fill_type": "NOTHING"}),
    "sphere": ("primitive_uv_sphere_add", {"segments": 16, "ring_count": 8, "radius": 1.0}),
    "cube": ("primitive_cube_add", {"size": 2.0}),
    "plane": ("primitive_plane_add", {"size": 2.0}),
}
KEPT = {"X": "-", "Y": "-", "Z": "+"}
MERGE = 0.0001  # m: 0.1 mm (D-054)


class PartError(RuntimeError):
    pass


CAP_RING = 0.8  # the cap's ring of quads closes to 80% of the rim


def _cap_with_grids(obj, n, ring=CAP_RING):
    """Close both ends of an open cylinder the modeler's way: extrude the rim,
    scale it in X and Y toward the axis (E, S, Shift+Z), then Grid Fill the new
    inner loop, turned to line up with the X and Y extremes (it could be cut in
    quarters and mirrored). The cap gets a ring of quads, then a grid of quads."""
    import bmesh

    if n % 4:
        raise PartError(f"a cylinder needs a vertex count divisible by 4 for quad caps, not {n}")
    with editing(obj, take_lock=False) as ectx:
        for top in (True, False):
            bm = bmesh.from_edit_mesh(obj.data)
            border = [e for e in bm.edges if e.is_boundary]
            z = [sum(v.co.z for v in e.verts) / 2 for e in border]
            edge_z = max(z) if top else min(z)
            for el in (*bm.verts, *bm.edges, *bm.faces):
                el.select_set(False)
            for e, ez in zip(border, z):
                if abs(ez - edge_z) < 1e-6:
                    e.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            with bpy.context.temp_override(**ectx):
                bpy.context.tool_settings.mesh_select_mode = (False, True, False)
                bpy.ops.mesh.extrude_region(mirror=False)
                bpy.ops.transform.resize(value=(ring, ring, 1.0), orient_type="LOCAL",
                                         center_override=tuple(obj.matrix_world.translation))
                fill_grid_aligned(span=n // 4)  # the extruded loop is still selected


WHOLE = ("cylinder",)  # D-061: modeled whole, never cut and mirrored by default


ON_PROP = "fofuxo_on"  # the body a part sits on, drawn around it in every sheet


def start_part(name, primitive, size, mirror=None, subdivision=1, parent=None, at=(0.0, 0.0, 0.0),
               sides=None, on=None, **settings):
    """A new part `name` from `primitive` (cylinder, sphere, cube, plane),
    `size` (w, d, h) in mm, mirrored on the axes in `mirror` ("" for none;
    default: whole for a cylinder, "XY" otherwise),
    at `at` (mm, in the parent's space when a parent is given). `on`: the
    body the part sits on (D-063): the part goes in its collection and every
    sheet draws it around the part, with no parenting. `settings` go to the
    primitive's operator (vertices=12, segments=24, ...).
    Returns the first sync's report."""
    from .sync import set_frame, sync

    if primitive not in PRIMITIVES:
        raise PartError(f"primitive must be one of {', '.join(PRIMITIVES)}, not {primitive!r}")
    if name in bpy.data.objects:
        raise PartError(f"there is an object named {name!r} already")
    if not bpy.data.filepath:
        raise PartError("save the .blend first: the part's text lives next to it")
    parent_obj = bpy.data.objects.get(parent) if parent else None
    if parent and parent_obj is None:
        raise PartError(f"no object named {parent!r} to parent to")
    on_obj = bpy.data.objects.get(on) if on else None
    if on and on_obj is None:
        raise PartError(f"no object named {on!r} for the part to sit on")
    op_name, base = PRIMITIVES[primitive]
    kwargs = {**base, **settings}
    if mirror is None:
        mirror = "" if primitive in WHOLE else "XY"
    mirror = mirror.upper()
    kept = {**KEPT, **(sides or {})}

    ctx = _view3d_context()
    with bpy.context.temp_override(**ctx):
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        before = set(bpy.data.objects)
        getattr(bpy.ops.mesh, op_name)(**kwargs, enter_editmode=False, location=(0.0, 0.0, 0.0))
    new = [o for o in bpy.data.objects if o not in before]
    if len(new) != 1:
        raise PartError(f"{op_name} made {len(new)} objects")
    obj = new[0]
    obj.name = name
    obj.data.name = name
    half = [s / 2000.0 for s in size]
    for v in obj.data.vertices:  # size the primitive (it spans -1..1)
        v.co = [c * h for c, h in zip(v.co, half)]
    obj.data.update()
    home = parent_obj or on_obj  # the part goes in the collection of what it belongs to
    if home is not None:
        for coll in list(obj.users_collection):
            coll.objects.unlink(obj)
        for coll in home.users_collection:
            coll.objects.link(obj)
    if parent_obj is not None:
        obj.parent = parent_obj
    if on_obj is not None:
        obj[ON_PROP] = on_obj.name
    obj.location = [a / 1000.0 for a in at]

    if primitive == "cylinder":
        _cap_with_grids(obj, kwargs["vertices"])

    if mirror:
        with editing(obj, take_lock=False) as ectx:
            with bpy.context.temp_override(**ectx):
                bpy.ops.mesh.select_all(action="SELECT")
                for axis in mirror:
                    k = "XYZ".index(axis)
                    normal = [0.0, 0.0, 0.0]
                    normal[k] = 1.0 if kept[axis] == "-" else -1.0  # the side the normal points to goes
                    world_no = (obj.matrix_world.to_3x3() @ Vector(normal)).normalized()
                    bpy.ops.mesh.select_all(action="SELECT")
                    bpy.ops.mesh.bisect(plane_co=tuple(obj.matrix_world.translation), plane_no=tuple(world_no),
                                        clear_outer=True)
                bpy.ops.mesh.select_all(action="SELECT")
                # a cap's fan of triangles pairs into quads only with the limits open
                bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.1416, shape_threshold=3.1416)
        for v in obj.data.vertices:  # the cut lands on the plane within float error: put it on it
            v.co = [0.0 if a in mirror and abs(c) < 1e-5 else c for a, c in zip("XYZ", v.co)]
        obj.data.update()
        mod = obj.modifiers.new("Mirror", "MIRROR")
        mod.use_axis = [a in mirror for a in "XYZ"]
        mod.use_clip = True
        mod.use_mirror_merge = True
        mod.merge_threshold = MERGE
    if subdivision:
        sub = obj.modifiers.new("Subdivision", "SUBSURF")
        sub.levels = subdivision
        sub.render_levels = max(2, subdivision)
    non_quads = [p.index for p in obj.data.polygons if len(p.vertices) != 4]
    report = sync(name, render=False)
    if report["action"] in ("init", "pulled"):
        report = set_frame(name, w=size[0], d=size[1], h=size[2])
    if non_quads:
        report.setdefault("issues", []).append({"level": "WARN", "code": "start_non_quads",
                                                "msg": f"{len(non_quads)} faces are not quads after the cut: "
                                                       "try another vertex count", "verts": []})
    return report
