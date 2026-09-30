"""The cost of a round (ROADMAP, Part 2, item 8): time and work per round.

    round_start("B1 round 7")
    ...                                     # syncs, ops, views, measures
    round_end(tokens=180000)                # tokens: from the session's usage

Counts what passes through Fofuxo Cage (syncs, ops applied, renders, dense
evaluations for measures) and the minutes between start and end; the tokens
come from the AI's session (the extension cannot see them). Each round is
appended to <file>.cage/rounds.json, and round_end returns the line for the
run's report.md.
"""

import json
import time
from pathlib import Path

import bpy

_round = {"label": None, "start": None, "syncs": 0, "ops": 0, "renders": 0, "measures": 0}


def count(kind, n=1):
    """Called by the sync, the views and the shape tools while a round is open."""
    if _round["start"] is not None:
        _round[kind] += n


def round_start(label):
    _round.update(label=label, start=time.time(), syncs=0, ops=0, renders=0, measures=0)
    return {"round": label, "started": time.strftime("%Y-%m-%d %H:%M")}


def round_end(tokens=None, note=None):
    if _round["start"] is None:
        raise RuntimeError("no round open: call round_start(label) first")
    entry = {"round": _round["label"], "date": time.strftime("%Y-%m-%d"),
             "minutes": round((time.time() - _round["start"]) / 60, 1),
             **{k: _round[k] for k in ("syncs", "ops", "renders", "measures")}, "tokens": tokens, "note": note}
    _round["start"] = None
    if bpy.data.filepath:
        path = Path(bpy.data.filepath).with_suffix(".cage") / "rounds.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = json.loads(path.read_text("utf-8")) if path.exists() else []
        rows.append(entry)
        path.write_text(json.dumps(rows, indent=1, ensure_ascii=False), "utf-8")
    tok = f", {tokens / 1000:.0f}k tokens" if tokens else ", tokens not given"
    entry["report_line"] = (f"Cost: {entry['minutes']} min, {entry['syncs']} syncs, {entry['ops']} ops, "
                            f"{entry['renders']} renders, {entry['measures']} measures{tok}.")
    return entry
