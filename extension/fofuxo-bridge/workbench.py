"""Single-view Workbench renders in a disposable scene, optionally cropped to a region."""

from pathlib import Path
import math

import bpy
from mathutils import Vector

from .rounds import count, record_image

VIEWS = {"3q": (-0.62, -0.62, 0.38), "front": (0, -1, 0),
         "high": (-0.75, -0.35, 0.65), "top": (0, 0, 1), "side": (1, 0, 0)}


def _render_scene(scene):
    return bpy.ops.render.render(write_still=True, scene=scene.name)


def workbench(name, out=None, view="3q", cage=False, focus=None, size=768, margin=1.25):
    from .sync import paths
    from .mesh_io import ensure_ids
    from .regions import region_ids
    from .instance import assert_ai_access
    assert_ai_access()
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH" or obj.mode != "OBJECT":
        raise ValueError("workbench requires a mesh in Object Mode")
    if view not in VIEWS or type(size) is not int or not 64 <= size <= 4096 or not math.isfinite(margin) or margin < 1:
        raise ValueError("use a known view, size 64..4096 and margin >= 1")
    ids = ensure_ids(obj.data)[0]
    if isinstance(focus, str):
        focus = region_ids(name, focus)
    wanted = {int(str(vid).removeprefix("v")) for vid in focus} if focus is not None else None
    if wanted is not None:
        if not wanted or not wanted <= set(ids):
            raise ValueError("focus must contain existing stable vertex ids")
        points = [obj.matrix_world @ vertex.co for vertex, vid in zip(obj.data.vertices, ids) if vid in wanted]
    else:
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        finally:
            evaluated.to_mesh_clear()
    if not points:
        raise ValueError("the mesh is empty")
    root = Path(out) if out else paths(obj)["render"].parent
    root.mkdir(parents=True, exist_ok=True)
    filename = paths(obj)["render"].stem if out is None else "model"
    path = root / f"{filename}.{'cage' if cage else 'workbench'}.{view}.png"
    scene = bpy.data.scenes.new("LLM temporary render")
    objects, meshes, cameras = [], [], []
    images_before = set(bpy.data.images)
    try:
        def copy_mesh(source):
            duplicate = source.copy()
            objects.append(duplicate)
            duplicate.data = source.data.copy()
            meshes.append(duplicate.data)
            duplicate.parent = None
            duplicate.matrix_world = source.matrix_world
            scene.collection.objects.link(duplicate)
            duplicate.hide_render = False
            duplicate.hide_viewport = False
            return duplicate

        model = copy_mesh(obj)
        for polygon in model.data.polygons:
            polygon.use_smooth = True
        model.color = (0.86, 0.80, 0.64, 1)
        if cage:
            wire = copy_mesh(obj)
            for modifier in list(wire.modifiers):
                if modifier.type != "MIRROR":
                    wire.modifiers.remove(modifier)
            bounds = [max(point[axis] for point in points) - min(point[axis] for point in points) for axis in range(3)]
            thickness = max(max(bounds) / 350, 0.00001)
            modifier = wire.modifiers.new("Cage wire", "WIREFRAME")
            modifier.thickness = thickness
            modifier.use_replace = True
            wire.color = (0.08, 0.12, 0.30, 1)
        center = Vector([(min(point[axis] for point in points) + max(point[axis] for point in points)) / 2 for axis in range(3)])
        direction = Vector(VIEWS[view]).normalized()
        rotation = (-direction).to_track_quat("-Z", "Y")
        inverse = rotation.inverted()
        projected = [inverse @ (point - center) for point in points]
        spans = [max(point[axis] for point in projected) - min(point[axis] for point in projected) for axis in (0, 1)]
        camera_data = bpy.data.cameras.new("LLM temporary camera")
        cameras.append(camera_data)
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = max(max(spans) * margin, 0.001)
        radius = max((point - center).length for point in points)
        camera_data.clip_start = 0.00001
        camera_data.clip_end = max(radius * 20, 10)
        camera = bpy.data.objects.new("LLM temporary camera", camera_data)
        objects.append(camera)
        scene.collection.objects.link(camera)
        camera.location = center + direction * max(radius * 4, 0.1)
        camera.rotation_euler = rotation.to_euler()
        scene.camera = camera
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = scene.render.resolution_y = size
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(path)
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "OBJECT"
        scene.display.shading.show_cavity = True
        scene.display.shading.background_type = "WORLD"
        scene.display.shading.background_color = (0.16, 0.16, 0.16)
        _render_scene(scene)
        count("renders")
        record_image(size, size, "workbench")
        return {"render": str(path), "view": view, "pixels": size * size, "focus_vertices": len(wanted) if wanted else None}
    finally:
        for duplicate in reversed(objects):
            bpy.data.objects.remove(duplicate, do_unlink=True)
        for mesh in meshes:
            bpy.data.meshes.remove(mesh)
        for camera_data in cameras:
            bpy.data.cameras.remove(camera_data)
        bpy.data.scenes.remove(scene)
        for image in set(bpy.data.images) - images_before:
            if image.type == "RENDER_RESULT":
                bpy.data.images.remove(image)
