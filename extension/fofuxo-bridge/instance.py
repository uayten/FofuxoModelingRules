"""Two Blenders: the AI's own instance and the human's review.

The AI works in a Blender of its own, started with `-- --llm-bridge-ai`
(launcher.py does it): every editor is painted black with a notice, input
is swallowed, and the MCP server runs there. A human's Blender stops its own
MCP server while an AI instance is alive, so the MCP always reaches the AI's.

    review(names)   save the AI's file, write the objects to
                    <file>.bridge/review.blend and open it in a normal Blender;
                    while that review is open, later calls announce a newer
                    version and the human loads it (LLM tab)
    absorb()        read what the human saved in the review back into the
                    AI's objects (mesh, modifiers, transform) and sync them:
                    the edits come back as blender_edits
"""

import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import bpy

from .lock import PROP as LOCK_PROP

AI_FLAG = "--llm-bridge-ai"
MARKER = Path(tempfile.gettempdir()) / "llm_modeling_bridge_ai.json"
REVIEW_PROP = "llm_bridge_review"
UPDATE_NOTICE = "review.update.json"
OPENED = "review.opened.json"
COLLECT = "review.collect.json"  # the AI asks the human's Blender to save the review (and close)
OPS_LOG = "review.ops.jsonl"  # every operator the human runs in the review, one JSON line each
RECORD = 0.5  # s, how often the human's Blender copies its new operators to OPS_LOG
POLL = 3.0  # s, how often a human's Blender looks for the AI instance and updates
NOTICE = ("Blender de uso exclusivo do LLM",
          "Esta janela é de uso exclusivo do LLM.",
          "Para editar ou ver o modelo, requisite acesso na conversa e o seu modelo abrirá",
          "um novo Blender ou liberará a edição usando essa janela.",
          "Não feche essa janela enquanto estiver trabalhando em conjunto com a LLM",
          "na modelagem de um objeto.")
_state = {"handles": [], "review_seen": None, "update_seen": None, "message": ""}
_state["human_editing"] = False


class InstanceError(RuntimeError):
    pass


def assert_ai_access():
    if _state.get("human_editing"):
        raise InstanceError("the human is editing this window; return it to the LLM before running edits")


def human_access():
    """Release this AI window, keeping the MCP connected for status and return."""
    if not is_ai() or bpy.app.background:
        raise InstanceError("human_access requires the AI's interactive Blender")
    if not bpy.data.filepath:
        raise InstanceError("save the file before handing over the window")
    if _state.get("human_editing"):
        raise InstanceError("the human already holds this window")
    from .migration import data_root
    import shutil
    bpy.ops.wm.save_mainfile()
    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    before = root / "handover.before.blend"
    shutil.copy2(bpy.data.filepath, before)
    _state["human_before"] = str(before)
    _state["last_human_example"] = None
    _state["human_objects"] = [obj.name for obj in bpy.data.objects if obj.type == "MESH"]
    for filename in ("handover.ops.jsonl", "handover.input.jsonl"):
        (root / filename).write_text("", "utf-8")
    from .lock import unlock
    unlock()
    _state["human_editing"] = True
    screen_off()
    _focus(False)
    _start_recording()
    from .input_recorder import start_recording
    start_recording()
    return {"access": "human", "file": bpy.data.filepath}


def resume_ai(save=True):
    """The human returns the window; save their work before enabling edits."""
    if not _state.get("human_editing"):
        raise InstanceError("this window has not been handed to the human")
    from .lock import _leave_edit_mode
    _leave_edit_mode()
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    _record_ops()
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        from .catalog import archive_review, human_directory
        from .migration import data_root
        names = list(dict.fromkeys([*_state.get("human_objects", []), *[obj.name for obj in bpy.data.objects if obj.type == "MESH"]]))
        if names:
            example = archive_review(_state["human_before"], bpy.data.filepath, names,
                                     human_dir=human_directory(bpy.data.filepath), recording_root=data_root())
            _state["last_human_example"] = example["example"]
    _state["human_editing"] = False
    _setup_ai()
    return {"access": "ai", "saved": save, "file": bpy.data.filepath, "example": _state.get("last_human_example")}


# --- which Blender is this -----------------------------------------------------

def is_ai():
    return AI_FLAG in sys.argv or "--fofuxo-ai" in sys.argv


def _alive(pid):
    if not pid:
        return False
    if os.name == "nt":
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(handle, ctypes.byref(code))
        k32.CloseHandle(handle)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def ai_instance():
    """The live AI instance from the marker file, or None."""
    for path in (MARKER, MARKER.with_name("fofuxo_cage_ai.json")):
        try:
            data = json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if _alive(data.get("pid")):
            return data
    return None


