"""Exercise Blender's restricted add-on activation and deferred migration lifecycle."""

from pathlib import Path
import sys
import traceback

import addon_utils
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
errors = []


def activation_error():
    errors.append(traceback.format_exc())


module = addon_utils.enable("llm_modeling_bridge", default_set=False, handle_error=activation_error)
assert module is not None and not errors, "activation failed: " + "\n".join(errors)
assert module.__addon_enabled__, "Blender did not enable the add-on"
migration = sys.modules["llm_modeling_bridge.migration"]
assert migration.on_load in bpy.app.handlers.load_post, "file migration handler missing"
assert bpy.app.timers.is_registered(migration.on_load), "initial migration was not deferred"

mesh = bpy.data.objects["Cube"].data
attribute = mesh.attributes.new("fofuxo_cage_id", "INT", "POINT")
attribute.data.foreach_set("value", list(range(len(mesh.vertices))))
migration.on_load()
assert mesh.attributes.get("llm_modeling_bridge_id") is not None, "deferred migration did not run"

addon_utils.disable("llm_modeling_bridge", default_set=False, handle_error=activation_error)
assert not errors, "deactivation failed: " + "\n".join(errors)
assert migration.on_load not in bpy.app.handlers.load_post, "migration handler left behind"
assert not bpy.app.timers.is_registered(migration.on_load), "migration timer left behind"
print("REGISTRATION ALL PASSED (8 checks)", flush=True)
