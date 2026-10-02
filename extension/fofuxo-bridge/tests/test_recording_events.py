"""Focused event recorder checks: rapid operations must reach disk individually."""

import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import bpy
import bmesh

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm_modeling_bridge as bridge
import importlib

instance = importlib.import_module(bridge.__name__ + ".instance")
input_recorder = importlib.import_module(bridge.__name__ + ".input_recorder")
recording = importlib.import_module(bridge.__name__ + ".recording")
checks = 0


class LLM_TEST_OT_add_vertex(bpy.types.Operator):
    bl_idname = "llm_test.add_vertex"
    bl_label = "Add recording test vertex"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    retired_id: bpy.props.IntProperty()

    def execute(self, context):
        mesh = context.object.data
        cage = bmesh.from_edit_mesh(mesh)
        vertex = cage.verts.new((0.2, 0.2, 0.2))
        vertex[cage.verts.layers.int.get(bridge.mesh_io.ID_ATTR)] = self.retired_id
        instance._mesh_state(repair_ids=False)
        check(vertex[cage.verts.layers.int.get(bridge.mesh_io.ID_ATTR)] == self.retired_id,
              "priority input snapshots cannot modify native modal mesh data")
        bmesh.update_edit_mesh(mesh)
        return {"FINISHED"}


def check(condition, message):
    global checks
    assert condition, message
    checks += 1
    print("ok " + message, flush=True)