def instance():
    """Who this Blender is: {"role": "ai" or "human", "pid", "file", ...}."""
    out = {"role": "ai" if is_ai() else "human", "pid": os.getpid(), "file": bpy.data.filepath,
           "mcp_running": _mcp_running(), "access": "human" if _state.get("human_editing") else "ai" if is_ai() else "human"}
    ai = ai_instance()
    if not is_ai() and ai:
        out["ai_pid"] = ai["pid"]
    review = bpy.context.scene.get(REVIEW_PROP) if bpy.context.scene else None
    if review:
        out["review_of"] = json.loads(review)["source"]
    return out


# --- the MCP server ------------------------------------------------------------

def _mcp_module(name):
    return next((m for key, m in sys.modules.items() if key.endswith(f".mcp.{name}")), None)


def _mcp_running():
    server = _mcp_module("mcp_to_blender_server")
    return bool(server and server.is_running())


def release_mcp():
    """Stop this Blender's MCP server, so the AI instance's answers alone."""
    if not _mcp_running():
        return False
    bpy.ops.blmcp.server_stop()
    return True


def _ensure_mcp():
    if not _mcp_running() and hasattr(bpy.ops, "blmcp"):
        try:
            bpy.ops.blmcp.server_start()
        except RuntimeError as e:
            print(f"LLM Modeling Bridge: MCP server not started: {e}")


# --- the AI's screen -----------------------------------------------------------

