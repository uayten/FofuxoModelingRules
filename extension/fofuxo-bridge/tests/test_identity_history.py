"""Focused identity restoration for native undo's older custom-data snapshots."""

import importlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import bpy
import bmesh

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm_modeling_bridge as bridge

instance = importlib.import_module(bridge.__name__ + ".instance")
identity_history = importlib.import_module(bridge.__name__ + ".identity_history")
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1
    print("ok " + message, flush=True)


def ids():
    obj = bpy.context.object
    if obj.mode == "EDIT":
        cage = bmesh.from_edit_mesh(obj.data)
        layer = cage.verts.layers.int.get(bridge.mesh_io.ID_ATTR)
        return [vertex[layer] for vertex in cage.verts]
    return [item.value for item in obj.data.attributes[bridge.mesh_io.ID_ATTR].data]


def main():
    root = Path(tempfile.mkdtemp(prefix="llm_bridge_identity_"))
    bpy.ops.wm.save_as_mainfile(filepath=str(root / "test.blend"))
    bridge.register()
    bridge.sync("Cube", render=False)
    with patch.object(instance, "_review_info", return_value={"objects": ["Cube"]}):
        instance._start_recording()
        bpy.ops.ed.undo_push(message="Identity history baseline")
        bpy.ops.object.mode_set("EXEC_DEFAULT", True, mode="EDIT")
        initial = ids()
        bpy.ops.mesh.subdivide("EXEC_DEFAULT", True, number_cuts=1)
        expected = ids()
        check(len(expected) == 26 and len(set(expected)) == 26, "completed topology stores unique identities")
        bpy.ops.ed.undo()
        check(set(ids()) == set(initial), "native undo restores the original topology ids")
        bpy.ops.ed.redo()
        check(set(ids()) == set(expected), "native redo restores the exact ids from the completed topology operation")
        bpy.ops.mesh.select_all("EXEC_DEFAULT", True, action="DESELECT")
        bpy.ops.ed.undo()
        check(set(ids()) == set(expected), "native selection undo cannot change topology ids")
        cage = bmesh.from_edit_mesh(bpy.context.object.data)
        for edge in cage.edges:
            edge.select_set(all(abs(vertex.co.z) < 0.0001 for vertex in edge.verts))
        bmesh.update_edit_mesh(bpy.context.object.data)
        bpy.ops.mesh.dissolve_edges("EXEC_DEFAULT", True, use_verts=True)
        dissolved = ids()
        check(len(dissolved) < len(expected), "native dissolve changes the recorded topology")
        bpy.ops.ed.undo()
        check(set(ids()) == set(expected), "native dissolve undo restores removed ids exactly")
        bpy.ops.ed.redo()
        check(set(ids()) == set(dissolved), "native dissolve redo restores the recorded surviving ids")
        bpy.ops.ed.undo()
        instance._on_history_pre()
        cage = bmesh.from_edit_mesh(bpy.context.object.data)
        layer = cage.verts.layers.int.get(bridge.mesh_io.ID_ATTR)
        for vertex in cage.verts:
            vertex[layer] += 500
        bmesh.update_edit_mesh(bpy.context.object.data)
        instance._on_undo_human()
        check(ids() == expected, "undo with unchanged geometry restores recorded ids instead of stale custom data")
        rows = [json.loads(line) for line in (root / "review.ops.jsonl").read_text("utf-8").splitlines()]
        check(rows[-1]["op"] == "UNDO" and rows[-1]["identity_restored"], "undo receipt confirms identity restoration")
        context = bpy.context
        class PartialContext:
            def __getattr__(self, name):
                return None if name == "object" else getattr(context, name)
        with patch.object(bpy, "context", PartialContext()):
            check(instance._mesh_state()[0] == "Cube", "partial handler context resolves the active object through its view layer")
        bpy.ops.object.mode_set("EXEC_DEFAULT", True, mode="OBJECT")
        obj = bpy.context.object
        positions = [tuple(vertex.co) for vertex in obj.data.vertices]
        edges = [tuple(edge.vertices) for edge in obj.data.edges]
        faces = [tuple(face.vertices) for face in obj.data.polygons]
        expected_by_position = dict(zip(positions, ids()))
        instance._on_history_pre()
        order = list(reversed(range(len(positions))))
        remap = {old: new for new, old in enumerate(order)}
        obj.data.clear_geometry()
        obj.data.from_pydata([positions[index] for index in order],
                            [tuple(remap[index] for index in edge) for edge in edges],
                            [tuple(remap[index] for index in face) for face in faces])
        attribute = obj.data.attributes.new(bridge.mesh_io.ID_ATTR, "INT", "POINT")
        attribute.data.foreach_set("value", list(range(1000, 1000 + len(order))))
        instance._on_redo_human()
        check(all(vid == expected_by_position[tuple(vertex.co)] for vid, vertex in zip(ids(), obj.data.vertices)),
              "redo restores ids by geometry and connectivity despite reordered vertices")
        obj.data.vertices[0].co.x += 0.123
        check(not identity_history.restore(obj, instance._rec["identity_history"]),
              "unrecorded geometry does not receive a guessed identity snapshot")
        positions = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        signatures = identity_history.vertex_signatures(positions, [(0, 2), (1, 3)], [])
        check(signatures[0] != signatures[1], "connectivity distinguishes coincident vertices")
        bpy.ops.object.mode_set("EXEC_DEFAULT", True, mode="EDIT")
        cage = bmesh.from_edit_mesh(bpy.context.object.data)
        extra = cage.verts.new((0.42, 0.43, 0.44))
        extra[cage.verts.layers.int.get(bridge.mesh_io.ID_ATTR)] = -1
        first = instance._mesh_state()
        second = instance._mesh_state()
        check(first[2] == second[2], "repeated reads cannot retire ids allocated before the next recorder snapshot")
    bridge.unregister()
    print(f"IDENTITY HISTORY ALL PASSED ({checks} checks)", flush=True)


if __name__ == "__main__":
    main()