def main():
    root = Path(tempfile.mkdtemp(prefix="llm_bridge_recording_"))
    bpy.ops.wm.save_as_mainfile(filepath=str(root / "test.blend"))
    bridge.register()
    bpy.utils.register_class(LLM_TEST_OT_add_vertex)
    bridge.sync("Cube", render=False)
    log = root / "review.ops.jsonl"

    def read():
        return [json.loads(line) for line in log.read_text("utf-8").splitlines()] if log.exists() else []

    with patch.object(instance, "_review_info", return_value={"objects": ["Cube"]}):
        check("MODAL_PRIORITY" in input_recorder.LLM_BRIDGE_OT_record_input.bl_options,
              "input observer has priority over consuming native modal operators")
        instance._start_recording()
        check(not bpy.app.timers.is_registered(instance._record_ops), "operator capture has no repeating timer")
        bpy.ops.object.mode_set("EXEC_DEFAULT", True, mode="EDIT")
        check(read()[-1]["op"] == "OBJECT_OT_editmode_toggle", "mode changes are saved before the operator call returns")
        bpy.ops.mesh.select_all("EXEC_DEFAULT", True, action="SELECT")
        check(read()[-1]["op"] == "MESH_OT_select_all" and len(read()[-1]["selected"]) == 8,
              "selection is saved immediately with stable ids")
        bpy.ops.transform.translate("EXEC_DEFAULT", True, value=(0.001, 0, 0))
        first = read()[-1]
        bpy.ops.transform.translate("EXEC_DEFAULT", True, value=(-0.001, 0, 0))
        second = read()[-1]
        check(first["op"] == second["op"] == "TRANSFORM_OT_translate", "back-to-back moves have separate records")
        check(all(delta == [1.0, 0.0, 0.0] for delta in first["moved"].values())
              and all(delta == [-1.0, 0.0, 0.0] for delta in second["moved"].values()),
              "opposite rapid moves retain both deltas instead of cancelling in a poll")
        count = len(read())
        instance._on_record_update(None, None)
        instance._record_after_event()
        check(len(read()) == count, "graph and input callbacks do not duplicate completed operators")
        bpy.ops.mesh.subdivide("EXEC_DEFAULT", True, number_cuts=1)
        topology = read()[-1]
        check(topology["op"] == "TOPOLOGY" and len(topology["added_ids"]) == 18,
              "topology and new stable ids are saved immediately")
        cage = bmesh.from_edit_mesh(bpy.context.object.data)
        layer = cage.verts.layers.int.get(bridge.mesh_io.ID_ATTR)
        retired_id = max(vertex[layer] for vertex in cage.verts)
        for vertex in cage.verts:
            vertex.select_set(vertex[layer] == retired_id)
        bmesh.update_edit_mesh(bpy.context.object.data)
        bpy.ops.mesh.delete("EXEC_DEFAULT", True, type="VERT")
        bpy.ops.llm_test.add_vertex("EXEC_DEFAULT", True, retired_id=retired_id)
        fresh_id = read()[-1]["added_ids"][0]
        check(fresh_id > retired_id, "new Edit Mode vertices cannot reuse a deleted stable id")
        instance._on_history_pre()
        cage = bmesh.from_edit_mesh(bpy.context.object.data)
        restored = cage.verts.new((0.3, 0.3, 0.3))
        restored[cage.verts.layers.int.get(bridge.mesh_io.ID_ATTR)] = retired_id
        bmesh.update_edit_mesh(bpy.context.object.data)
        instance._on_undo_human()
        check(retired_id in read()[-1]["added_ids"], "undo restoration preserves the historical id")
        bpy.ops.object.mode_set("EXEC_DEFAULT", True, mode="OBJECT")

        # Boundary checks use real mesh changes without automating Sculpt input.
        with patch.object(instance, "_sculpt_record", return_value={"op": "SCULPT", "brush": "Grab", "radius_px": 32, "strength": 0.5}):
            context = SimpleNamespace(mode="SCULPT")
            press = SimpleNamespace(type="LEFTMOUSE", value="PRESS")
            release = SimpleNamespace(type="LEFTMOUSE", value="RELEASE")
            instance.record_input_event(context, press)
            bpy.context.object.data.vertices[0].co.x += 0.002
            instance.record_input_event(context, release)
            instance.record_input_event(context, press)
            first_stroke = read()[-1]
            instance._record_after_event()
            check(instance._rec["sculpt_active"], "a queued previous release does not end the next stroke")
            count = len(read())
            instance._on_record_update(None, None)
            check(instance._rec["sculpt_active"] and len(read()) == count,
                  "graph refreshes cannot split an unfinished stroke")
            bpy.context.object.data.vertices[0].co.x -= 0.001
            instance.record_input_event(context, release)
            instance._record_after_event()
            second_stroke = read()[-1]
        check(first_stroke["op"] == second_stroke["op"] == "SCULPT"
              and list(first_stroke["moved"].values()) == [[2.0, 0.0, 0.0]]
              and list(second_stroke["moved"].values()) == [[-1.0, 0.0, 0.0]],
              "stroke releases separate movements without an idle interval")
        check(first_stroke["brush"] == "Grab" and first_stroke["radius_px"] == 32,
              "stroke metadata is captured at its beginning")
        instance._on_history_pre()
        bpy.context.object.data.vertices[0].co.x += 0.003
        instance._on_undo_human()
        check(read()[-1]["op"] == "UNDO" and list(read()[-1]["moved"].values()) == [[3.0, 0.0, 0.0]],
              "undo boundaries retain their own movements")
        instance._on_history_pre()
        bpy.context.object.data.vertices[0].co.x -= 0.003
        instance._on_redo_human()
        check(read()[-1]["op"] == "REDO" and list(read()[-1]["moved"].values()) == [[-3.0, 0.0, 0.0]],
              "redo boundaries retain their own movements")
        summary = bridge.recording_summary(log)
        check(summary["capture"] == "event" and summary["combined_boundaries"] == 0,
              "summaries identify event capture without combined boundaries")

        grab = {"brush": "Grab", "brush_type": "GRAB", "radius_px": 32, "strength": 0.4,
                "radius_source": "brush", "strength_source": "brush"}
        smooth = input_recorder.apply_sculpt_modifiers(grab, shift=True)
        check(smooth["brush"] == "Smooth" and smooth["selected_brush"] == "Grab"
              and smooth["temporary_smooth"], "Shift records effective Smooth and preserves selected Grab")
        check(smooth["strength"] is None and smooth["radius_px"] is None
              and smooth["selected_strength"] == 0.4,
              "temporary Smooth does not inherit unverified Grab settings")
        check(not recording.replay_candidates([{"op": "SCULPT", "moved": {"0": [1, 0, 0]}, **smooth}]),
              "unknown temporary Smooth strength produces no invented replay command")
        shared = input_recorder.apply_sculpt_modifiers({**grab, "radius_source": "unified", "strength_source": "unified"}, shift=True)
        check(shared["radius_px"] == 32 and shared["strength"] == 0.4,
              "known shared settings remain available for temporary Smooth")
        hit = {"object": "Cube", "vertex": "v0", "point_mm": [0, 0, 0]}
        observer = SimpleNamespace(generation=input_recorder._generation, window_id=1234, drag=None, last_sample=0)
        middle_press = SimpleNamespace(type="MIDDLEMOUSE", value="PRESS", ctrl=False, shift=False, alt=False, oskey=False, is_repeat=False)
        middle_release = SimpleNamespace(**{**vars(middle_press), "value": "RELEASE"})
        with patch.object(input_recorder, "surface_sample", side_effect=[hit, RuntimeError("test ray miss")]):
            input_recorder.LLM_BRIDGE_OT_record_input.modal(observer, bpy.context, middle_press)
            input_recorder.LLM_BRIDGE_OT_record_input.modal(observer, bpy.context, middle_release)
        inputs = [json.loads(line) for line in (root / "review.input.jsonl").read_text("utf-8").splitlines()]
        check(inputs[-2]["key"] == "MIDDLEMOUSE" and inputs[-2]["value"] == "RELEASE"
              and inputs[-2]["surface_status"] == "error", "surface sampling failure cannot drop a release")
        check(inputs[-1]["complete"] and observer.drag is None,
              "a released drag closes even without an ending surface hit")
    bridge.unregister()
    bpy.utils.unregister_class(LLM_TEST_OT_add_vertex)
    check(all(callback not in handlers for handlers, callback in instance.RECORD_HANDLERS),
          "deactivation removes every recorder handler")
    check(not bpy.app.timers.is_registered(instance._record_after_event), "deactivation removes pending event callbacks")
    print(f"RECORDING EVENTS ALL PASSED ({checks} checks)", flush=True)


if __name__ == "__main__":
    main()
