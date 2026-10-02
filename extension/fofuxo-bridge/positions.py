"""Batch absolute frame coordinates through the checked edit pipeline."""

import math
import bpy


def set_positions(name, positions, render=False, verbose=False):
    from .sync import sync, edit
    from .mesh_io import ensure_ids
    from .instance import assert_ai_access
    assert_ai_access()
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH" or obj.mode != "OBJECT":
        raise ValueError("set_positions requires a mesh in Object Mode")
    known = set(ensure_ids(obj.data)[0])
    lines = []
    for key, value in positions.items():
        vid = int(str(key).removeprefix("v"))
        if vid not in known or len(value) != 3 or any(not math.isfinite(float(v)) for v in value):
            raise ValueError(f"invalid frame position for v{vid}")
        lines.extend(f"position v{vid} {axis} {float(number):.12f}" for axis, number in zip("wdh", value))
    before = sync(name, render=False)
    if before["action"] in ("error", "conflict") or not lines:
        return before
    return edit(name, *lines, render=render, verbose=verbose)
