"""Fofuxo Cage: text round trip of cage meshes between an AI and a human.

From the Blender MCP:

    import fofuxo_cage
    result = fofuxo_cage.sync("Laço")
    fofuxo_cage.lock("Laço")      # keep the human off while the AI edits
    fofuxo_cage.unlock()
"""

import sys

import bpy

from . import cage_format, concept, frame, mesh_io, mesh_ops, modifier_info, object_ops, ops, render, topology, validate
from . import lock as lock_mod
from .concept import find_box, sample
from .lock import LockError, lock, unlock
from .shape import ShapeError, capture, compare, deviation, fit, profile, rebuild, sections
from .sync import SyncError, flip, set_frame, sync, views  # sync shadows the submodule name on purpose

ALIAS = "fofuxo_cage"


def register():
    # Short import name for scripts sent through the MCP; the extension itself
    # lives under bl_ext.<repository>.fofuxo_cage.
    sys.modules.setdefault(ALIAS, sys.modules[__name__])
    for cls in lock_mod.CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    lock_mod.unlock()
    for cls in reversed(lock_mod.CLASSES):
        bpy.utils.unregister_class(cls)
    if sys.modules.get(ALIAS) is sys.modules[__name__] and __name__ != ALIAS:
        del sys.modules[ALIAS]
