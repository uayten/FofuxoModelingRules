"""Questions the AI asks inside the human's review Blender.

The AI names the vertices, edges and faces a question is about, by stable id;
the human's Blender marks them in the viewport, lists the questions in the
LLM tab with a field for each answer, and writes the answers beside the
review as they are typed. collect() returns them with the correction.

    ask(questions)      AI: write <file>.bridge/review.questions.json
    answers()           AI: the questions with what the human wrote
    poll()              human: (re)load the questions when the file changes

A question: {"object": "Plane.001", "text": "...", "verts": [12, 13],
"edges": [[12, 13]], "faces": [[12, 13, 40, 41]]}.
"""

import json
import textwrap
import time
from pathlib import Path

import bpy

from .mesh_io import ID_ATTR

QUESTIONS = "review.questions.json"
ANSWERS = "review.answers.json"
WRAP = 46  # characters per line of a question, in the panel and the viewport

_draw = {"handles": [], "loaded": None}


class QuestionError(RuntimeError):
    pass


# --- the AI's side -------------------------------------------------------------

def _root():
    from .migration import data_root
    return data_root()


def ask(questions):
    """Write the questions for the review Blender (an open review reloads them
    on its next poll). Each names its object and the ids it is about; the ids
    are checked against the AI's file. Clears the answers to earlier ones."""
    questions = list(questions)
    if not questions:
        raise QuestionError("ask needs one question at least")
    out = []
    for k, q in enumerate(questions, 1):
        obj = bpy.data.objects.get(q.get("object", ""))
        if obj is None or obj.type != "MESH":
            raise QuestionError(f"question {k}: no mesh object {q.get('object')!r}")
        if not q.get("text"):
            raise QuestionError(f"question {k}: no text")
        attr = obj.data.attributes.get(ID_ATTR)
        known = {a.value for a in attr.data} if attr else set()
        verts = [int(v) for v in q.get("verts", ())]
        edges = [[int(a), int(b)] for a, b in q.get("edges", ())]
        faces = [[int(v) for v in f] for f in q.get("faces", ())]
        named = set(verts) | {v for e in edges for v in e} | {v for f in faces for v in f}
        if not named:
            raise QuestionError(f"question {k}: mark at least one vertex, edge or face")
        missing = sorted(named - known)
        if missing:
            raise QuestionError(f"question {k}: {obj.name} has no ids {missing}")
        out.append({"id": f"Q{k}", "object": obj.name, "text": q["text"],
                    "verts": verts, "edges": edges, "faces": faces})
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    (root / ANSWERS).unlink(missing_ok=True)
    (root / QUESTIONS).write_text(json.dumps({"written": time.time(), "questions": out}, ensure_ascii=False,
                                             indent=1), "utf-8")
    return {"questions": len(out), "file": str(root / QUESTIONS)}


def clear():
    """Drop the questions and answers of an earlier review."""
    root = _root()
    for name in (QUESTIONS, ANSWERS):
        (root / name).unlink(missing_ok=True)


def answers():
    """The questions of the review with what the human wrote (None when
    unanswered); [] when no question was asked."""
    root = _root()
    try:
        asked = json.loads((root / QUESTIONS).read_text("utf-8"))["questions"]
    except (OSError, ValueError, KeyError):
        return []
    try:
        given = json.loads((root / ANSWERS).read_text("utf-8")).get("answers", {})
    except (OSError, ValueError):
        given = {}
    return [{"id": q["id"], "text": q["text"], "answer": given.get(q["id"]) or None} for q in asked]


# --- the human's side ----------------------------------------------------------

def _beside(name):
    return Path(bpy.data.filepath).with_name(name) if bpy.data.filepath else None


def _write_answers(scene):
    path = _beside(ANSWERS)
    if path is None:
        return
    given = {item.qid: item.answer for item in scene.llm_bridge_questions if item.answer.strip()}
    path.write_text(json.dumps({"written": time.time(), "answers": given}, ensure_ascii=False, indent=1), "utf-8")


def _on_answer(self, context):
    _write_answers(context.scene)


class LLM_BRIDGE_Question(bpy.types.PropertyGroup):
    qid: bpy.props.StringProperty()
    text: bpy.props.StringProperty()
    object: bpy.props.StringProperty()
    data: bpy.props.StringProperty()  # the marked ids, as JSON
    answer: bpy.props.StringProperty(name="Answer", update=_on_answer)


