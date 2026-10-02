"""LLM Modeling Bridge: text round trip of cage meshes between an AI and a human.

From the Blender MCP:

    import llm_modeling_bridge
    result = llm_modeling_bridge.sync("Laço")
    llm_modeling_bridge.lock("Laço")      # keep the human off while the AI edits
    llm_modeling_bridge.unlock()
    llm_modeling_bridge.review(["Laço"])  # show the human, in a Blender of their own
    llm_modeling_bridge.absorb()          # read back what the human saved there
    llm_modeling_bridge.collect()         # after the human's edit: their Blender saves and closes, then absorb
"""

import sys

import bpy

from . import cage_format, concept, frame, labels, mesh_io, marks, mesh_ops, modifier_info, object_ops, ops, render, rounds, selection, targets as targets_mod, topology, validate
from . import instance as instance_mod
from . import lock as lock_mod
from .concept import find_box, sample
from .labels import LabelError, mark_loop, show, show_faces
from .editability import editability
from .instance import InstanceError, absorb, collect, instance, is_ai, release_mcp, review, say, human_access, resume_ai
from .lock import LockError, lock, unlock
from .parts import PartError, start_part
from .rounds import PlanError, read_plan, round_end, round_start, record_read, record_agent_text, round_checkpoint, round_resume
from .mesh_ops import MeshOpError, ensure_looptools, help_text as mesh_help, select
from .shape import ShapeError, capture, compare, deviation, fit, profile, rebuild, sections
from .targets import TargetError, check as check_targets
from .marks import clear_annotations
from .regions import name_region, region_ids
from .positions import set_positions
from .recording import recording_summary
from .workbench import workbench
from .migration import migrate_scene
from .sessions import stage_handoff
from .catalog import catalog_edit, catalog_measures
from .sync import SyncError, annotations, edit, flip, set_frame, sync, views  # sync shadows the submodule name on purpose

ALIAS = "llm_modeling_bridge"


def register():
    from . import migration
    migration.register()
    # Short import name for scripts sent through the MCP; the extension itself
    # lives under bl_ext.<repository>.llm_modeling_bridge.
    sys.modules.setdefault(ALIAS, sys.modules[__name__])
    sys.modules.setdefault("fofuxo_cage", sys.modules[__name__])
    for cls in lock_mod.CLASSES:
        bpy.utils.register_class(cls)
    instance_mod.register()
    if not bpy.app.background:
        # LoopTools is part of the toolset (mesh op): enable or install it once
        # Blender is up; an extension may not install another while registering.
        bpy.app.timers.register(_looptools_later, first_interval=2.0)


def _looptools_later():
    try:
        print("LLM Modeling Bridge:", ensure_looptools())
    except Exception as e:  # never break the extension over it; the mesh op retries
        print(f"LLM Modeling Bridge: LoopTools not ready: {e}")
    return None


def unregister():
    from . import migration
    migration.unregister()
    lock_mod.unlock()
    instance_mod.unregister()
    for cls in reversed(lock_mod.CLASSES):
        bpy.utils.unregister_class(cls)
    if sys.modules.get(ALIAS) is sys.modules[__name__] and __name__ != ALIAS:
        del sys.modules[ALIAS]
