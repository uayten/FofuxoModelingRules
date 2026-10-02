"""Targeted native cancellation without global input injection or focus changes."""

import ctypes
from ctypes import wintypes
import os

import bpy


def prepare_transform_cancel(window):
    """Resolve and validate the recipient before installing a return guard."""
    if os.name != "nt":
        raise RuntimeError("active transform return currently requires Windows; cancel it manually")
    windows = bpy.context.window_manager.windows
    if len(windows) != 1 or window.as_pointer() != windows[0].as_pointer():
        raise RuntimeError("native cancellation requires exactly one Blender window")
    if bpy.app.use_event_simulate:
        raise RuntimeError("event simulation disables human input; restart Blender without that option")
    keymap = bpy.context.window_manager.keyconfigs.user.keymaps.get("Transform Modal Map")
    if keymap is None or not any(item.active and item.propvalue == "CANCEL" and item.type == "RIGHTMOUSE"
                                 and item.value in {"PRESS", "ANY"} and
                                 (item.any or all(modifier in {-1, 0} for modifier in
                                                  (item.shift, item.ctrl, item.alt, item.oskey))) and
                                 item.key_modifier == "NONE" for item in keymap.keymap_items):
        raise RuntimeError("the native transform keymap must map unmodified right-button press to Cancel")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumThreadWindows.argtypes = [wintypes.DWORD, callback_type, wintypes.LPARAM]
    user32.EnumThreadWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    handles = []

    @callback_type
    def visit(handle, _parameter):
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle, ctypes.byref(process_id))
        class_name = ctypes.create_unicode_buffer(128)
        user32.GetClassNameW(handle, class_name, len(class_name))
        if process_id.value == os.getpid() and class_name.value == "GHOST_WindowClass":
            handles.append(handle)
        return True

    if not user32.EnumThreadWindows(kernel32.GetCurrentThreadId(), visit, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    if len(handles) != 1:
        raise RuntimeError("could not uniquely identify this process's native Blender window")
    handle = handles[0]

    def dispatch():
        process_id = wintypes.DWORD()
        if not user32.GetWindowThreadProcessId(handle, ctypes.byref(process_id)) or process_id.value != os.getpid():
            raise RuntimeError("native window identity changed before cancellation")
        # Blender consumes these mouse messages; its keyboard messages use raw input.
        if not user32.PostMessageW(handle, 0x0204, 0x0002, 0):  # WM_RBUTTONDOWN, MK_RBUTTON
            raise ctypes.WinError(ctypes.get_last_error())
        if not user32.PostMessageW(handle, 0x0205, 0, 0):  # WM_RBUTTONUP
            raise ctypes.WinError(ctypes.get_last_error())

    return dispatch, {"transport": "win32_window_messages", "pid": os.getpid(), "window_handle": handle,
                      "button": "RIGHTMOUSE", "policy": "cancel_unconfirmed_transform"}
