"""Compact operator receipts and explicit, provisional replay candidates."""

from collections import Counter
import json
import math
import re
from pathlib import Path


def summarize(records):
    operators = Counter(record.get("op", record.get("event", "UNKNOWN")) for record in records)
    moves = {}
    unattributed = 0
    for record in records:
        moved = record.get("moved") or {}
        regions = record.get("regions") or {}
        if moved and not regions:
            unattributed += len(moved)
        for name, ids in regions.items():
            deltas = [moved[str(vid)] for vid in ids if str(vid) in moved]
            if not deltas:
                continue
            row = moves.setdefault(name, {"samples": 0, "net_mm": [0.0, 0.0, 0.0], "max_mm": 0.0})
            row["samples"] += len(deltas)
            row["net_mm"] = [round(row["net_mm"][i] + sum(delta[i] for delta in deltas), 3) for i in range(3)]
            row["max_mm"] = round(max(row["max_mm"], max(sum(value * value for value in delta) ** 0.5 for delta in deltas)), 3)
    return {"count": len(records), "operators": dict(operators), "undos": operators["UNDO"],
            "redos": operators["REDO"], "moves_by_region": moves, "unattributed_vertex_samples": unattributed,
            "attribution": "poll samples may contain several operators; net_mm is the sum of vertex samples"}


def replay_candidates(records):
    """Never execute: incomplete or nonlinear strokes require human review."""
    candidates = []
    for index, record in enumerate(records):
        if record.get("op") == "SCULPT" and "smooth" in record.get("brush", "").lower():
            moved = record.get("moved") or {}
            strength = record.get("strength")
            if moved and all(re.fullmatch(r"\d+", str(vid)) for vid in moved) and isinstance(strength, (int, float)) and math.isfinite(strength) and 0 <= strength <= 1:
                line = "mesh vertices_smooth " + " ".join(f"v{vid}" for vid in moved) + f" factor={strength:g} repeat=1"
                candidates.append({"record": index, "object": record.get("object"), "op": line, "status": "provisional",
                                   "reason": "one mesh smoothing pass is only an approximation of the recorded Sculpt Smooth stroke; compare before reuse"})
            continue
        if record.get("event") != "DRAG" or len(record.get("points", [])) < 2:
            continue
        start, end = record["points"][0], record["points"][-1]
        brush = start.get("brush", "").lower()
        if start.get("object") != end.get("object") or "grab" not in brush or not start.get("radius_mm"):
            continue
        signs = start.get("axis_signs", {})
        if set(signs) != set("wdh") or any(signs[axis] not in (-1, 1) for axis in "wdh"):
            continue
        if not re.fullmatch(r"v\d+", start.get("vertex", "")):
            continue
        delta = [(b - a) * signs[axis] for axis, a, b in zip("wdh", start["point_mm"], end["point_mm"])]
        if len(delta) != 3 or any(not math.isfinite(value) for value in delta) or not math.isfinite(start["radius_mm"]) or start["radius_mm"] <= 0:
            continue
        line = (f"mesh translate {start['vertex']} " + " ".join(f"{axis}={value:+.3f}mm" for axis, value in zip("wdh", delta))
                + f" falloff=smooth radius={start['radius_mm']:.3f}mm")
        candidates.append({"record": index, "object": start["object"], "op": line, "status": "provisional",
                           "reason": "surface ray points approximate the gesture; compare the recorded moved vertices before reuse"})
    return candidates


def read_recording(path):
    records, errors = [], []
    for index, line in enumerate(Path(path).read_text("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("expected an object")
            records.append(record)
        except ValueError as error:
            errors.append({"line": index, "error": str(error)})
    return records, errors


def recording_summary(path, candidates=False):
    records, errors = read_recording(path)
    result = summarize(records)
    if errors:
        result["parse_errors"] = errors
    if candidates:
        result["replay_candidates"] = replay_candidates(records)
    return result
