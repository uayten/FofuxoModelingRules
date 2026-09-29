"""Fofuxo Cage: text round trip of cage meshes between an AI and a human.

From the Blender MCP:

    import fofuxo_cage
    result = fofuxo_cage.sync("Laço")
"""

import sys

from . import cage_format, concept, frame, mesh_io, object_ops, ops, render, topology, validate
from .concept import find_box, sample
from .sync import SyncError, set_frame, sync, views  # sync shadows the submodule name on purpose

ALIAS = "fofuxo_cage"


def register():
    # Short import name for scripts sent through the MCP; the extension itself
    # lives under bl_ext.<repository>.fofuxo_cage.
    sys.modules.setdefault(ALIAS, sys.modules[__name__])


def unregister():
    if sys.modules.get(ALIAS) is sys.modules[__name__] and __name__ != ALIAS:
        del sys.modules[ALIAS]
