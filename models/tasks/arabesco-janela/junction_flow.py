"""New junction flow on a copy: cut both islands at their crossing, weld the seam.

Runs on a temp copy of the work file and prints the numbers, so the same steps
can be applied to the real file once they prove clean.
"""
import bpy
import bmesh
import shutil
import tempfile
import os

SRC = r"C:\Users\ant7a\OneDrive\Documentos\GitHub\FofuxoModelingRules\models\tasks\arabesco-janela\arabescos.blend"
tmp = tempfile.mkdtemp(prefix="junction_")
dst = os.path.join(tmp, "t.blend")
shutil.copy2(SRC, dst)
bpy.ops.wm.open_mainfile(filepath=dst)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'extension'))
import llm_modeling_bridge as b


def measure(name):
    obj = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    seen = set()
    comps = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        comps += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            cur = stack.pop()
            for e in cur.link_edges:
                w = e.other_vert(cur)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
    nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bd = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    tris = sum(1 for f in bm.faces if len(f.verts) == 3)
    bm.free()
    return {"v": len(obj.data.vertices), "f": len(obj.data.polygons), "components": comps,
            "non_manifold": nm, "boundary": bd, "tris": tris}


print("BEFORE", measure("Plane.001"))

obj = bpy.data.objects["Plane.001"]
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.intersect(mode="SELECT", separate_mode="NONE", threshold=1e-6)
bpy.ops.object.mode_set(mode="OBJECT")
print("AFTER_INTERSECT", measure("Plane.001"))

from llm_modeling_bridge import mesh_io
ids, _ = mesh_io.ensure_ids(obj.data, write=True)
out = b.weld_region("Plane.001", ids, ids, threshold=0.0002, sync=False)
print("AFTER_WELD", measure("Plane.001"), "pairs", len(out.get("pairs", [])))
print("TMP", dst)

