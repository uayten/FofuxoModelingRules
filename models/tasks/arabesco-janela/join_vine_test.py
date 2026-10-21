"""Prototype: join the arch vine into one mesh, without saving the .blend.

Each piece is evaluated with its own modifiers into a fresh mesh (the stack in
the file is untouched), the copies are joined, and the result is rendered next
to the pieces. The prototype objects are removed and the file is reloaded from
disk at the end, so the work file stays exactly as it was.
"""
import bpy
import math
import os
from mathutils import Vector

OUT = os.environ.get("FOFUXO_OUT", r"C:\Users\ant7a\OneDrive\Documentos\GitHub\FofuxoModelingRules\models\tasks\arabesco-janela\renders")
VINE = ["Plane.%03d" % i for i in list(range(17, 28)) + list(range(29, 38))]
PATH = bpy.data.filepath

scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()

temp = bpy.data.collections.new("__join_test")
scene.collection.children.link(temp)
copies = []
for name in VINE:
    src = bpy.data.objects[name]
    ev = src.evaluated_get(depsgraph)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=depsgraph)
    me.name = name + "_eval"
    ob = bpy.data.objects.new(name + "_eval", me)
    ob.matrix_world = src.matrix_world
    temp.objects.link(ob)
    copies.append(ob)

before_verts = sum(len(o.data.vertices) for o in copies)
before_faces = sum(len(o.data.polygons) for o in copies)

bpy.ops.object.select_all(action="DESELECT")
for ob in copies:
    ob.select_set(True)
bpy.context.view_layer.objects.active = copies[0]
bpy.ops.object.join()
joined = bpy.context.view_layer.objects.active
joined.name = "Videira_JUNTADA_TESTE"
joined.data.name = "Videira Juntada (teste)"

used = {i for p in joined.data.polygons for i in p.vertices}
result = {
    "pieces": len(VINE),
    "verts_in": before_verts,
    "faces_in": before_faces,
    "verts_out": len(joined.data.vertices),
    "faces_out": len(joined.data.polygons),
    "materials": [s.material.name if s.material else None for s in joined.material_slots],
    "loose_verts": len(joined.data.vertices) - len(used),
}

# Render: the joined mesh alone, same framing as the pieces render.
pts = [joined.matrix_world @ Vector(c) for c in joined.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo + hi) / 2
size = hi - lo

cam = bpy.data.objects.get("VineCam")
if cam is None:
    cam_data = bpy.data.cameras.new("VineCam")
    cam = bpy.data.objects.new("VineCam", cam_data)
    scene.collection.objects.link(cam)
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

for o in bpy.data.objects:
    if o.type in {"CAMERA", "LIGHT", "EMPTY"}:
        continue
    o.hide_render = o.name not in {"Videira_JUNTADA_TESTE"}

path = os.path.join(OUT, "vine_joined_test.png")
scene.render.filepath = path
bpy.ops.render.render(write_still=True)
result["render"] = path

# Leave the file untouched: reload it from disk.
bpy.ops.wm.open_mainfile(filepath=PATH)
print("RELOADED", bpy.data.filepath, "dirty=", bpy.data.is_dirty)

result = {k: v for k, v in result.items()}
