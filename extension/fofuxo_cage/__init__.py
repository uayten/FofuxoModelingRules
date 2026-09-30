"""Fofuxo Cage: text round trip of cage meshes between an AI and a human.

From the Blender MCP:

    import fofuxo_cage
    result = fofuxo_cage.sync("Laço")
    fofuxo_cage.lock("Laço")      # keep the human off while the AI edits
    fofuxo_cage.unlock()
    fofuxo_cage.review(["Laço"])  # show the human, in a Blender of their own
    fofuxo_cage.absorb()          # read back what the human saved there
"""

import sys

import bpy

from . import cage_format, concept, frame, mesh_io, marks, mesh_ops, modifier_info, object_ops, ops, render, rounds, selection, targets as targets_mod, topology, validate
from . import instance as instance_mod
from . import lock as lock_mod
from .concept import find_box, sample
from .editability import editability
from .instance import InstanceError, absorb, instance, is_ai, release_mcp, review, say
from .lock import LockError, lock, unlock
from .parts import PartError, start_part
from .rounds import round_end, round_start
from .mesh_ops import MeshOpError, ensure_looptools, help_text as mesh_help, select
from .shape import ShapeError, capture, compare, deviation, fit, profile, rebuild, sections
from .targets import TargetError, check as check_targets
from .marks import clear_annotations
from .sync import SyncError, annotations, edit, flip, set_frame, sync, views  # sync shadows the submodule name on purpose

ALIAS = "fofuxo_cage"


def register():
    # Short import name for scripts sent through the MCP; the extension itself
    # lives under bl_ext.<repository>.fofuxo_cage.
    sys.modules.setdefault(ALIAS, sys.modules[__name__])
    for cls in lock_mod.CLASSES:
        bpy.utils.register_class(cls)
    instance_mod.register()
    if not bpy.app.background:
        # LoopTools is part of the toolset (mesh op): enable or install it once
        # Blender is up; an extension may not install another while registering.
        bpy.app.timers.register(_looptools_later, first_interval=2.0)


def _looptools_later():
    try:
        print("Fofuxo Cage:", ensure_looptools())
    except Exception as e:  # never break the extension over it; the mesh op retries
        print(f"Fofuxo Cage: LoopTools not ready: {e}")
    return None


def unregister():
    lock_mod.unlock()
    instance_mod.unregister()
    for cls in reversed(lock_mod.CLASSES):
        bpy.utils.unregister_class(cls)
    if sys.modules.get(ALIAS) is sys.modules[__name__] and __name__ != ALIAS:
        del sys.modules[ALIAS]
