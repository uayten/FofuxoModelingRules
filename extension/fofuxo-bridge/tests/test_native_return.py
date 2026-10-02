"""Cancel a real native Object Mode transform in an isolated Windows Blender."""

from contextlib import ExitStack
import importlib
import json
from pathlib import Path
import sys
import tempfile
import time
import traceback
from unittest.mock import patch

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm_modeling_bridge as bridge

instance = importlib.import_module(bridge.__name__ + ".instance")
native_events = importlib.import_module(bridge.__name__ + ".native_events")
root = Path(tempfile.mkdtemp(prefix="llm_bridge_native_return_"))
checks = 0
patches = ExitStack()
deadline = time.monotonic() + 15
report = None
saved_location = None
window = None
native_handle = None


def check(condition, message):
    global checks
    assert condition, message
    checks += 1
    print("ok " + message, flush=True)


def fail():
    traceback.print_exc()
    sys.stdout.flush()
    # A failed interactive test must terminate instead of leaving a stray window.
    import os
    os._exit(1)


def poll():
    try:
        assert time.monotonic() < deadline, "native return did not finish within 15 seconds"
        if report.get("pending"):
            return 0.05
        check(not report.get("error") and report["saved"] and report["access"] == "ai",
              "native modal cancellation completes a saved AI return")
        check(report["cancelled_transforms"] == ["TRANSFORM_OT_translate"],
              "native return identifies the cancelled transform")
        check(not instance._active_transforms() and bpy.context.mode == "OBJECT",
              "native modal handler is gone before Object Mode save")
        check(tuple(bpy.data.objects["Cube"].location) == saved_location,
              "cancellation preserves the completed move and removes the live preview")
        check(not bpy.app.use_event_simulate, "real mouse and keyboard remain enabled")
        example = Path(report["example"])
        check(example.is_dir() and (example / "after.blend").exists(),
              "saved return preserves the immutable after-file")
        records = [json.loads(line) for line in (root / "test.bridge" / "handover.ops.jsonl").read_text().splitlines()]
        check([record["status"] for record in records if record.get("event") == "HANDOVER_RETURN"] ==
              ["requested", "cancelled"], "cancellation has separate request and completion receipts")
        check(sum(record.get("op") == "TRANSFORM_OT_translate" for record in records) == 1,
              "an unconfirmed native transform is not recorded as a completed human move")
        print(f"NATIVE RETURN ALL PASSED ({checks} checks)", flush=True)
        patches.close()
        bpy.ops.wm.quit_blender()
    except Exception:
        fail()
    return None


def return_window():
    global report
    try:
        check(tuple(bpy.data.objects["Cube"].location) != saved_location,
              "a genuine native preview changes the object before return")
        check(bool(instance._active_transforms()), "a native transform is still active at return")
        report = bridge.resume_ai(save=True)
        check(report.get("pending") and not report["saved"] and report["access"] == "human",
              "the initial return report waits for native cancellation")
        bpy.app.timers.register(poll, first_interval=0.05)
    except Exception:
        fail()
    return None


def move_preview():
    try:
        check(bool(instance._active_transforms()), "the native modal handler survives invocation")
        user32 = native_events.ctypes.WinDLL("user32", use_last_error=True)
        user32.PostMessageW.argtypes = [native_events.wintypes.HWND, native_events.wintypes.UINT,
                                       native_events.wintypes.WPARAM, native_events.wintypes.LPARAM]
        user32.PostMessageW.restype = native_events.wintypes.BOOL
        check(bool(user32.PostMessageW(native_handle, 0x0200, 0, (180 << 16) | 220)),
              "preview movement is queued only to the isolated Blender window")
        bpy.app.timers.register(return_window, first_interval=0.2)
    except Exception:
        fail()
    return None


def start():
    global saved_location, window, native_handle
    try:
        bridge.register()
        patches.enter_context(patch.object(instance, "is_ai", return_value=True))
        patches.enter_context(patch.object(instance, "_setup_ai", return_value=None))
        bpy.ops.wm.save_as_mainfile(filepath=str(root / "test.blend"))
        bridge.sync("Cube", render=False)
        bridge.human_access()
        bpy.ops.transform.translate("EXEC_DEFAULT", True, value=(0.1, 0.05, 0.02))
        saved_location = tuple(bpy.data.objects["Cube"].location)
        window = bpy.context.window_manager.windows[0]
        _, receipt = native_events.prepare_transform_cancel(window)
        native_handle = receipt["window_handle"]
        area = next(area for area in window.screen.areas if area.type == "VIEW_3D")
        region = next(region for region in area.regions if region.type == "WINDOW")
        with bpy.context.temp_override(window=window, area=area, region=region):
            check(bpy.ops.transform.translate("INVOKE_DEFAULT", True, value=(0.3, -0.2, 0.1)) == {"RUNNING_MODAL"},
                  "a native transform is invoked in the isolated Object Mode fixture")
        bpy.app.timers.register(move_preview, first_interval=0.2)
    except Exception:
        fail()
    return None


bpy.app.timers.register(start, first_interval=0.5)
