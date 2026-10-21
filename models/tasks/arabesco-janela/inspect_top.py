"""Close-up of the top of the vine: solid colors and an x-ray wire pass, plus
boundary edges of the three objects. Does not save the .blend."""
import bpy
import math
import os
from mathutils import Vector

OUT = r"C:\Users\ant7a\OneDrive\Documentos\GitHub\FofuxoModelingRules\models\tasks\arabesco-janela\renders"
NAMES = ["Plane.001", "Plane.019", "Plane.020"]
COLORS = [(0.85, 0.25, 0.25, 1), (0.25, 0.55, 0.9, 1), (0.95, 0.75, 0.2, 1)]

scene = bpy.context.scene
for name, color in zip(NAMES, COLORS):
    bpy.data.objects[name].color = color

pts = []
for name in NAMES:
    o = bpy.data.objects[name]
    pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
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
cam.rotation_euler = (math.radians(90), 0, 0)

scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.display.shading.light = "FLAT"
scene.display.shading.color_type = "OBJECT"
scene.display.shading.show_cavity = False

keep = set(NAMES)
for o in bpy.data.objects:
    if o.type in {"CAMERA", "LIGHT", "EMPTY"}:
        continue
    o.hide_render = o.name not in keep


def shot(name, xray):
    scene.display.shading.show_xray = xray
    scene.display.shading.xray_alpha = 0.35 if xray else 1.0
    path = os.path.join(OUT, name)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("WROTE", path)


shot("top_cluster_solid.png", False)
shot("top_cluster_xray.png", True)

for name in NAMES:
    o = bpy.data.objects[name]
    me = o.data
    counts = {}
    for p in me.polygons:
        for e in p.edge_keys:
            counts[e] = counts.get(e, 0) + 1
    border = [e for e, c in counts.items() if c == 1]
    print("BORDER", name, "edges", len(me.edges), "border", len(border), "verts", len(me.vertices))
    world = [tuple(round(v, 4) for v in (o.matrix_world @ me.vertices[i].co)) for e in border for i in e]
    print("BORDER_WORLD", name, world[:40])
