"""Small handoffs and tool requests that keep modeling context out of tool development."""

from pathlib import Path

import bpy


def stage_handoff(stage, state, next_step, read_first, decisions=(), avoid=(), tool_need=None, path=None):
    from .migration import data_root
    from .rounds import _round, round_checkpoint
    from .instance import assert_ai_access
    assert_ai_access()
    if not bpy.data.filepath:
        raise ValueError("save the .blend before writing a handoff")
    target = Path(path) if path else data_root() / "NEXT.md"
    checkpoint = round_checkpoint() if _round["start"] is not None else None
    text = f"# {stage}\n\n{state}\n\n## Contents\n\n- [Resume](#resume)\n- [Read first](#read-first)\n- [Decisions](#decisions)\n- [Avoid](#avoid)\n"
    text += f"\n## Resume\n\nOpen `{bpy.data.filepath}`. Next: {next_step}\n"
    if checkpoint:
        text += f"\nRound checkpoint: `{checkpoint['checkpoint']}`. Call `round_resume()` once before continuing.\n"
    text += "\n## Read first\n\n" + "\n".join(f"- {item}" for item in read_first) + "\n"
    text += "\n## Decisions\n\n" + "\n".join(f"- {item}" for item in decisions) + "\n"
    text += "\n## Avoid\n\n" + "\n".join(f"- {item}" for item in avoid) + "\n"
    if tool_need:
        text += f"\n## Tool request\n\n{tool_need}\n\nDevelop and test the tool in its own session. Return with the API, validation result and next modeling call; do not reconstruct this stage from the conversation.\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, "utf-8")
    return {"handoff": str(target), "checkpoint": checkpoint}
