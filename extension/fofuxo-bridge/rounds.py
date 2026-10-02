"""The cost of a round (ROADMAP, Part 2, item 8): time and work per round.

    round_start("B1 round 7", plan="plan.md")  # the plan written before modeling
    ...                                     # syncs, ops, views, measures
    round_end(tokens=180000)                # tokens: from the session's usage

Counts what passes through LLM Modeling Bridge (syncs, ops applied, renders, dense
evaluations for measures) and the minutes between start and end; the tokens
come from the AI's session (the extension cannot see them). Each round is
appended to <file>.bridge/rounds.json, and round_end returns the line for the
run's report.md.

The plan (SKILL, step 5) is a Markdown file with the sections in SECTIONS and
a ```budget block (one "<kind> <number>" per line: syncs, ops, renders,
measures, minutes). round_start refuses a plan that misses a section; every
sync then warns once a count passes its budget, and round_end puts the plan
beside what was done.
"""

import json
import re
import time
import math
from pathlib import Path

import bpy

_round = {"label": None, "start": None, "syncs": 0, "ops": 0, "renders": 0, "measures": 0, "budget": {}}
KINDS = ("syncs", "ops", "renders", "measures", "minutes")
SECTIONS = ("Read", "Parts", "Stack", "Commands", "Checks", "Budget", "Changes")


class PlanError(ValueError):
    pass


def read_plan(path):
    """The plan's budget {kind: number}; PlanError when a section or the budget is missing."""
    path = Path(path)
    if not path.exists():
        raise PlanError(f"no plan at {path}: write it before modeling (SKILL, step 5)")
    text = path.read_text("utf-8").replace("\r\n", "\n")
    heads = {h.strip().lower() for h in re.findall(r"^##\s+(.+)$", text, re.M)}
    missing = [s for s in SECTIONS if s.lower() not in heads]
    if missing:
        raise PlanError(f"the plan misses the section(s) {', '.join(missing)} (## headings)")
    blocks = re.findall(r"```budget\n(.*?)```", text, re.S)
    if not blocks:
        raise PlanError("the plan has no ```budget block (syncs, ops, renders, measures, minutes)")
    budget = {}
    for line in blocks[0].splitlines():
        words = line.split("#")[0].split()
        if not words:
            continue
        if len(words) != 2 or words[0] not in KINDS or not re.fullmatch(r"\d+(\.\d+)?", words[1]):
            raise PlanError(f"budget line {line.strip()!r}: '<kind> <number>' with a kind from {', '.join(KINDS)}")
        budget[words[0]] = float(words[1])
    return budget


def _spent():
    out = {k: _round[k] for k in ("syncs", "ops", "renders", "measures")}
    if _round["start"] is not None:
        out["minutes"] = round((_round.get("elapsed_seconds", 0) + time.time() - _round["start"]) / 60, 1)
    return out


def budget_issues():
    """WARN issues for the counts past the plan's budget (none without a plan)."""
    if _round["start"] is None or not _round["budget"]:
        return []
    spent = _spent()
    over = [f"{k} {spent[k]:g} of {v:g}" for k, v in _round["budget"].items() if spent.get(k, 0) > v]
    if not over:
        return []
    return [{"level": "WARN", "code": "round_budget",
             "msg": f"past the plan's budget ({', '.join(over)}): stop, write in the plan's Changes why, "
                    f"and revise the plan before going on", "verts": []}]


def count(kind, n=1):
    """Called by the sync, the views and the shape tools while a round is open."""
    if _round["start"] is not None:
        _round[kind] += n


def round_start(label, plan=None):
    """Open a round; plan: the path of the plan written before modeling (its budget is read)."""
    budget = read_plan(plan) if plan is not None else {}
    if _round["start"] is not None:
        raise RuntimeError("a round is already open; checkpoint or end it before starting another")
    _round.update(label=label, start=time.time(), syncs=0, ops=0, renders=0, measures=0, budget=budget,
                  plan=str(plan) if plan else None, reports={}, images={}, reads={}, agent_text_chars=0, elapsed_seconds=0)
    return {"round": label, "started": time.strftime("%Y-%m-%d %H:%M"), "budget": budget}