def _draw_black(big):
    import blf
    import gpu
    from gpu_extras.batch import batch_for_shader

    region = bpy.context.region
    w, h = region.width, region.height
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    batch = batch_for_shader(shader, "TRIS", {"pos": [(0, 0), (w, 0), (w, h), (0, h)]}, indices=[(0, 1, 2), (0, 2, 3)])
    gpu.state.blend_set("NONE")
    shader.bind()
    shader.uniform_float("color", (0.0, 0.0, 0.0, 1.0))
    batch.draw(shader)
    if not big or w < 200 or h < 120:
        return
    size = max(14, min(32, w // 40))
    lines = list(NOTICE) + ([_state["message"]] if _state["message"] else [])
    y = h / 2 + size * len(lines) / 2
    for k, text in enumerate(lines):
        s = size if k == 0 else int(size * 0.6)
        blf.size(0, s)
        tw, _ = blf.dimensions(0, text)
        blf.position(0, max(10, (w - tw) / 2), y, 0)
        blf.color(0, 1.0, 0.55 if k == 0 else 1.0, 0.1 if k == 0 else 1.0, 1.0)
        blf.draw(0, text)
        y -= s * 1.8


def _spaces():
    return [cls for cls in bpy.types.Space.__subclasses__() if hasattr(cls, "draw_handler_add")]


def screen_on():
    """Paint every editor black, with the notice in the largest ones."""
    if _state["handles"]:
        return
    regions = ("WINDOW", "HEADER", "TOOLS", "UI", "TOOL_HEADER", "TOOL_PROPS", "NAVIGATION_BAR", "EXECUTE",
               "FOOTER", "CHANNELS", "ASSET_SHELF", "ASSET_SHELF_HEADER")
    for space in _spaces():
        for region in regions:
            try:
                handle = space.draw_handler_add(_draw_black, (region == "WINDOW",), region, "POST_PIXEL")
            except (TypeError, ValueError, RuntimeError):
                continue
            _state["handles"].append((space, handle, region))
    _redraw()


def screen_off():
    for space, handle, region in _state["handles"]:
        space.draw_handler_remove(handle, region)
    _state["handles"].clear()
    _redraw()


def _redraw():
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            area.tag_redraw()


def say(text):
    """A status line under the notice on the AI's screen."""
    _state["message"] = text or ""
    _redraw()


class LLM_BRIDGE_OT_ai_screen(bpy.types.Operator):
    """Swallow every input event in the AI's own Blender"""

    bl_idname = "llm_modeling_bridge.ai_screen"
    bl_label = "LLM screen"

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not _state["handles"]:
            return {"FINISHED"}
        return {"RUNNING_MODAL"}  # the window's close button still works


def _window_area():
    win = bpy.context.window_manager.windows[0]
    area = max(win.screen.areas, key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == "WINDOW")
    return win, area, region


def _focus(on):
    """One area over the whole window, top bar and status bar hidden
    (Blender's focus mode), or back to the file's own layout."""
    win, area, region = _window_area()
    if on == win.screen.show_fullscreen:
        return
    with bpy.context.temp_override(window=win, area=area, region=region):
        if on:
            bpy.ops.screen.screen_full_area(use_hide_panels=True)
        else:
            bpy.ops.screen.back_to_previous()


def _setup_ai():
    if _state.get("human_editing"):
        return None
    wm = bpy.context.window_manager
    if not wm.windows:
        return 0.5  # not up yet
    MARKER.write_text(json.dumps({"pid": os.getpid(), "file": bpy.data.filepath, "started": time.time(),
                                  "binary": bpy.app.binary_path}), "utf-8")
    screen_on()
    _focus(True)
    win, area, region = _window_area()
    if not any(op.bl_idname == "LLM_MODELING_BRIDGE_OT_ai_screen" for op in win.modal_operators):
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.llm_modeling_bridge.ai_screen("INVOKE_DEFAULT")
    _ensure_mcp()
    return None


@bpy.app.handlers.persistent
def _on_load(*_args):
    # A file brings its own layout and drops modal operators: set up again.
    if is_ai() and not bpy.app.timers.is_registered(_setup_ai):
        bpy.app.timers.register(_setup_ai, first_interval=0.2)


@bpy.app.handlers.persistent
def _on_save_pre(*_args):
    # The AI's file keeps the layout it came with, not the focus mode.
    if is_ai() and not _state.get("human_editing") and bpy.context.window_manager.windows:
        _focus(False)


def _plain(v):
    if isinstance(v, (bool, int, float, str)) or v is None:
        return v
    if isinstance(v, dict):
        return v
    try:
        return [_plain(x) for x in v]
    except TypeError:
        return str(v)


_rec = {"last": None}


def _signature(op):
    return (op.as_pointer(), op.bl_idname, json.dumps(_op_record(op)["props"], sort_keys=True, default=str))


def _op_record(op):
    props = {}
    for p in op.properties.bl_rna.properties:
        if p.identifier == "rna_type":
            continue
        try:
            v = getattr(op.properties, p.identifier)
        except AttributeError:
            continue
        if hasattr(v, "bl_rna"):  # a nested operator (a macro's step): its own settings
            v = {q.identifier: _plain(getattr(v, q.identifier, None))
                 for q in v.bl_rna.properties if q.identifier != "rna_type"}
        props[p.identifier] = _plain(v)
    return {"op": op.bl_idname, "name": op.name, "props": props}


def _log(lines):
    if not lines or _review_info() is None or not bpy.data.filepath:
        return
    path = recording_path(OPS_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps({"t": round(time.time(), 2), **line}, default=str) + "\n")


def recording_path(filename):
    path = Path(bpy.data.filepath)
    if _state.get("human_editing"):
        return path.with_suffix(".bridge") / filename.replace("review.", "handover.", 1)
    return path.with_name(filename)


MOVED_MIN = 0.05  # mm: a vertex that moved less is left out of a "moved" record


def _mesh_state():
    """(object name, mode, ids, positions in mm, selected ids) of the active
    reviewed mesh, read the way its mode keeps it (bmesh in Edit Mode)."""
    from .mesh_io import ID_ATTR

    obj = bpy.context.object
    info = _review_info()
    if not info or obj is None or obj.type != "MESH" or obj.name not in info.get("objects", []):
        return None
    if obj.mode == "EDIT":
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        layer = bm.verts.layers.int.get(ID_ATTR) or bm.verts.layers.int.new(ID_ATTR)
        previous = _rec.get("snap")
        previous_co = dict(zip(previous[2], previous[3])) if previous and previous[0] == obj.name else {}
        by_id = {}
        for vertex in bm.verts:
            by_id.setdefault(vertex[layer], []).append(vertex)
        next_id = max([_rec.get("next_id", 0), max(by_id, default=-1) + 1, max(previous_co, default=-1) + 1])
        for vid, vertices in by_id.items():
            keep = min(vertices, key=lambda vertex: sum((vertex.co[i] * 1000 - previous_co[vid][i]) ** 2 for i in range(3))) if vid in previous_co else vertices[0]
            for vertex in vertices:
                if vid < 0 or vertex is not keep:
                    vertex[layer] = next_id
                    next_id += 1
        _rec["next_id"] = next_id
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        ids = [v[layer] for v in bm.verts]
        co = [tuple(c * 1000 for c in v.co) for v in bm.verts]
        sel = [i for v, i in zip(bm.verts, ids) if v.select]
    else:
        from .mesh_io import ensure_ids
        previous = _rec.get("snap")
        snapshot = {vid: tuple(value / 1000 for value in co) for vid, co in zip(previous[2], previous[3])} if previous and previous[0] == obj.name else None
        ensure_ids(obj.data, snapshot, _rec.get("next_id", 0))
        attr = obj.data.attributes.get(ID_ATTR)
        ids = [d.value for d in attr.data] if attr else list(range(len(obj.data.vertices)))
        co = [tuple(c * 1000 for c in v.co) for v in obj.data.vertices]
        sel = []
    return obj.name, obj.mode, ids, co, sel


def _moved(before, after):
    """{id: [dw, dd, dh] mm} for the vertices that moved, or None when the
    topology changed (another count or order of ids)."""
    if before is None or before[0] != after[0] or before[2] != after[2]:
        return None
    out = {}
    for vid, a, b in zip(after[2], before[3], after[3]):
        d = [round(y - x, 2) for x, y in zip(a, b)]
        if max(abs(x) for x in d) >= MOVED_MIN:
            out[str(vid)] = d
    return out


def _sculpt_record(moved):
    ts = bpy.context.tool_settings
    brush = ts.sculpt.brush if ts and ts.sculpt else None
    out = {"op": "SCULPT", "moved": moved}
    if brush is not None:
        # Blender 5 keeps the unified size and strength per paint mode; 4.x on tool_settings
        ups = getattr(ts.sculpt, "unified_paint_settings", None) or getattr(ts, "unified_paint_settings", None)
        out["brush"] = brush.name
        out["radius_px"] = ups.size if ups and ups.use_unified_size else brush.size
        out["strength"] = round(ups.strength if ups and ups.use_unified_strength else brush.strength, 3)
    return out


def _record_ops():
    """Blender keeps only its last operators; this copies each new one to
    OPS_LOG as it comes, so the AI reads the whole session, undos included.
    Each operator also carries the ids selected and how far each vertex moved
    since the last record; Sculpt strokes (which Blender does not list) come
    as SCULPT lines: the brush and the vertices it moved."""
    try:
        if _review_info() is None:
            return RECORD
        ops = list(bpy.context.window_manager.operators)
        sigs = [_signature(op) for op in ops]
        start = 0
        if _rec["last"] is not None:
            start = next((i + 1 for i in range(len(sigs) - 1, -1, -1) if sigs[i] == _rec["last"]), 0)
        lines = [_op_record(op) for op in ops[start:]]
        if sigs:
            _rec["last"] = sigs[-1]
        state = _mesh_state()
        if state is not None:
            moved = _moved(_rec.get("snap"), state)
            if lines:
                lines[-1]["object"] = state[0]
                from .regions import groups as region_groups
                lines[-1]["regions"] = region_groups(bpy.data.objects[state[0]], state[2])
                lines[-1]["selected"] = state[4]
                if moved is None and _rec.get("snap") is not None:
                    lines.append({"op": "TOPOLOGY", "object": state[0], "verts": len(state[2])})
                elif moved:
                    lines[-1]["moved"] = moved
                _rec["snap"], _rec["sculpt_pending"] = state, False
            elif state[1] == "SCULPT":
                # a stroke: changes keep coming; it is written once a poll sees none
                now = _moved(_rec.get("tick"), state)
                if now:
                    _rec["sculpt_pending"] = True
                elif _rec.get("sculpt_pending"):
                    total = _moved(_rec.get("snap"), state)
                    if total:
                        stroke = _sculpt_record(total)
                        stroke["object"] = state[0]
                        from .regions import groups as region_groups
                        stroke["regions"] = region_groups(bpy.data.objects[state[0]], state[2])
                        lines.append(stroke)
                    _rec["snap"], _rec["sculpt_pending"] = state, False
            elif _rec.get("snap") is None or _rec["snap"][0] != state[0]:
                _rec["snap"] = state
            elif _rec.get("sculpt_pending"):
                total = _moved(_rec.get("snap"), state)
                if total:
                    stroke = _sculpt_record(total)
                    stroke["object"] = state[0]
                    lines.append(stroke)
                _rec["snap"], _rec["sculpt_pending"] = state, False
            _rec["tick"] = state
        _log(lines)
    except Exception as e:  # recording never breaks the human's Blender
        print(f"LLM Modeling Bridge: operator recorder: {e!r}")
    return RECORD


def _start_recording():
    """From now on: what is in the history already (opening the review) is not the human's."""
    ops = list(bpy.context.window_manager.operators)
    _rec["last"] = _signature(ops[-1]) if ops else None
    _rec["snap"] = _rec["tick"] = None
    _rec["sculpt_pending"] = False
    if not bpy.app.timers.is_registered(_record_ops):
        bpy.app.timers.register(_record_ops, first_interval=RECORD, persistent=True)


@bpy.app.handlers.persistent
def _on_undo_human(*_args):
    if not is_ai() or _state.get("human_editing"):
        _log([{"op": "UNDO"}])
        try:  # the mesh went back (or forward): moves are counted from here
            _rec["snap"] = _rec["tick"] = _mesh_state()
            _rec["sculpt_pending"] = False
        except Exception:
            pass


@bpy.app.handlers.persistent
def _on_redo_human(*_args):
    if not is_ai() or _state.get("human_editing"):
        _log([{"op": "REDO"}])
        try:  # the mesh went back (or forward): moves are counted from here
            _rec["snap"] = _rec["tick"] = _mesh_state()
            _rec["sculpt_pending"] = False
        except Exception:
            pass


@bpy.app.handlers.persistent
def _on_save_post(*_args):
    if is_ai() and not _state.get("human_editing") and bpy.context.window_manager.windows:
        _focus(True)
# --- the human's Blender -------------------------------------------------------

def _poll_human():
    try:
        ai = ai_instance()
        if ai and _mcp_running():
            release_mcp()
            print("LLM Modeling Bridge: an AI instance is running; this Blender's MCP server stopped")
        if _pending_update():
            _set_header("The LLM has a newer version of this review: LLM tab > Load LLM update")
        _answer_collect()
    except Exception as e:  # a poll never breaks the human's Blender
        print(f"LLM Modeling Bridge: poll failed: {e!r}")
    return POLL


def _answer_collect():
    """The AI's collect(): save the review where the human left it and, when
    asked, close this Blender."""
    if _review_info() is None or not bpy.data.filepath:
        return
    request = Path(bpy.data.filepath).with_name(COLLECT)
    try:
        ask = json.loads(request.read_text("utf-8"))
    except (OSError, ValueError):
        return
    request.unlink(missing_ok=True)
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win):
        bpy.ops.wm.save_mainfile()
    print("LLM Modeling Bridge: saved the review for the AI")
    if ask.get("close"):
        bpy.app.timers.register(_quit, first_interval=0.5)


def _quit():
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win):
        bpy.ops.wm.quit_blender()
    return None


