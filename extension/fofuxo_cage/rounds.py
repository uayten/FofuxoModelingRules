"""The cost of a round (ROADMAP, Part 2, item 8): time and work per round.

    round_start("B1 round 7", plan="plan.md")  # the plan written before modeling
    ...                                     # syncs, ops, views, measures
    round_end(tokens=180000)                # tokens: from the session's usage

Counts what passes through Fofuxo Cage (syncs, ops applied, renders, dense
evaluations for measures) and the minutes between start and end; the tokens
come from the AI's session (the extension cannot see them). Each round is
appended to <file>.cage/rounds.json, and round_end returns the line for the
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
        out["minutes"] = round((time.time() - _round["start"]) / 60, 1)
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
    _round.update(label=label, start=time.time(), syncs=0, ops=0, renders=0, measures=0, budget=budget,
                  plan=str(plan) if plan else None)
    return {"round": label, "started": time.strftime("%Y-%m-%d %H:%M"), "budget": budget}


def round_end(tokens=None, note=None):
    if _round["start"] is None:
        raise RuntimeError("no round open: call round_start(label) first")
    entry = {"round": _round["label"], "date": time.strftime("%Y-%m-%d"),
             "minutes": round((time.time() - _round["start"]) / 60, 1),
             **{k: _round[k] for k in ("syncs", "ops", "renders", "measures")}, "tokens": tokens, "note": note,
             "budget": dict(_round["budget"])}
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
    if entry["budget"]:
        parts = [f"{k} {entry[k]:g}/{v:g}{' over' if entry[k] > v else ''}" for k, v in entry["budget"].items()]
        entry["report_line"] += f" Plan: {', '.join(parts)}."
    return entry
