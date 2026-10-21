"""Inspect the arch vine and render it close up. Does not save the .blend."""
import bpy
import math
import os
from mathutils import Vector

OUT = os.environ.get("FOFUXO_OUT", r"C:\Users\ant7a\OneDrive\Documentos\GitHub\FofuxoModelingRules\models\tasks\arabesco-janela\renders")
VINE = ["Plane.%03d" % i for i in list(range(17, 28)) + list(range(29, 38))]

rows = []
for name in VINE:
    obj = bpy.data.objects[name]
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = [round(min(p[i] for p in bb), 3) for i in range(3)]
    hi = [round(max(p[i] for p in bb), 3) for i in range(3)]
    rows.append({
        "name": name,
        "verts": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "mods": [m.type + (":%d" % m.levels if m.type == "SUBSURF" else "") for m in obj.modifiers],
        "mats": [s.material.name if s.material else None for s in obj.material_slots],
        "z": (lo[2], hi[2]),
        "x": (lo[0], hi[0]),
        "y": (lo[1], hi[1]),
    })

rows.sort(key=lambda r: -r["z"][1])
for r in rows:
    print("VINE", r["name"], r["verts"], "v", r["faces"], "f", "z", r["z"], "x", r["x"], "y", r["y"],
          r["mods"], r["mats"])

# Camera: close up of the vine only, front orthographic.
objs = [bpy.data.objects[n] for n in VINE]
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo + hi) / 2
size = hi - lo

scene = bpy.context.scene
cam_data = bpy.data.cameras.new("VineCam")
cam = bpy.data.objects.new("VineCam", cam_data)
scene.collection.objects.link(cam)
old_cam = scene.camera
scene.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1.15 * max(size.x, size.z)
cam.location = (center.x, lo.y - 3.0, center.z)
cam.rotation_euler = (math.radians(90), 0, 0)

scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 900
scene.render.resolution_y = 1400
scene.render.film_transparent = False
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "RANDOM"
scene.display.shading.show_shadows = True

keep = set(VINE)
hidden = {}
for o in bpy.data.objects:
    if o.type in {"CAMERA", "LIGHT", "EMPTY"}:
        continue
    hidden[o.name] = o.hide_render
    o.hide_render = o.name not in keep

path = os.path.join(OUT, "vine_closeup.png")
scene.render.filepath = path
bpy.ops.render.render(write_still=True)
print("WROTE", path)
print("COUNT", len(VINE))
print("TOTAL_VERTS", sum(r["verts"] for r in rows))
print("TOTAL_FACES", sum(r["faces"] for r in rows))
