"""Two Blenders: the AI's own instance and the human's review.

The AI works in a Blender of its own, started with `-- --fofuxo-ai`
(launcher.py does it): every editor is painted black with a notice, input
is swallowed, and the MCP server runs there. A human's Blender stops its own
MCP server while an AI instance is alive, so the MCP always reaches the AI's.

    review(names)   save the AI's file, write the objects to
                    <file>.cage/review.blend and open it in a normal Blender;
                    while that review is open, later calls announce a newer
                    version and the human loads it (Fofuxo tab)
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

AI_FLAG = "--fofuxo-ai"
MARKER = Path(tempfile.gettempdir()) / "fofuxo_cage_ai.json"
REVIEW_PROP = "fofuxo_review"
UPDATE_NOTICE = "review.update.json"
OPENED = "review.opened.json"
POLL = 3.0  # s, how often a human's Blender looks for the AI instance and updates
NOTICE = ("Fofuxo Cage: Blender exclusivo da AI",
          "Esta janela é controlada pela AI. Não edite aqui.",
          "Para ver ou editar o modelo, a AI abre outro Blender para você.")
_state = {"handles": [], "review_seen": None, "update_seen": None, "message": ""}


class InstanceError(RuntimeError):
    pass


# --- which Blender is this -----------------------------------------------------

def is_ai():
    return AI_FLAG in sys.argv


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
    try:
        data = json.loads(MARKER.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    return data if _alive(data.get("pid")) else None


def instance():
    """Who this Blender is: {"role": "ai" or "human", "pid", "file", ...}."""
    out = {"role": "ai" if is_ai() else "human", "pid": os.getpid(), "file": bpy.data.filepath,
           "mcp_running": _mcp_running()}
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
            print(f"Fofuxo Cage: MCP server not started: {e}")


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


class FOFUXO_OT_ai_screen(bpy.types.Operator):
    """Swallow every input event in the AI's own Blender"""

    bl_idname = "fofuxo_cage.ai_screen"
    bl_label = "Fofuxo Cage: AI screen"

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
    wm = bpy.context.window_manager
    if not wm.windows:
        return 0.5  # not up yet
    MARKER.write_text(json.dumps({"pid": os.getpid(), "file": bpy.data.filepath, "started": time.time(),
                                  "binary": bpy.app.binary_path}), "utf-8")
    screen_on()
    _focus(True)
    win, area, region = _window_area()
    if not any(op.bl_idname == "FOFUXO_CAGE_OT_ai_screen" for op in win.modal_operators):
        with bpy.context.temp_override(window=win, area=area, region=region):
            bpy.ops.fofuxo_cage.ai_screen("INVOKE_DEFAULT")
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
    if is_ai() and bpy.context.window_manager.windows:
        _focus(False)


@bpy.app.handlers.persistent
def _on_save_post(*_args):
    if is_ai() and bpy.context.window_manager.windows:
        _focus(True)
# --- the human's Blender -------------------------------------------------------

def _poll_human():
    try:
        ai = ai_instance()
        if ai and _mcp_running():
            release_mcp()
            print("Fofuxo Cage: an AI instance is running; this Blender's MCP server stopped")
        if _pending_update():
            _set_header("Fofuxo Cage: the AI has a newer version of this review. Fofuxo tab > Load AI update")
    except Exception as e:  # a poll never breaks the human's Blender
        print(f"Fofuxo Cage: poll failed: {e!r}")
    return POLL


def _set_header(text):
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.header_text_set(text)


def _review_info(scene=None):
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
    return [o.name for o in dst.objects]


class FOFUXO_OT_load_update(bpy.types.Operator):
    """Replace the reviewed objects with the AI's newer version (save your own edits first: the AI reads what you save)"""

    bl_idname = "fofuxo_cage.load_update"
    bl_label = "Load AI update"

    def execute(self, context):
        notice = _pending_update()
        if notice is None:
            self.report({"WARNING"}, "No update from the AI")
            return {"CANCELLED"}
        info = _review_info()
        names = replace_from(info["source"], notice["objects"])
        info["loaded"] = notice["written"]
        context.scene[REVIEW_PROP] = json.dumps(info)
        _set_header(None)
        self.report({"INFO"}, f"Loaded the AI's update: {', '.join(names)}")
        return {"FINISHED"}