def round_end(tokens=None, note=None):
    if _round["start"] is None:
        raise RuntimeError("no round open: call round_start(label) first")
    entry = {"round": _round["label"], "date": time.strftime("%Y-%m-%d"),
             "minutes": _spent()["minutes"],
             **{k: _round[k] for k in ("syncs", "ops", "renders", "measures")}, "tokens": tokens, "note": note,
             "budget": dict(_round["budget"]),
             "cost_by_kind": {"reports": _round.get("reports", {}), "images": _round.get("images", {}),
                              "external_reads": _round.get("reads", {}),
                              "agent_text_chars": _round.get("agent_text_chars", 0)},
             "token_source": "session_usage" if tokens is not None else "unavailable"}
    tok = f", {tokens / 1000:.0f}k tokens" if tokens is not None else ", tokens not given"
    entry["report_line"] = (f"Cost: {entry['minutes']} min, {entry['syncs']} syncs, {entry['ops']} ops, "
                            f"{entry['renders']} renders, {entry['measures']} measures{tok}.")
    if entry["budget"]:
        parts = [f"{k} {entry[k]:g}/{v:g}{' over' if entry[k] > v else ''}" for k, v in entry["budget"].items()]
        entry["report_line"] += f" Plan: {', '.join(parts)}."
    if bpy.data.filepath:
        from .migration import data_root
        path = data_root() / "rounds.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = json.loads(path.read_text("utf-8")) if path.exists() else []
        rows.append(entry)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(rows, indent=1, ensure_ascii=False), "utf-8")
        temporary.replace(path)
    _round["start"] = None
    return entry


def round_checkpoint():
    """Persist a round for a new process, excluding the idle time until resume."""
    from .migration import data_root
    if _round["start"] is None:
        raise RuntimeError("no round open")
    path = data_root() / "round.open.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    state = dict(_round)
    state["checkpoint_version"] = 1
    state["blend"] = bpy.data.filepath
    state["elapsed_seconds"] = state.get("elapsed_seconds", 0) + time.time() - state["start"]
    state["start"] = None
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=1), "utf-8")
    temporary.replace(path)
    _round.update(state)
    return {"checkpoint": str(path), "round": state["label"]}


def round_resume(path=None):
    from .migration import data_root
    if _round["start"] is not None:
        raise RuntimeError("a round is already open")
    source = Path(path) if path else data_root() / "round.open.json"
    state = json.loads(source.read_text("utf-8"))
    if state.get("checkpoint_version") != 1 or not state.get("label") or any(kind not in state for kind in KINDS if kind != "minutes"):
        raise ValueError("invalid round checkpoint")
    if Path(state.get("blend", "")).resolve() != Path(bpy.data.filepath).resolve():
        raise ValueError("the checkpoint belongs to another .blend file")
    state["start"] = time.time()
    _round.update(state)
    source.unlink()
    return {"round": state["label"], "resumed": True, "budget": state["budget"]}


def record_report(kind, full, returned=None):
    """Count serialized characters, never claim these are billed tokens."""
    if _round["start"] is None:
        return
    row = _round["reports"].setdefault(kind, {"count": 0, "full_chars": 0, "returned_chars": 0})
    row["count"] += 1
    row["full_chars"] += len(json.dumps(full, ensure_ascii=False, default=str))
    row["returned_chars"] += len(json.dumps(full if returned is None else returned, ensure_ascii=False, default=str))


def record_image(width, height, kind="render"):
    if _round["start"] is None:
        return
    row = _round["images"].setdefault(kind, {"count": 0, "pixels": 0})
    row["count"] += 1
    row["pixels"] += int(width) * int(height)


def record_read(path, kind="file", characters=None, width=None, height=None):
    """Explicit receipts for reads outside the extension; image billing is unknown."""
    if _round["start"] is None:
        raise RuntimeError("no round open")
    if kind not in ("file", "image"):
        raise ValueError("kind must be file or image")
    if kind == "file":
        if characters is None:
            raise ValueError("provide the characters actually read, not the whole file size")
        amount = float(characters)
    else:
        if width is None or height is None:
            raise ValueError("provide image width and height")
        amount = float(width) * float(height)
    if not math.isfinite(amount) or amount < 0:
        raise ValueError("read size must be finite and nonnegative")
    row = _round["reads"].setdefault(kind, {"count": 0, "characters" if kind == "file" else "pixels": 0})
    row["count"] += 1
    row["characters" if kind == "file" else "pixels"] += int(amount)
    return {"recorded": str(path), "kind": kind, "image_tokens": "unavailable" if kind == "image" else None}


def record_agent_text(text):
    if _round["start"] is None:
        raise RuntimeError("no round open")
    _round["agent_text_chars"] += len(text)
    return {"characters": len(text)}