def _set_header(text):
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.header_text_set(text)


def _review_info(scene=None):
    if _state.get("human_editing"):
        return {"source": bpy.data.filepath, "objects": [obj.name for obj in bpy.data.objects if obj.type == "MESH"]}
    scene = scene or bpy.context.scene
    raw = scene.get(REVIEW_PROP) if scene else None
    return json.loads(raw) if raw else None


def _pending_update():
    """The AI's update notice for the open review, if newer than the last one loaded."""
    info = _review_info()
    if not info or not bpy.data.filepath:
        return None
    try:
        notice = json.loads(Path(bpy.data.filepath).with_name(UPDATE_NOTICE).read_text("utf-8"))
    except (OSError, ValueError):
        return None
    return notice if notice["written"] > info.get("loaded", info["written"]) else None


def open_review(source, names, out, units=None):
    """In the human's Blender: an empty scene (the human's startup file without
    its objects), the objects appended from the AI's saved file, saved as `out`."""
    bpy.ops.wm.read_homefile(use_empty=True)
    scene = bpy.context.scene
    with bpy.data.libraries.load(str(source), link=False) as (src, dst):
        dst.objects = [n for n in names if n in src.objects]
    for obj in dst.objects:
        scene.collection.objects.link(obj)
        if LOCK_PROP in obj:  # the AI's lock stays in the AI's Blender
            obj.hide_select = bool(obj[LOCK_PROP])
            del obj[LOCK_PROP]
    for prop, value in (units or {}).items():
        setattr(scene.unit_settings, prop, value)
    scene[REVIEW_PROP] = json.dumps({"source": str(source), "objects": list(names), "written": time.time()})
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    # The first save is the AI's version: absorb counts only saves after it.
    Path(out).with_name(OPENED).write_text(json.dumps({"mtime": Path(out).stat().st_mtime, "pid": os.getpid()}),
                                           "utf-8")
    _start_recording()
    from .input_recorder import start_recording
    start_recording()
    return [o.name for o in dst.objects]


