"""Join Plane.020 into Plane.001 (no modifier applied) and report the result.

The join keeps Plane.001's stack; Plane.020's modifiers stop existing, which is
expected: the two pieces sit on the same surface and the merged object keeps
the larger piece's Subdivision and Smooth by Angle.
"""
import bpy
import os
from mathutils import Vector

OUT = r"C:\Users\ant7a\OneDrive\Documentos\GitHub\FofuxoModelingRules\models\tasks\arabesco-janela\renders"
TARGET = "Plane.001"
SOURCE = "Plane.020"

scene = bpy.context.scene
target = bpy.data.objects[TARGET]
source = bpy.data.objects[SOURCE]

before = {
    "target_verts": len(target.data.vertices),
    "target_faces": len(target.data.polygons),
    "source_verts": len(source.data.vertices),
    "source_faces": len(source.data.polygons),
    "objects": len(bpy.data.objects),
}

# World-space copy of the source geometry so the transform is preserved by the join.
source.matrix_world = source.matrix_world.copy()
bpy.ops.object.select_all(action="DESELECT")
target.select_set(True)
source.select_set(True)
bpy.context.view_layer.objects.active = target
bpy.ops.object.join()

joined = bpy.context.view_layer.objects.active
result = {
    "before": before,
    "after": {"verts": len(joined.data.vertices), "faces": len(joined.data.polygons),
              "objects": len(bpy.data.objects),
              "materials": [s.material.name if s.material else None for s in joined.material_slots],
              "mods": [m.type for m in joined.modifiers]},
}

# How many vertices of the merged piece sit within 0.5 mm of another piece's?
import mathutils
kd = mathutils.kdtree.KDTree(len(joined.data.vertices))
for i, v in enumerate(joined.data.vertices):
    kd.insert(v.co, i)
kd.balance()
close = 0
for i, v in enumerate(joined.data.vertices):
    hits = [j for (co, j, dist) in kd.find_range(v.co, 0.0005) if j != i]
    if hits:
        close += 1
result["verts_within_0_5mm"] = close

bpy.ops.wm.save_mainfile()

# Render the merged object, same framing as the previous close-up.
pts = [joined.matrix_world @ Vector(c) for c in joined.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo + hi) / 2
size = hi - lo

cam = bpy.data.objects.get("TopCam")
if cam is None:
    cam = bpy.data.objects.new("TopCam", bpy.data.cameras.new("TopCam"))
    scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1.3 * max(size.x, size.z)
cam.location = (center.x, lo.y - 2.0, center.z)
cam.rotation_euler = (0.0, 0.0, 0.0)
cam.rotation_euler = (1.5708, 0.0, 0.0)

scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.display.shading.light = "FLAT"
scene.display.shading.color_type = "OBJECT"
joined.color = (0.85, 0.25, 0.25, 1)
bpy.data.objects["Plane.019"].color = (0.25, 0.55, 0.9, 1)

for o in bpy.data.objects:
    if o.type in {"CAMERA", "LIGHT", "EMPTY"}:
        continue
    o.hide_render = o.name not in {TARGET, "Plane.019"}

scene.render.filepath = os.path.join(OUT, "merge_step1.png")
bpy.ops.render.render(write_still=True)
result["render"] = scene.render.filepath
