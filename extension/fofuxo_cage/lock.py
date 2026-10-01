"""Keep the human's hands off what the AI is editing.

    lock("Laço")            take control: leave Edit Mode (the human's edits
                            are kept), make the object unselectable and
                            swallow every mouse and key event in Blender
    lock("Laço", ui=False)  only the object lock
    unlock()                release everything

A locked object keeps its original selectability in a custom property, so a
file saved while locked can still be unlocked after reopening. The human can
always take over: Esc while the UI is blocked, or the Unlock button in the
3D View sidebar (Fofuxo tab). The next sync then reports that the human took
over, and the AI should stop and ask.
"""

import bpy

PROP = "fofuxo_cage_lock"
_state = {"ui": False, "taken_over": False, "message": ""}


class LockError(RuntimeError):
    pass


def _locked_objects():
    return [o for o in bpy.data.objects if PROP in o]


def _set_header(text):
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.header_text_set(text)
        win.workspace.status_text_set(text)


def _leave_edit_mode():
    """Back to Object Mode, which writes the Edit Mode changes into the mesh.
    Returns the name of the object that was being edited, or None."""
    obj = bpy.context.view_layer.objects.active
    if obj is None or obj.mode == "OBJECT":
        return None
    wm = bpy.context.window_manager
    if wm.windows:
        win = wm.windows[0]
        area = next((a for a in win.screen.areas if a.type == "VIEW_3D"), win.screen.areas[0])
        with bpy.context.temp_override(window=win, area=area, active_object=obj, object=obj):
            bpy.ops.object.mode_set(mode="OBJECT")
    else:
        bpy.ops.object.mode_set(mode="OBJECT")
    return obj.name


def lock(name, ui=True):
    """Take control of object `name`: leave Edit Mode (keeping the human's
    edits: the next sync reads them as Blender edits), make the object
    unselectable and, with ui (the default), swallow all input."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise LockError(f"no object named {name!r}")
    left = _leave_edit_mode()
    if PROP not in obj:
        obj[PROP] = int(obj.hide_select)
    obj.select_set(False)
    obj.hide_select = True
    _state["taken_over"] = False
    names = ", ".join(o.name for o in _locked_objects())
    _state["message"] = f"The LLM is editing {names}"
    if ui and not _state["ui"] and bpy.context.window_manager.windows:  # no windows in background
        _start_block()
    _set_header(_state["message"] + ("   (Esc to take over)" if _state["ui"] else ""))
    report = status()
    if left:
        report["left_edit_mode"] = left
    return report


def unlock(name=None):
    """Release one object (or all, with name None) and the UI block."""
    for obj in _locked_objects():
        if name is None or obj.name == name:
            obj.hide_select = bool(obj[PROP])
            del obj[PROP]
    if not _locked_objects():
        _state["ui"] = False  # the modal operator sees this and ends
        _set_header(None)
    return status()


def status():
    return {"locked": [o.name for o in _locked_objects()], "ui_blocked": _state["ui"],
            "taken_over": _state["taken_over"]}


def took_over():
    """True once after the human released a lock the AI had set."""
    hit = _state["taken_over"]
    _state["taken_over"] = False
    return hit


def _start_block():
    wm = bpy.context.window_manager
    win = wm.windows[0]
    area = next((a for a in win.screen.areas if a.type == "VIEW_3D"), win.screen.areas[0])
    region = next((r for r in area.regions if r.type == "WINDOW"), area.regions[0])
    _state["ui"] = True
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.fofuxo_cage.block_input("INVOKE_DEFAULT")


def _human_takes_over():
    for obj in _locked_objects():
        obj.hide_select = bool(obj[PROP])
        del obj[PROP]
    _state["ui"] = False
    _state["taken_over"] = True
    _set_header(None)


class FOFUXO_OT_block_input(bpy.types.Operator):
    """Swallow input while the AI edits; Esc hands control back to the human"""

    bl_idname = "fofuxo_cage.block_input"
    bl_label = "LLM editing: block input"

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(0.25, window=context.window)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not _state["ui"]:
            return self._finish(context)
        if event.type == "ESC" and event.value == "PRESS":
            _human_takes_over()
            return self._finish(context)
        return {"RUNNING_MODAL"}  # every other event is eaten

    def _finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        return {"FINISHED"}


class FOFUXO_OT_unlock(bpy.types.Operator):
    """Take the objects back from the AI"""

    bl_idname = "fofuxo_cage.unlock"
    bl_label = "Unlock"

    def execute(self, context):
        _human_takes_over()
        return {"FINISHED"}


class FOFUXO_PT_lock(bpy.types.Panel):
    bl_label = "LLM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM"

    def draw(self, context):
        locked = _locked_objects()
        col = self.layout.column()
        if not locked:
            col.label(text="Nothing locked")
            return
        col.label(text="The LLM is editing:", icon="LOCKED")
        for obj in locked:
            col.label(text=obj.name)
        col.operator(FOFUXO_OT_unlock.bl_idname, icon="UNLOCKED")


CLASSES = (FOFUXO_OT_block_input, FOFUXO_OT_unlock, FOFUXO_PT_lock)