class LLM_BRIDGE_OT_load_update(bpy.types.Operator):
    """Replace the reviewed objects with the AI's newer version (save your own edits first: the AI reads what you save)"""

    bl_idname = "llm_modeling_bridge.load_update"
    bl_label = "Load LLM update"

    def execute(self, context):
        notice = _pending_update()
        if notice is None:
            self.report({"WARNING"}, "No update from the LLM")
            return {"CANCELLED"}
        info = _review_info()
        names = replace_from(info["source"], notice["objects"])
        info["loaded"] = notice["written"]
        context.scene[REVIEW_PROP] = json.dumps(info)
        _set_header(None)
        self.report({"INFO"}, f"Loaded the LLM's update: {', '.join(names)}")
        return {"FINISHED"}


class LLM_BRIDGE_PT_review(bpy.types.Panel):
    bl_label = "LLM review"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM"

    @classmethod
    def poll(cls, context):
        return _review_info(context.scene) is not None

    def draw(self, context):
        info = _review_info(context.scene)
        col = self.layout.column()
        if _state.get("human_editing"):
            col.label(text="You are editing the LLM window", icon="INFO")
            col.operator(LLM_BRIDGE_OT_return_to_ai.bl_idname, icon="CHECKMARK")
            return
        col.label(text="A review of the LLM's model", icon="INFO")
        col.label(text=Path(info["source"]).name)
        col.label(text="Done? Tell the LLM: it saves and reads it")
        if _pending_update():
            col.operator(LLM_BRIDGE_OT_load_update.bl_idname, icon="IMPORT")


