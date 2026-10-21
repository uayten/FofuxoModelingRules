"""Close-up of the junction with the cage drawn as wire, to show the weld.

Creates a temporary duplicate with a Wireframe modifier, renders front and 3/4,
then removes it. Does not save the .blend.
"""
import bpy
import math
from mathutils import Vector

OUT = r"C:\Users\ant7a\OneDrive\Documentos\GitHub\FofuxoModelingRules\models\tasks\arabesco-janela\renders"
BOX_MIN = Vector((0.02, -0.09, 2.08))
BOX_MAX = Vector((0.12, -0.04, 2.19))

scene = bpy.context.scene
obj = bpy.data.objects["Plane.001"]

pts = []
for v in obj.data.vertices:
    p = obj.matrix_world @ v.co
    if all(BOX_MIN[i] <= p[i] <= BOX_MAX[i] for i in range(3)):
        pts.append(p)
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo + hi) / 2
size = hi - lo
print("REGION", tuple(round(v, 4) for v in lo), tuple(round(v, 4) for v in hi))

wire = obj.copy()
wire.data = obj.data.copy()
wire.name = "WireTest"
scene.collection.objects.link(wire)
for m in list(wire.modifiers):
    wire.modifiers.remove(m)
mod = wire.modifiers.new("Wire", "WIREFRAME")
mod.thickness = 0.00035
mod.use_replace = True
mod.use_even_offset = True

cam = bpy.data.objects.new("CloseCam", bpy.data.cameras.new("CloseCam"))
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1000
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "OBJECT"
scene.display.shading.show_cavity = True
obj.color = (0.85, 0.82, 0.76, 1)
wire.color = (0.05, 0.35, 0.75, 1)

for o in bpy.data.objects:
    if o.type in {"CAMERA", "LIGHT", "EMPTY"}:
        continue
    o.hide_render = o.name not in {"Plane.001", "WireTest"}


def shot(name, yaw_deg, pitch_deg, scale_mul=1.25):
    dist = 1.0
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = scale_mul * max(size.x, size.z)
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cam.location = (center.x + dist * math.sin(yaw) * math.cos(pitch),
                    center.y - dist * math.cos(yaw) * math.cos(pitch),
                    center.z + dist * math.sin(pitch))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = f"{OUT}/{name}.png"
    bpy.ops.render.render(write_still=True)
    print("WROTE", scene.render.filepath)


shot("weld_front", 0, 0)
shot("weld_3q", 35, 18)

bpy.data.objects.remove(wire, do_unlink=True)
bpy.data.objects.remove(cam, do_unlink=True)
print("CLEANED")
