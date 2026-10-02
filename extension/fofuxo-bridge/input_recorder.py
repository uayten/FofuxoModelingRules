"""Pass-through review input with surface coordinates and bounded drag samples."""

import json
import time

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

INPUT_LOG = "review.input.jsonl"
MAX_DRAG_POINTS = 32
_windows = set()
_generation = 0


def write_record(record):
    from .instance import _review_info, recording_path
    if not _review_info() or not bpy.data.filepath:
        return
    path = recording_path(INPUT_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"t": round(time.time(), 3), **record}, ensure_ascii=False) + "\n")


def surface_sample(context, event):
    from bpy_extras import view3d_utils
    from .instance import _review_info
    from .mesh_io import ID_ATTR
    obj = context.view_layer.objects.active
    info = _review_info()
    if not info or obj is None or obj.type != "MESH" or obj.name not in info["objects"]:
        return None
    region = area = None
    for candidate in context.window.screen.areas:
        if candidate.type != "VIEW_3D":
            continue
        for item in candidate.regions:
            if item.type == "WINDOW" and item.x <= event.mouse_x < item.x + item.width and item.y <= event.mouse_y < item.y + item.height:
                area, region = candidate, item
                break
    if region is None:
        return None
    rv3d = area.spaces.active.region_3d
    pixel = (event.mouse_x - region.x, event.mouse_y - region.y)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, pixel)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, pixel)
    depsgraph = context.evaluated_depsgraph_get()
    hit, point, normal, face, found, matrix = context.scene.ray_cast(depsgraph, origin, direction)
    if not hit or getattr(found, "original", found) != obj:
        return None
    if obj.mode == "EDIT":
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.verts.layers.int.get(ID_ATTR)
        vertices = [(vertex[layer] if layer else vertex.index, obj.matrix_world @ vertex.co) for vertex in bm.verts]
    else:
        attr = obj.data.attributes.get(ID_ATTR)
        vertices = [(attr.data[vertex.index].value if attr else vertex.index, obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
    if not vertices:
        return None
    tree = KDTree(len(vertices))
    for index, (vid, position) in enumerate(vertices):
        tree.insert(position, index)
    tree.balance()
    _, index, distance = tree.find(point)
    local = obj.matrix_world.inverted() @ point
    sample = {"object": obj.name, "vertex": f"v{vertices[index][0]}",
              "point_mm": [round(value * 1000, 3) for value in local], "nearest_mm": round(distance * 1000, 3)}
    from .regions import axis_signs
    sample["axis_signs"] = axis_signs(obj)
    ts = context.tool_settings
    brush = getattr(ts.sculpt, "brush", None) if obj.mode == "SCULPT" else None
    if brush:
        unified = getattr(ts.sculpt, "unified_paint_settings", None) or getattr(ts, "unified_paint_settings", None)
        radius_px = unified.size if unified and unified.use_unified_size else brush.size
        edge = view3d_utils.region_2d_to_location_3d(region, rv3d, (pixel[0] + radius_px, pixel[1]), point)
        local_edge = obj.matrix_world.inverted() @ edge
        sample["radius_mm"] = round((local_edge - local).length * 1000, 3)
        sample["brush"] = brush.name
    return sample


class LLM_BRIDGE_OT_record_input(bpy.types.Operator):
    bl_idname = "llm_modeling_bridge.record_input"
    bl_label = "Record review input"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):
        self.window_id = context.window.as_pointer()
        self.generation = _generation
        self.drag = None
        self.last_sample = 0.0
        _windows.add(self.window_id)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        from .instance import _review_info
        if self.generation != _generation or not _review_info():
            _windows.discard(self.window_id)
            return {"FINISHED"}
        try:
            if event.type in ("TIMER", "INBETWEEN_MOUSEMOVE") or event.type.startswith("TIMER"):
                return {"PASS_THROUGH"}
            if event.type == "MOUSEMOVE":
                if self.drag and time.monotonic() - self.last_sample >= 0.1:
                    sample = surface_sample(context, event)
                    if sample:
                        points = self.drag["points"]
                        if (Vector(sample["point_mm"]) - Vector(points[-1]["point_mm"])).length >= 1.0:
                            if len(points) >= MAX_DRAG_POINTS:
                                self.drag["points"] = points[::2]
                            self.drag["points"].append(sample)
                    self.last_sample = time.monotonic()
                return {"PASS_THROUGH"}
            if event.value not in ("PRESS", "RELEASE"):
                return {"PASS_THROUGH"}
            sample = surface_sample(context, event)
            record = {"event": "INPUT", "key": event.type, "value": event.value,
                      "modifiers": {key: bool(getattr(event, key)) for key in ("ctrl", "shift", "alt", "oskey")}}
            if sample:
                record["surface"] = sample
            write_record(record)
            if event.type in ("LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE"):
                if event.value == "PRESS" and sample:
                    self.drag = {"event": "DRAG", "button": event.type, "modifiers": record["modifiers"], "points": [sample]}
                elif event.value == "RELEASE" and self.drag and event.type == self.drag["button"]:
                    if sample:
                        self.drag["points"].append(sample)
                    if len(self.drag["points"]) > 1:
                        write_record(self.drag)
                    self.drag = None
        except (RuntimeError, ValueError, ReferenceError) as error:
            print(f"LLM Modeling Bridge: input recorder: {error}")
        return {"PASS_THROUGH"}


def start_recording():
    if bpy.app.background:
        return {"started": False, "reason": "background"}
    for window in bpy.context.window_manager.windows:
        if window.as_pointer() in _windows:
            continue
        area = next((area for area in window.screen.areas if area.type == "VIEW_3D"), None)
        if area:
            region = next(region for region in area.regions if region.type == "WINDOW")
            with bpy.context.temp_override(window=window, area=area, region=region):
                bpy.ops.llm_modeling_bridge.record_input("INVOKE_DEFAULT")
    return {"started": bool(_windows)}


def _start_after_load():
    from .instance import _review_info, _start_recording
    if _review_info():
        _start_recording()
        start_recording()
    return None


@bpy.app.handlers.persistent
def _on_load(*_args):
    global _generation
    _generation += 1
    _windows.clear()
    if not bpy.app.background and not bpy.app.timers.is_registered(_start_after_load):
        bpy.app.timers.register(_start_after_load, first_interval=0.5)


def register():
    bpy.utils.register_class(LLM_BRIDGE_OT_record_input)
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)


def unregister():
    global _generation
    _generation += 1
    _windows.clear()
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    if bpy.app.timers.is_registered(_start_after_load):
        bpy.app.timers.unregister(_start_after_load)
    bpy.utils.unregister_class(LLM_BRIDGE_OT_record_input)