# --- review and absorb ---------------------------------------------------------

def _review_state_path():
    if not bpy.data.filepath:
        raise InstanceError("Save the .blend first: the review lives next to it")
    from .migration import data_root
    return data_root() / "review.json"


def _load_review_state():
    p = _review_state_path()
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _save_review_state(data):
    p = _review_state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1), "utf-8")


def _default_names():
    return [o.name for o in bpy.context.scene.objects]


_UNITS = ("system", "scale_length", "length_unit", "mass_unit", "time_unit", "temperature_unit")


def review(names=None, launch=True, save=True):
    """Show the human the objects `names` (default: every object in the
    scene). Saves the AI's file; a normal Blender then appends them into an
    empty scene and saves <file>.bridge/review.blend. While that Blender is
    open, a later call only tells it that there is a newer version; the human
    loads it from the LLM tab. launch=False returns the command instead."""
    assert_ai_access()
    names = list(names or _default_names())
    missing = [n for n in names if n not in bpy.data.objects]
    if missing:
        raise InstanceError(f"no objects {missing}")
    state = _load_review_state()
    root = _review_state_path().parent
    path = root / "review.blend"
    if save:
        bpy.ops.wm.save_mainfile()
    if _alive(state.get("pid")) and Path(state.get("review", "")) == path:
        notice = {"source": bpy.data.filepath, "objects": names, "written": time.time()}
        (root / UPDATE_NOTICE).write_text(json.dumps(notice), "utf-8")
        say(f"newer version announced to the human's Blender: {', '.join(names)}")
        return {"review": str(path), "update": True, "pid": state["pid"], "launched": False}
    root.mkdir(parents=True, exist_ok=True)
    units = {k: getattr(bpy.context.scene.unit_settings, k) for k in _UNITS}
    code = (f"import llm_modeling_bridge; llm_modeling_bridge.instance_mod.open_review({bpy.data.filepath!r}, {names!r}, "
            f"{str(path)!r}, {units!r})")
    command = [bpy.app.binary_path, "--python-expr", code]
    from .input_recorder import INPUT_LOG
    for stale in (UPDATE_NOTICE, OPENED, OPS_LOG, COLLECT, INPUT_LOG):
        (root / stale).unlink(missing_ok=True)
    pid = None
    if launch:
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0  # DETACHED_PROCESS | NEW_PROCESS_GROUP
        proc = subprocess.Popen(command, creationflags=flags, close_fds=True,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = proc.pid
        say(f"review opened for the human: {', '.join(names)}")
    state.update(review=str(path), objects=names, pid=pid, written=time.time(), absorbed=None, ops_read=0, inputs_read=0)
    _save_review_state(state)
    return {"review": str(path), "pid": pid, "launched": bool(pid), "command": command}


def replace_from(path, names):
    """Replace mesh, modifiers and transform of the objects `names` of this
    file with those of the same objects in `path`. Returns the names replaced."""
    assert_ai_access()
    before = {kind: set(getattr(bpy.data, kind)) for kind in _KINDS}
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        found = [n for n in names if n in src.objects]
        dst.objects = list(found)  # the loader swaps names for objects in this list
    loaded = dict(zip(found, dst.objects))
    done = []
    for name, new in loaded.items():
        old = bpy.data.objects.get(name)
        if old is None or new is None:
            continue
        if old.type == "MESH":
            old_mesh = old.data
            mesh_name = old_mesh.name
            old.data = new.data
            if old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)
            old.data.name = mesh_name
            _copy_groups(new, old)
        _copy_modifiers(new, old)
        old.matrix_basis = new.matrix_basis
        done.append(name)
    # What the loaded objects referred to (each other, parents, mirror objects)
    # goes to this file's objects of the same name; the loaded copies go away.
    for kind in _KINDS:
        coll = getattr(bpy.data, kind)
        for idb in set(coll) - before[kind]:
            base = idb.name.rsplit(".", 1)[0] if idb.name[-4:-3] == "." and idb.name[-3:].isdigit() else idb.name
            twin = coll.get(base)
            if kind == "meshes" and idb.users > 0:
                continue  # a mesh now in use by one of this file's objects
            if twin is not None and twin is not idb:
                idb.user_remap(twin)
            if kind == "objects" or idb.users == 0:
                coll.remove(idb)
    from .migration import migrate_scene
    migrate_scene()
    return done


