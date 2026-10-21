"""Tight crop of the leaf-stem junction, cage and subdivision, via views().

Focus is picked by position, so the same box works before and after the weld.
"""
import bpy
import llm_modeling_bridge as b
from mathutils import Vector

OBJ = "Plane.001"
BOX_MIN = Vector((0.02, -0.09, 2.08))
BOX_MAX = Vector((0.12, -0.04, 2.19))
LABEL = "junction"

obj = bpy.data.objects[OBJ]
me = obj.data
attr = me.attributes["llm_modeling_bridge_id"].data
focus = []
for v in me.vertices:
    p = obj.matrix_world @ v.co
    if all(BOX_MIN[i] <= p[i] <= BOX_MAX[i] for i in range(3)):
        focus.append(attr[v.index].value)

out = b.views(OBJ, views=["front", (30, 14)], render_name=LABEL,
              focus=focus, crop=True, isolate=True)
print("RENDER", out.get("render"))
print("FOCUS", len(focus))