def poll():
    """Load the questions beside the open review when they change, keeping the
    answers already typed. Called from the human's Blender poll."""
    path = _beside(QUESTIONS)
    scene = bpy.context.scene
    if path is None or scene is None or not hasattr(scene, "llm_bridge_questions"):
        return
    try:
        stamp = path.stat().st_mtime
    except OSError:
        if _draw["loaded"] is not None:
            scene.llm_bridge_questions.clear()
            _draw["loaded"] = None
            _handlers(False)
        return
    if stamp == _draw["loaded"]:
        return
    try:
        asked = json.loads(path.read_text("utf-8"))["questions"]
    except (OSError, ValueError, KeyError):
        return
    try:
        given = json.loads(_beside(ANSWERS).read_text("utf-8")).get("answers", {})
    except (OSError, ValueError):
        given = {}
    items = scene.llm_bridge_questions
    items.clear()
    for q in asked:
        item = items.add()
        item.qid, item.text, item.object = q["id"], q["text"], q["object"]
        item.data = json.dumps({k: q.get(k, []) for k in ("verts", "edges", "faces")})
        item["answer"] = given.get(q["id"], "")  # no update callback: the file already says it
    scene.llm_bridge_question_index = 0
    _draw["loaded"] = stamp
    _handlers(True)
    _redraw()
    print(f"LLM Modeling Bridge: {len(asked)} question(s) from the LLM in the LLM tab")


def _redraw():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _id_positions(obj):
    """World position of each stable id, from the edit mesh when in Edit Mode."""
    mw = obj.matrix_world
    if obj.mode == "EDIT":
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.verts.layers.int.get(ID_ATTR)
        if layer is None:
            return {}
        return {v[layer]: mw @ v.co for v in bm.verts}
    attr = obj.data.attributes.get(ID_ATTR)
    if attr is None:
        return {}
    return {a.value: mw @ v.co for a, v in zip(attr.data, obj.data.vertices)}


def _marks(item):
    obj = bpy.data.objects.get(item.object)
    if obj is None or obj.type != "MESH":
        return None
    data = json.loads(item.data)
    pos = _id_positions(obj)
    verts = [pos[v] for v in data["verts"] if v in pos]
    edges = [(pos[a], pos[b]) for a, b in data["edges"] if a in pos and b in pos]
    faces = [[pos[v] for v in f] for f in data["faces"] if all(v in pos for v in f)]
    every = verts + [p for e in edges for p in e] + [p for f in faces for p in f]
    if not every:
        return None
    center = sum(every, every[0].copy() * 0) / len(every)
    return verts, edges, faces, center


ACTIVE = (1.0, 0.25, 0.05)
OTHER = (0.2, 0.7, 1.0)


def _draw_marks():
    import gpu
    from gpu_extras.batch import batch_for_shader

    scene = bpy.context.scene
    items = getattr(scene, "llm_bridge_questions", None)
    if not items:
        return
    region = bpy.context.region
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("NONE")
    flat = gpu.shader.from_builtin("UNIFORM_COLOR")
    line = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
    point = gpu.shader.from_builtin("POINT_UNIFORM_COLOR")
    for k, item in enumerate(items):
        marks = _marks(item)
        if marks is None:
            continue
        verts, edges, faces, _center = marks
        rgb = ACTIVE if k == scene.llm_bridge_question_index else OTHER
        if faces:
            tris = [(f[0], f[i], f[i + 1]) for f in faces for i in range(1, len(f) - 1)]
            batch = batch_for_shader(flat, "TRIS", {"pos": [p for t in tris for p in t]})
            flat.bind()
            flat.uniform_float("color", (*rgb, 0.35))
            batch.draw(flat)
        outline = edges + [(f[i], f[(i + 1) % len(f)]) for f in faces for i in range(len(f))]
        if outline:
            batch = batch_for_shader(line, "LINES", {"pos": [p for e in outline for p in e]})
            line.bind()
            line.uniform_float("viewportSize", (region.width, region.height))
            line.uniform_float("lineWidth", 4.0 if k == scene.llm_bridge_question_index else 2.0)
            line.uniform_float("color", (*rgb, 1.0))
            batch.draw(line)
        if verts:
            gpu.state.point_size_set(12.0 if k == scene.llm_bridge_question_index else 8.0)
            batch = batch_for_shader(point, "POINTS", {"pos": verts})
            point.bind()
            point.uniform_float("color", (*rgb, 1.0))
            batch.draw(point)
    gpu.state.depth_test_set("LESS_EQUAL")
    gpu.state.blend_set("NONE")