def _copy_groups(src, dst):
    definitions = [(group.name, group.lock_weight) for group in src.vertex_groups]
    weights = [(vertex.index, membership.group, membership.weight) for vertex in src.data.vertices for membership in vertex.groups]
    active = src.vertex_groups.active_index
    dst.vertex_groups.clear()
    for name, locked in definitions:
        group = dst.vertex_groups.new(name=name)
        group.lock_weight = locked
    for index, group, weight in weights:
        dst.vertex_groups[group].add([index], weight, "REPLACE")
    if definitions:
        dst.vertex_groups.active_index = active


_KINDS = ("objects", "meshes", "materials", "images", "textures", "node_groups", "collections")


def _take_annotations(path):
    """The human's Annotate strokes in the review become this scene's, so the
    sync names the vertices under them. Marks need nothing: they are the mesh's."""
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.annotations = list(src.annotations)
    loaded = [a for a in dst.annotations if a is not None]
    if not loaded:
        return
    scene = bpy.context.scene
    old = scene.annotation
    scene.annotation = loaded[0]
    for extra in loaded[1:]:
        bpy.data.annotations.remove(extra)
    if old is not None and old is not loaded[0] and old.users == 0:
        name = old.name
        bpy.data.annotations.remove(old)
        loaded[0].name = name


def _copy_modifiers(src, dst):
    dst.modifiers.clear()
    for m in src.modifiers:
        new = dst.modifiers.new(m.name, m.type)
        for p in m.bl_rna.properties:
            if p.is_readonly or p.identifier in ("name", "type"):
                continue
            try:
                setattr(new, p.identifier, getattr(m, p.identifier))
            except (AttributeError, TypeError, ValueError):
                pass


def absorb(names=None, sync=True, verbose=False, why=None, human_dir=None):
    """Read what the human saved in the review back into the AI's objects
    and sync them. Returns per object the sync's action, edits and issues."""
    assert_ai_access()
    state = _load_review_state()
    path = Path(state.get("review", ""))
    if not state or not path.exists():
        raise InstanceError("no review to absorb: call review() first")
    mtime = path.stat().st_mtime
    try:
        opened = json.loads(path.with_name(OPENED).read_text("utf-8"))["mtime"]
    except (OSError, ValueError, KeyError):
        opened = 0
    if mtime <= max(state.get("absorbed") or 0, opened):
        return {"changed": False, "note": "the human has not saved the review since it was written or absorbed"}
    names = list(names or state["objects"])
    bpy.ops.wm.save_mainfile()
    from .catalog import archive_review
    example = archive_review(bpy.data.filepath, path, names, why=why, human_dir=human_dir)
    done = replace_from(path, names)
    _take_annotations(path)
    state["absorbed"] = mtime
    _save_review_state(state)
    out = {"changed": True, "objects": done, **example}
    from .recording import summarize
    operator_records = []
    try:  # what the human ran since the last absorb, from the review's recorder
        lines = path.with_name(OPS_LOG).read_text("utf-8").splitlines()
        records = [json.loads(x) for x in lines[state.get("ops_read", 0):] if x.strip()]
        operator_records = records
        from .recording import summarize
        out["operator_summary"] = summarize(records)
        out["operator_log"] = str(path.with_name(OPS_LOG))
        if verbose:
            out["operators"] = records
        state["ops_read"] = len(lines)
        _save_review_state(state)
    except (OSError, ValueError):
        pass
    from .recording import replay_candidates
    out["replay_candidates"] = replay_candidates(operator_records)
    from .input_recorder import INPUT_LOG
    input_path = path.with_name(INPUT_LOG)
    if input_path.exists():
        from .recording import read_recording, replay_candidates
        records, errors = read_recording(input_path)
        fresh = records[state.get("inputs_read", 0):]
        out["input_summary"] = summarize(fresh)
        out["replay_candidates"] = replay_candidates([*operator_records, *fresh])
        out["input_log"] = str(input_path)
        if errors:
            out["input_errors"] = errors
        if verbose:
            out["inputs"] = fresh
        state["inputs_read"] = len(records)
        _save_review_state(state)
    if sync:
        from .sync import sync as sync_fn
        for name in done:
            if bpy.data.objects[name].type != "MESH":
                continue
            r = sync_fn(name, render=False)
            out[name] = {k: r[k] for k in ("action", "blender_edits", "blender_deltas", "blender_by_loop", "stack_changes", "marks",
                                           "annotations", "changes_by_region", "error") if k in r}
            out[name]["issues"] = [f"{i['level']} {i['code']} {' '.join(i['verts'])}" for i in r["issues"]]
    say(f"absorbed the human's review: {', '.join(done)}")
    bpy.ops.wm.save_mainfile()
    from .reports import finish
    return finish("absorb", out, verbose)


