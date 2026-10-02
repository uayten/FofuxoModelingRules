"""Failure-path checks for asynchronous ownership return, without native input."""

from contextlib import nullcontext
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm_modeling_bridge as bridge

instance = importlib.import_module(bridge.__name__ + ".instance")
native_events = importlib.import_module(bridge.__name__ + ".native_events")
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1
    print("ok " + message, flush=True)


def main():
    prior = instance._state.copy()
    region = SimpleNamespace(type="WINDOW")
    window = SimpleNamespace(screen=SimpleNamespace(areas=[SimpleNamespace(type="VIEW_3D", regions=[region])]))
    active = [(window, ["TRANSFORM_OT_translate"])]
    dispatcher = Mock()
    finish = Mock(return_value={"access": "ai", "saved": True})
    fake_bpy = SimpleNamespace(data=SimpleNamespace(filepath="test.blend"),
                              context=SimpleNamespace(temp_override=lambda **kwargs: nullcontext()),
                              app=SimpleNamespace(timers=SimpleNamespace(register=Mock())),
                              ops=SimpleNamespace(llm_modeling_bridge=SimpleNamespace(return_guard=Mock())))
    try:
        instance._state["human_editing"] = True
        with patch.object(instance, "bpy", fake_bpy), \
                patch.object(instance, "_active_transforms", side_effect=lambda: active), \
                patch.object(instance, "_finish_return", finish), patch.object(instance, "_log"), \
                patch.object(native_events, "prepare_transform_cancel", return_value=(dispatcher, {})) as prepare:
            report = instance.resume_ai()
            check(report["pending"] and not report["saved"] and not finish.called,
                  "pending cancellation cannot claim a completed save")
            check(instance.resume_ai() is report and dispatcher.call_count == 1,
                  "repeated requests do not inject duplicate cancellation events")
            check(instance._poll_return() == 0.05 and instance._state["human_editing"] and not finish.called,
                  "native cancellation must complete before ownership or saving changes")
            try:
                instance.assert_ai_access()
                raise AssertionError("pending return allowed an extension edit")
            except instance.InstanceError:
                check(True, "extension edits refuse throughout a pending return")
            guard = instance.LLM_BRIDGE_OT_return_guard
            check(guard.modal(None, None, SimpleNamespace(type="LEFTMOUSE")) == {"RUNNING_MODAL"} and
                  guard.modal(None, None, SimpleNamespace(type="MOUSEMOVE")) == {"RUNNING_MODAL"} and
                  guard.modal(None, None, SimpleNamespace(type="RIGHTMOUSE")) == {"PASS_THROUGH"},
                  "return guard blocks further edits but passes cancellation")
            instance._state["return_pending"]["deadline"] = 0
            instance._poll_return()
            check(report["error"] and not report["pending"] and not report["saved"] and not finish.called and
                  instance._state["human_editing"], "timeout releases the guard without saving or claiming AI access")
            report = instance.resume_ai()
            active.clear()
            finish.side_effect = RuntimeError("save failed")
            instance._poll_return()
            check(report["error"] == "save failed" and not report["pending"] and not report["saved"] and
                  instance._state["human_editing"], "save failure retains human ownership and reports the error")
            active.append((window, ["TRANSFORM_OT_translate"]))
            prepare.side_effect = RuntimeError("recipient could not be identified")
            count = dispatcher.call_count
            try:
                instance.resume_ai()
                raise AssertionError("invalid recipient was accepted")
            except RuntimeError:
                check(dispatcher.call_count == count and not instance._state.get("return_pending") and
                      instance._state["human_editing"], "recipient validation fails before injecting input or installing a guard")
    finally:
        instance._state.clear()
        instance._state.update(prior)
    print(f"MODAL RETURN ALL PASSED ({checks} checks)", flush=True)


main()