class FOFUXO_PT_review(bpy.types.Panel):
    bl_label = "Fofuxo Review"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Fofuxo"

    @classmethod
    def poll(cls, context):
        return _review_info(context.scene) is not None

    def draw(self, context):
        info = _review_info(context.scene)
        col = self.layout.column()
        col.label(text="A review of the AI's model", icon="INFO")
        col.label(text=Path(info["source"]).name)
        col.label(text="Save (Ctrl+S): the AI reads it")
        if _pending_update():
            col.operator(FOFUXO_OT_load_update.bl_idname, icon="IMPORT")


# --- review and absorb ---------------------------------------------------------

def _review_state_path():
    if not bpy.data.filepath:
        raise InstanceError("Save the .blend first: the review lives next to it")
    return Path(bpy.data.filepath).with_suffix(".cage") / "review.json"


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
    empty scene and saves <file>.cage/review.blend. While that Blender is
    open, a later call only tells it that there is a newer version; the human
    loads it from the Fofuxo tab. launch=False returns the command instead."""
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
    code = (f"import fofuxo_cage; fofuxo_cage.instance_mod.open_review({bpy.data.filepath!r}, {names!r}, "
            f"{str(path)!r}, {units!r})")
    command = [bpy.app.binary_path, "--python-expr", code]
    for stale in (UPDATE_NOTICE, OPENED):
        (root / stale).unlink(missing_ok=True)
    pid = None
    if launch:
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0  # DETACHED_PROCESS | NEW_PROCESS_GROUP
        proc = subprocess.Popen(command, creationflags=flags, close_fds=True,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = proc.pid
        say(f"review opened for the human: {', '.join(names)}")
    state.update(review=str(path), objects=names, pid=pid, written=time.time(), absorbed=None)
    _save_review_state(state)
    return {"review": str(path), "pid": pid, "launched": bool(pid), "command": command}


def replace_from(path, names):
    """Replace mesh, modifiers and transform of the objects `names` of this
    file with those of the same objects in `path`. Returns the names replaced."""
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
    return done


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


def absorb(names=None, sync=True):
    """Read what the human saved in the review back into the AI's objects
    and sync them. Returns per object the sync's action, edits and issues."""
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
    done = replace_from(path, names)
    _take_annotations(path)
    state["absorbed"] = mtime
    _save_review_state(state)
    out = {"changed": True, "objects": done}
    if sync:
        from .sync import sync as sync_fn
        for name in done:
            if bpy.data.objects[name].type != "MESH":
                continue
            r = sync_fn(name, render=False)
            out[name] = {k: r[k] for k in ("action", "blender_edits", "blender_deltas", "blender_by_loop", "stack_changes", "marks",
                                           "annotations", "error") if k in r}
            out[name]["issues"] = [f"{i['level']} {i['code']} {' '.join(i['verts'])}" for i in r["issues"]]
    say(f"absorbed the human's review: {', '.join(done)}")
    return out


# --- registration --------------------------------------------------------------

CLASSES = (FOFUXO_OT_ai_screen, FOFUXO_OT_load_update, FOFUXO_PT_review)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    if bpy.app.background:
        return
    if is_ai():
        bpy.app.handlers.load_post.append(_on_load)
        bpy.app.handlers.save_pre.append(_on_save_pre)
        bpy.app.handlers.save_post.append(_on_save_post)
        bpy.app.timers.register(_setup_ai, first_interval=0.5, persistent=True)
    else:
        bpy.app.timers.register(_poll_human, first_interval=POLL, persistent=True)


def unregister():
    for timer in (_setup_ai, _poll_human):
        if bpy.app.timers.is_registered(timer):
            bpy.app.timers.unregister(timer)
    for handlers, fn in ((bpy.app.handlers.load_post, _on_load), (bpy.app.handlers.save_pre, _on_save_pre),
                         (bpy.app.handlers.save_post, _on_save_post)):
        if fn in handlers:
            handlers.remove(fn)
    screen_off()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
