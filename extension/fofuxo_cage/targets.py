"""Numeric targets of a task: a `targets` block in the task's target.md.

    ```targets
    # object  measure                  target   tolerance  why
    Laço      faces                    19       +20%       the modeler's cage (poly budget, D-046)
    Laço      size w                   124.4mm  6%         the concept's width (D-038, D-056)
    Laço      section w 0.15 waist     0.32     0.05       the pinch into the knot (D-039)
    Laço      section w 0.85 n         3.8      0.3        a boxy outer lobe
    Laço      profile top 0.75         14.5mm   1mm        half depth of the lobe from the top
    ```

Measures: `faces`, `verts` (the base cage), `evaluated faces`, `size w|d|h`
(the full result, mm), `section <axis> <fraction> n|waist` (a cut across the
axis at a fraction of the part's half size from its mirror plane: the
superellipse exponent, or depth at h 0 over the largest depth),
`profile top|front|side <fraction>` (the largest half size in that band, mm).
Tolerance: `5%` or `0.05` or `1mm` both ways; `+20%` only above, `-10%`
only below. Names with spaces go in quotes ("Laço Nó").

target.md is found by walking up from the .blend's folder. The sync checks
the counts on every run (the poly budget); targets() measures everything.
"""

import re
from pathlib import Path

import bpy
import numpy as np

COUNTS = ("faces", "verts")
_TOL = re.compile(r"([+-]?)(\d*\.?\d+)(%|mm)?")
_VALUE = re.compile(r"(\d*\.?\d+)(mm)?")
_MAX_UP = 6  # folders walked up from the .blend
_WORDS = {"faces": 1, "verts": 1, "evaluated": 2, "size": 2, "profile": 3, "section": 4}


class TargetError(ValueError):
    pass


class Target:
    def __init__(self, obj, measure, value, tol, why, line):
        self.obj, self.measure, self.value, self.why, self.line = obj, measure, value, why, line
        m = _TOL.fullmatch(tol)
        if not m:
            raise TargetError(f"{line!r}: tolerance like 5%, 0.05, 1mm, +20% or -10%, not {tol!r}")
        self.side, self.amount, self.unit = m[1], float(m[2]), m[3] or ""

    def limits(self):
        span = self.value * self.amount / 100 if self.unit == "%" else self.amount
        lo = self.value - span if self.side in ("", "-") else float("-inf")
        hi = self.value + span if self.side in ("", "+") else float("inf")
        return lo, hi

    def text(self):
        sign = self.side or "±"
        return f"{self.value:g} {sign}{self.amount:g}{self.unit}"


def find(start=None):
    """target.md next to the .blend or in a folder above it, or None."""
    here = Path(start or bpy.data.filepath or ".").resolve()
    for folder in [here.parent, *here.parents][:_MAX_UP]:
        path = folder / "target.md"
        if path.exists():
            return path
    return None


def parse(path):
    """The targets in the file's ```targets block(s)."""
    text = Path(path).read_text("utf-8")
    out = []
    for block in re.findall(r"```targets\n(.*?)```", text.replace("\r\n", "\n"), re.S):
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Only the object name may be quoted; the why is free text (apostrophes and all).
            m = re.match(r'"([^"]+)"\s+(.*)', line)
            tokens = [m[1], *m[2].split()] if m else line.split()
            # Each kind of measure has a fixed number of words (a section's fraction is one of them).
            words = _WORDS.get(tokens[1]) if len(tokens) > 1 else None
            k = 1 + words if words else None
            if k is None or k + 1 >= len(tokens) or not _VALUE.fullmatch(tokens[k]):
                raise TargetError(f"{line!r}: expected '<object> <measure> <target> <tolerance> [why]' with a "
                                  f"measure from {', '.join(_WORDS)}")
            value = float(_VALUE.fullmatch(tokens[k])[1])
            out.append(Target(tokens[0], " ".join(tokens[1:k]), value, tokens[k + 1], " ".join(tokens[k + 2:]), line))
    return out


def _count(obj, measure):
    if measure == "faces":
        return len(obj.data.polygons)
    if measure == "verts":
        return len(obj.data.vertices)
    return None


def budget_issues(obj, path=None):
    """The sync's poly budget: counts over their target, as WARN issues."""
    from .validate import _issue

    path = path or find()
    if path is None:
        return []
    try:
        targets = [t for t in parse(path) if t.obj == obj.name and t.measure in COUNTS]
    except (TargetError, OSError, ValueError):
        return []
    issues = []
    for t in targets:
        n = _count(obj, t.measure)
        lo, hi = t.limits()
        if n > hi or n < lo:
            where = "over" if n > hi else "under"
            issues.append(_issue("WARN", "poly_budget", f"{n} {t.measure}, {where} the target {t.text()} "
                                                        f"({t.why or Path(path).name})"))
    return issues


def _measure(obj, measure, cache):
    from . import shape

    words = measure.split()
    if measure in COUNTS:
        return _count(obj, measure)
    if "co" not in cache:
        cache["co"], _ = shape.dense(obj)
    co = cache["co"]
    if measure == "evaluated faces":
        dg = bpy.context.evaluated_depsgraph_get()
        return len(obj.evaluated_get(dg).data.polygons)
    if words[0] == "size" and len(words) == 2 and words[1] in "wdh":
        k = "wdh".index(words[1])
        return round(float(np.ptp(co[:, k])) * 1000, 1)
    if words[0] == "profile" and len(words) == 3 and words[1] in shape.VIEWS:
        f = float(words[2])
        rows = shape.profile(None, words[1], co=co)["rows"]
        return min(rows, key=lambda r: abs(r[0] - f))[1] if rows else None
    if words[0] == "section" and len(words) == 4 and words[1] in "wdh" and words[3] in ("n", "waist"):
        k = "wdh".index(words[1])
        half = float(np.abs(co[:, k]).max())
        frame = shape._frame(obj)
        at = float(words[2]) * half / frame.axes[k].extent * 1000
        s = shape.sections(obj.name, words[1], [at], render=False)["sections"][0]
        if words[3] == "n":
            return s.get("n")
        waist = s.get("waist")
        return waist.get("ratio") if isinstance(waist, dict) else None
    raise TargetError(f"unknown measure {measure!r}")


def check(names=None, path=None):
    """Measure every target of the task (or of the objects `names`).
    Returns {"target": path, "in": n, "out": n, "results": [lines]}."""
    path = Path(path) if path else find()
    if path is None:
        raise TargetError("no target.md next to the .blend or above it")
    targets = parse(path)
    if names is not None:
        names = [names] if isinstance(names, str) else list(names)
        targets = [t for t in targets if t.obj in names]
    results, n_in, caches = [], 0, {}
    for t in targets:
        obj = bpy.data.objects.get(t.obj)
        if obj is None or obj.type != "MESH":
            results.append(f"{t.obj} {t.measure}: no such mesh object")
            continue
        value = _measure(obj, t.measure, caches.setdefault(t.obj, {}))
        lo, hi = t.limits()
        ok = value is not None and lo <= value <= hi
        n_in += ok
        unit = "mm" if t.measure.startswith(("size", "profile")) else ""
        shown = "none" if value is None else f"{value:g}{unit}"
        results.append(f"{'in ' if ok else 'OUT'} {t.obj} {t.measure} = {shown} (target {t.text()})"
                       + (f"  {t.why}" if t.why else ""))
    return {"target": str(path), "in": n_in, "out": len(results) - n_in, "results": results}
