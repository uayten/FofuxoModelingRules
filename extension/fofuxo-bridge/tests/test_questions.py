"""Tests for the questions asked inside the review Blender.

Run from the repository root:
    blender -b --factory-startup --python extension/fofuxo-bridge/tests/test_questions.py --python-exit-code 1
"""

import json
import sys
import tempfile
from pathlib import Path

import bpy

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2]))

import llm_modeling_bridge as fc  # noqa: E402
from llm_modeling_bridge import mesh_io, questions  # noqa: E402

fc.register()

failures = []


def check(condition, message):
    if condition:
        print("PASS", message)
    else:
        failures.append(message)
        print("FAIL", message)


def raises(call):
    try:
        call()
    except Exception:
        return True
    return False


def ids_where(obj, test):
    attr = obj.data.attributes["llm_modeling_bridge_id"].data
    return [attr[v.index].value for v in obj.data.vertices if test(v.co)]


def main():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=3, y_subdivisions=3, size=2.0)
    obj = bpy.context.object
    obj.name = "Leaf"
    mesh_io.ensure_ids(obj.data, write=True)
    work = Path(tempfile.mkdtemp(prefix="questions_"))
    source = work / "leaf.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(source))

    a, b = ids_where(obj, lambda co: abs(co.y + 1) < 1e-6)[:2]
    face = [ids_where(obj, lambda co, x=x, y=y: abs(co.x - x) < 1e-6 and abs(co.y - y) < 1e-6)[0]
            for x, y in ((-1, -1), (-1 / 3, -1), (-1 / 3, -1 / 3), (-1, -1 / 3))]
    asked = [{"object": "Leaf", "text": "Is this edge a fold?", "edges": [[a, b]]},
             {"object": "Leaf", "text": "Should this face be a triangle?", "faces": [face], "verts": [face[0]]}]
    check(raises(lambda: fc.ask([{"object": "Leaf", "text": "?", "verts": [999]}])), "ask refuses an id the object lacks")
    check(raises(lambda: fc.ask([{"object": "Leaf", "text": "?"}])), "ask refuses a question that marks nothing")
    out = fc.ask(asked)
    root = Path(out["file"]).parent
    check(out["questions"] == 2 and (root / questions.QUESTIONS).exists(), "ask writes the questions beside the file")
    check([q["answer"] for q in fc.answers()] == [None, None], "nothing is answered yet")

    # The human's side: the review Blender lives in the same folder.
    bpy.ops.wm.save_as_mainfile(filepath=str(root / "review.blend"))
    questions.poll()
    items = bpy.context.scene.llm_bridge_questions
    check([i.qid for i in items] == ["Q1", "Q2"], "the review Blender loads the questions")
    marks = questions._marks(items[1])
    check(marks is not None and len(marks[2]) == 1 and len(marks[0]) == 1, "a question's face and vertex are found by id")
    bpy.ops.llm_modeling_bridge.show_question(index=1)
    bm_selected = {mesh_io_id for mesh_io_id in _selected_ids(obj)}
    check(bm_selected == set(face), f"Show selects what the question marks ({sorted(bm_selected)})")
    bpy.ops.object.mode_set(mode="OBJECT")
    items[0].answer = "Yes, crease it"
    saved = json.loads((root / questions.ANSWERS).read_text("utf-8"))["answers"]
    check(saved == {"Q1": "Yes, crease it"}, "an answer is written as it is typed")
    questions._draw["loaded"] = None  # as when the AI rewrites the questions
    bpy.context.scene.llm_bridge_questions.clear()
    questions.poll()
    check(bpy.context.scene.llm_bridge_questions[0].answer == "Yes, crease it", "a reload keeps the answers")

    # Back on the AI's side.
    bpy.ops.wm.open_mainfile(filepath=str(source))
    got = fc.answers()
    check([q["answer"] for q in got] == ["Yes, crease it", None] and got[0]["text"] == "Is this edge a fold?",
          "answers() pairs each question with what the human wrote")
    questions.clear()
    check(fc.answers() == [], "clear drops an earlier review's questions")

    print("FAILURES", len(failures))
    if failures:
        raise SystemExit(1)


def _selected_ids(obj):
    import bmesh
    bm = bmesh.from_edit_mesh(obj.data)
    layer = bm.verts.layers.int.get("llm_modeling_bridge_id")
    return [v[layer] for v in bm.verts if v.select]


main()