def collect(names=None, close=True, timeout=20.0, verbose=False):
    """After the human edits the review: ask their Blender to save it (and
    close, by default), wait for the save, then absorb() it. The human
    Blender answers on its next poll (every few seconds)."""
    state = _load_review_state()
    path = Path(state.get("review", ""))
    if not state or not path.exists():
        raise InstanceError("no review to collect: call review() first")
    pid = state.get("pid")
    if not _alive(pid):
        out = absorb(names, verbose=verbose)
        out["closed"] = True
        out["note"] = "the human's Blender was already closed; read what it last saved"
        return out
    before = path.stat().st_mtime
    path.with_name(COLLECT).write_text(json.dumps({"close": close, "written": time.time()}), "utf-8")
    end = time.time() + timeout
    while time.time() < end and path.stat().st_mtime == before:
        time.sleep(0.25)
    if path.stat().st_mtime == before:
        path.with_name(COLLECT).unlink(missing_ok=True)
        raise InstanceError(f"the human's Blender did not save the review in {timeout:.0f} s "
                            "(an older LLM Modeling Bridge there? ask the human to save)")
    time.sleep(0.5)  # let the save finish writing
    out = absorb(names, verbose=verbose)
    if close:
        while time.time() < end + 10 and _alive(pid):
            time.sleep(0.25)
        out["closed"] = not _alive(pid)
        if out["closed"]:
            state = _load_review_state()
            state["pid"] = None
            _save_review_state(state)
    return out


# --- registration --------------------------------------------------------------

class LLM_BRIDGE_OT_return_to_ai(bpy.types.Operator):
    bl_idname = "llm_modeling_bridge.return_to_ai"
    bl_label = "Save and return to LLM"

    def execute(self, context):
        try:
            resume_ai()
        except (InstanceError, RuntimeError) as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}


CLASSES = (LLM_BRIDGE_OT_ai_screen, LLM_BRIDGE_OT_load_update, LLM_BRIDGE_OT_return_to_ai, LLM_BRIDGE_PT_review)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    from . import input_recorder
    input_recorder.register()
    if bpy.app.background:
        return
    if is_ai():
        bpy.app.handlers.undo_post.append(_on_undo_human)
        bpy.app.handlers.redo_post.append(_on_redo_human)
        bpy.app.handlers.load_post.append(_on_load)
        bpy.app.handlers.save_pre.append(_on_save_pre)
        bpy.app.handlers.save_post.append(_on_save_post)
        bpy.app.timers.register(_setup_ai, first_interval=0.5, persistent=True)
    else:
        bpy.app.timers.register(_poll_human, first_interval=POLL, persistent=True)
        bpy.app.handlers.undo_post.append(_on_undo_human)
        bpy.app.handlers.redo_post.append(_on_redo_human)


def unregister():
    from . import input_recorder
    input_recorder.unregister()
    for timer in (_setup_ai, _poll_human, _record_ops):
        if bpy.app.timers.is_registered(timer):
            bpy.app.timers.unregister(timer)
    for handlers, fn in ((bpy.app.handlers.load_post, _on_load), (bpy.app.handlers.save_pre, _on_save_pre),
                         (bpy.app.handlers.save_post, _on_save_post),
                         (bpy.app.handlers.undo_post, _on_undo_human),
                         (bpy.app.handlers.redo_post, _on_redo_human)):
        if fn in handlers:
            handlers.remove(fn)
    screen_off()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
