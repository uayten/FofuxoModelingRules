"""Workbench renders used in run C1, kept as a reference for ROADMAP item 8
(make them one call of the extension). Run inside the LLM's Blender through
the MCP (execute_blender_code), with the hat's file open:

    exec(open(r"<repo>/models/tasks/chapeu-cowboy/ai/C1/workbench_render.py").read())
    render("Chapéu", "<out folder>")               # shaded only
    render("Chapéu", "<out folder>", cage=True)    # the cage's edges and vertices over it

Everything it adds (camera, cage copies, node group) is removed after, and
the settings it changes are put back: nothing stays in the file.
"""

import os

import bpy
from mathutils import Vector

VIEWS = {  # name: direction from the target to the camera
    "3q": (-0.62, -0.62, 0.38),
    "front": (0, -1, 0.08),
    "high": (-0.75, -0.35, 0.65),
    "top": (0, -0.05, 1),
}


def _mirrored_copy(obj, name):
    """A copy of obj's base mesh with only its Mirror modifiers: the whole cage."""
    scn = bpy.context.scene
    copy = bpy.data.objects.new(name, obj.data.copy())
    scn.collection.objects.link(copy)
    copy.matrix_world = obj.matrix_world
    for m in obj.modifiers:
        if m.type == "MIRROR":
            n = copy.modifiers.new(m.name, "MIRROR")
            n.use_axis = m.use_axis
            n.use_clip, n.use_mirror_merge, n.merge_threshold = True, True, 0.0001
    return copy


def _points_group():
    """Geometry Nodes: a small sphere on every vertex."""
    ng = bpy.data.node_groups.new("tmp_points", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n, link = ng.nodes, ng.links.new
    gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    to_points = n.new("GeometryNodeMeshToPoints")
    sphere = n.new("GeometryNodeMeshUVSphere")
    sphere.inputs["Radius"].default_value = 0.0028
    sphere.inputs["Segments"].default_value = 12
    sphere.inputs["Rings"].default_value = 6
    inst, real = n.new("GeometryNodeInstanceOnPoints"), n.new("GeometryNodeRealizeInstances")
    link(gi.outputs[0], to_points.inputs["Mesh"])
    link(to_points.outputs["Points"], inst.inputs["Points"])
    link(sphere.outputs["Mesh"], inst.inputs["Instance"])
    link(inst.outputs["Instances"], real.inputs["Geometry"])
    link(real.outputs["Geometry"], go.inputs[0])
    return ng


def render(name, out, cage=False, size=1200, distance=1.15, lens=70, views=VIEWS):
    scn = bpy.context.scene
    obj = bpy.data.objects[name]
    sub = obj.modifiers.get("Subdivision")
    sub_was = (sub.show_viewport, sub.show_render) if sub else None
    if sub:
        sub.show_viewport = sub.show_render = True
    smooth = [p.use_smooth for p in obj.data.polygons]
    for p in obj.data.polygons:
        p.use_smooth = True
    extra, ng = [], None
    color_was = tuple(obj.color)
    if cage:
        wire = _mirrored_copy(obj, "tmp_cage")
        wf = wire.modifiers.new("Wireframe", "WIREFRAME")
        wf.thickness, wf.use_replace, wf.use_even_offset = 0.0012, True, True
        wire.color = (0.08, 0.12, 0.30, 1)
        pts = _mirrored_copy(obj, "tmp_pts")
        ng = _points_group()
        pts.modifiers.new("Points", "NODES").node_group = ng
        pts.color = (0.95, 0.45, 0.05, 1)
        obj.color = (0.86, 0.80, 0.64, 1)
        extra += [wire, pts]
    cam_data = bpy.data.cameras.new("tmp_cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("tmp_cam", cam_data)
    scn.collection.objects.link(cam)
    sh = scn.display.shading
    was = (scn.camera, scn.render.engine, scn.render.resolution_x, scn.render.resolution_y, scn.render.filepath,
           sh.light, sh.color_type, tuple(sh.single_color), sh.show_cavity)
    hidden = [(o, o.hide_render) for o in bpy.data.objects if o.type == "EMPTY"]
    for o, _ in hidden:  # the concept image stays out of the render
        o.hide_render = True
    scn.camera, scn.render.engine = cam, "BLENDER_WORKBENCH"
    scn.render.resolution_x = scn.render.resolution_y = size
    sh.light, sh.show_cavity = "STUDIO", True
    if cage:
        sh.color_type = "OBJECT"
    else:
        sh.color_type, sh.single_color = "SINGLE", (0.85, 0.78, 0.6)
    os.makedirs(out, exist_ok=True)
    paths = []
    try:
        for view, d in views.items():
            v = Vector(d).normalized()
            cam.location = v * distance
            cam.rotation_euler = (-v).to_track_quat("-Z", "Y").to_euler()
            scn.render.filepath = os.path.join(out, f"{'wire' if cage else 'workbench'}-{view}.png")
            bpy.ops.render.render(write_still=True)
            paths.append(scn.render.filepath)
    finally:
        (scn.camera, scn.render.engine, scn.render.resolution_x, scn.render.resolution_y, scn.render.filepath,
         sh.light, sh.color_type, sh.single_color, sh.show_cavity) = was
        for o, h in hidden:
            o.hide_render = h
        obj.color = color_was
        for p, s in zip(obj.data.polygons, smooth):
            p.use_smooth = s
        if sub:
            sub.show_viewport, sub.show_render = sub_was
        for o in [cam] + extra:
            data = o.data
            bpy.data.objects.remove(o)
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)
        if ng:
            bpy.data.node_groups.remove(ng)
    return paths
