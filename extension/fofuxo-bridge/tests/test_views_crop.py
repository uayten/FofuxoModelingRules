"""Focused camera framing and annotation filtering without changing the model."""

import importlib
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm_modeling_bridge as bridge

render = importlib.import_module(bridge.__name__ + ".render")
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1
    print("ok " + message, flush=True)


root = Path(tempfile.mkdtemp(prefix="llm_bridge_views_crop_"))
bpy.ops.wm.save_as_mainfile(filepath=str(root / "test.blend"))
vertices = [(column, row, 0) for row in range(11) for column in range(11)]
faces = [(row * 11 + column, row * 11 + column + 1, (row + 1) * 11 + column + 1,
          (row + 1) * 11 + column) for row in range(10) for column in range(10)]
mesh = bpy.data.meshes.new("CropGridMesh")
mesh.from_pydata(vertices, [], faces)
obj = bpy.data.objects.new("CropGrid", mesh)
bpy.context.scene.collection.objects.link(obj)
bridge.sync(obj.name, render=False)
ids = [item.value for item in mesh.attributes[bridge.mesh_io.ID_ATTR].data]
selected = list(mesh.polygons[55].vertices)
focus = [ids[index] for index in selected]
face_marks = mesh.attributes.new("llm_bridge_show_face", "INT", "FACE")
face_marks.data[0].value = face_marks.data[55].value = 1
loop_marks = mesh.attributes.new("llm_bridge_loop", "INT", "EDGE")
loop_marks.data[0].value = 1
bridge.name_region(obj.name, "OutsideFocus", f"v{ids[0]}")
original_geometry = [list(vertex.co) for vertex in mesh.vertices]
original_labels = {attr.name: [item.value for item in attr.data]
                   for attr in mesh.attributes if attr.data_type == "INT"}
original_data = {kind: set(getattr(bpy.data, kind)) for kind in ("objects", "meshes", "cameras", "scenes")}
scene = render.Scene(obj, ids, bpy.context.evaluated_depsgraph_get())
cams = [render.Camera("top")]
full_scale, full_center = scene.fit(cams)
crop_scale, crop_center = scene.fit(cams, focus_points=scene.base[selected])
check(crop_scale > full_scale * 9, "one grid cell receives a genuine close camera framing")
check(np.allclose(crop_center, scene.base[selected].mean(axis=0)), "crop center follows the selected region")
check(not np.allclose(crop_center, full_center), "crop framing does not retain the whole-model center")

seen = []
original_cage = render.Scene.cage_panel
original_sub = render.Scene.sub_panel


def observe_cage(self, camera, scale, center, *args, **kwargs):
    check(not self.loops and not self.region_centers, "unrelated loop and region labels are hidden")
    check([label for label, _ in self.face_centers] == ["f55"], "only faces inside the focus retain their labels")
    seen.append((scale, center.copy()))
    return original_cage(self, camera, scale, center, *args, **kwargs)


def observe_sub(self, camera, scale, center, *args, **kwargs):
    check(scale == seen[-1][0] and np.array_equal(center, seen[-1][1]),
          "cage and Subdivision use exactly the same crop framing")
    return original_sub(self, camera, scale, center, *args, **kwargs)


with patch.object(render.Scene, "cage_panel", observe_cage), patch.object(render.Scene, "sub_panel", observe_sub):
    result = bridge.views(obj.name, ["top"], focus=focus, crop=True, context_labels=False, render_name="close")
check(Path(result["render"]).is_file(), "the focused sheet is written through the public views API")
check(original_geometry == [list(vertex.co) for vertex in mesh.vertices] and
      original_labels == {attr.name: [item.value for item in attr.data]
                          for attr in mesh.attributes if attr.data_type == "INT"},
      "rendering preserves geometry, ids and saved annotations")
check(all(set(getattr(bpy.data, kind)) == items for kind, items in original_data.items()),
      "rendering leaves no temporary scene data")


def observe_default(self, camera, scale, center, *args, **kwargs):
    check([label for label, _ in self.face_centers] == ["f0", "f55"] and
          len(self.loops) == len(scene.loops) and len(self.region_centers) == len(scene.region_centers),
          "existing focus calls keep their original face, loop and region annotations")
    check(scale == full_scale and np.array_equal(center, full_center),
          "existing focus calls retain whole-model framing unless crop is requested")
    return original_cage(self, camera, scale, center, *args, **kwargs)


with patch.object(render.Scene, "cage_panel", observe_default):
    bridge.views(obj.name, ["top"], focus=focus, render_name="existing-focus")


def observe_isolated(self, camera, scale, center, *args, **kwargs):
    check(len(self.cage_edges) == 4 and all(set(edge) <= set(selected) for edge in self.cage_edges),
          "isolated drawing contains only the selected face edges")
    check(set(self.draw_indices) == set(selected) and not any(self.copy_of),
          "unrelated vertices and mirror-copy wire are omitted from the isolated cage")
    check(scale > full_scale * 9 and [label for label, _ in self.face_centers] == ["f55"] and not self.loops,
          "isolating faces enables close framing with only relevant annotations")
    return original_cage(self, camera, scale, center, *args, **kwargs)


with patch.object(render.Scene, "cage_panel", observe_isolated):
    bridge.views(obj.name, ["top"], focus=focus, isolate=True, render_name="isolated")
check(original_geometry == [list(vertex.co) for vertex in mesh.vertices] and
      len(mesh.polygons) == 100 and original_labels == {attr.name: [item.value for item in attr.data]
                                                       for attr in mesh.attributes if attr.data_type == "INT"},
      "isolating the drawing never deletes or changes model geometry and annotations")
try:
    bridge.views(obj.name, ["top"], focus=focus[:2], isolate=True)
    raise AssertionError("incomplete-face isolation was accepted")
except ValueError:
    check(True, "incomplete-face isolation refuses instead of inventing a selected patch")
for invalid_focus in (None, [], [max(ids) + 999]):
    try:
        bridge.views(obj.name, ["top"], focus=invalid_focus, crop=True)
        raise AssertionError("invalid crop focus was accepted")
    except bridge.SyncError:
        check(True, "empty or unknown crop focus refuses before rendering")
try:
    bridge.views(obj.name, ["top"], focus=[ids[0]], crop=True)
    raise AssertionError("a zero-extent crop was accepted")
except ValueError:
    check(True, "a zero-extent region refuses instead of producing an unusable close")
panel = render.Panel(render.Camera("top"), 1.0, np.zeros(3))
blank = panel.img.copy()
for x in (-40, -3, render.PANEL + 3, render.PANEL + 40):  # a vertex left or right of a cropped panel
    panel.dot((x, render.PANEL / 2), render.WIRE_COPY, r=2)
check(np.array_equal(panel.img, blank), "a dot outside the panel paints nothing (no stripe across the row)")
print(f"VIEWS CROP ALL PASSED ({checks} checks)", flush=True)