def _draw_labels():
    import blf
    import gpu
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    from gpu_extras.batch import batch_for_shader

    scene = bpy.context.scene
    items = getattr(scene, "llm_bridge_questions", None)
    if not items:
        return
    region, rv3d = bpy.context.region, bpy.context.region_data
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    size = 14
    for k, item in enumerate(items):
        marks = _marks(item)
        if marks is None:
            continue
        at = location_3d_to_region_2d(region, rv3d, marks[3])
        if at is None:
            continue
        active = k == scene.llm_bridge_question_index
        lines = [item.qid] + (textwrap.wrap(item.text, WRAP) if active else [])
        blf.size(0, size)
        width = max(blf.dimensions(0, text)[0] for text in lines) + 12
        height = len(lines) * (size + 4) + 8
        x, y = at.x + 18, at.y + 18
        gpu.state.blend_set("ALPHA")
        box = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
        batch = batch_for_shader(shader, "TRIS", {"pos": box}, indices=[(0, 1, 2), (0, 2, 3)])
        shader.bind()
        shader.uniform_float("color", (0.05, 0.05, 0.05, 0.8))
        batch.draw(shader)
        gpu.state.blend_set("NONE")
        rgb = ACTIVE if active else OTHER
        for n, text in enumerate(lines):
            blf.position(0, x + 6, y + height - (n + 1) * (size + 4), 0)
            blf.color(0, *(rgb if n == 0 else (1.0, 1.0, 1.0)), 1.0)
            blf.draw(0, text)


def _handlers(on):
    if on and not _draw["handles"]:
        space = bpy.types.SpaceView3D
        _draw["handles"] = [space.draw_handler_add(_draw_marks, (), "WINDOW", "POST_VIEW"),
                            space.draw_handler_add(_draw_labels, (), "WINDOW", "POST_PIXEL")]
    elif not on and _draw["handles"]:
        bpy.types.SpaceView3D.draw_handler_remove(_draw["handles"][0], "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(_draw["handles"][1], "WINDOW")
        _draw["handles"] = []


class LLM_BRIDGE_OT_show_question(bpy.types.Operator):
    """Select what the question is about, in Edit Mode, and frame it"""

    bl_idname = "llm_modeling_bridge.show_question"
    bl_label = "Show"
    index: bpy.props.IntProperty()

    def execute(self, context):
        import bmesh
        scene = context.scene
        item = scene.llm_bridge_questions[self.index]
        scene.llm_bridge_question_index = self.index
        obj = bpy.data.objects.get(item.object)
        if obj is None:
            self.report({"WARNING"}, f"No object {item.object}")
            return {"CANCELLED"}
        if context.mode != "OBJECT" and context.edit_object is not obj:
            bpy.ops.object.mode_set(mode="OBJECT")
        for other in context.selected_objects:
            other.select_set(False)
        obj.hide_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        if obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
        data = json.loads(item.data)
        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.verts.layers.int.get(ID_ATTR)
        by_id = {v[layer]: v for v in bm.verts} if layer else {}
        for elem in (*bm.verts, *bm.edges, *bm.faces):
            elem.select = False
        for v in data["verts"]:
            if v in by_id:
                by_id[v].select = True
        for a, b in data["edges"]:
            edge = bm.edges.get((by_id[a], by_id[b])) if a in by_id and b in by_id else None
            if edge is not None:
                edge.select = True
        for f in data["faces"]:
            face = bm.faces.get([by_id[v] for v in f]) if all(v in by_id for v in f) else None
            if face is not None:
                face.select = True
        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data)
        if context.area and context.area.type == "VIEW_3D":
            bpy.ops.view3d.view_selected()
        _redraw()
        return {"FINISHED"}


class LLM_BRIDGE_PT_questions(bpy.types.Panel):
    bl_label = "Questions from the LLM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM"

    @classmethod
    def poll(cls, context):
        return bool(getattr(context.scene, "llm_bridge_questions", None))

    def draw(self, context):
        scene = context.scene
        items = scene.llm_bridge_questions
        done = sum(1 for item in items if item.answer.strip())
        col = self.layout.column()
        col.label(text=f"{done} of {len(items)} answered", icon="QUESTION")
        for k, item in enumerate(items):
            box = col.box()
            row = box.row()
            row.alert = k == scene.llm_bridge_question_index
            row.label(text=f"{item.qid}  {item.object}")
            row.operator(LLM_BRIDGE_OT_show_question.bl_idname, icon="VIEWZOOM").index = k
            for text in textwrap.wrap(item.text, WRAP):
                box.label(text=text)
            box.prop(item, "answer", text="")
        col.separator()
        col.label(text="Answered them all? Tell the LLM in the app.")


CLASSES = (LLM_BRIDGE_Question, LLM_BRIDGE_OT_show_question, LLM_BRIDGE_PT_questions)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.llm_bridge_questions = bpy.props.CollectionProperty(type=LLM_BRIDGE_Question)
    bpy.types.Scene.llm_bridge_question_index = bpy.props.IntProperty(update=lambda self, context: _redraw())


def unregister():
    _handlers(False)
    _draw["loaded"] = None
    del bpy.types.Scene.llm_bridge_question_index
    del bpy.types.Scene.llm_bridge_questions
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
