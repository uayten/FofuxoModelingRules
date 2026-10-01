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
For a part mirrored across another object (a horn across the body), the
world measures read one side, Mirror off, in mm with w d h = world x y z
(front is -y): `world min|max|size w|d|h` (its box), `base w|d|h` (the middle
of its open border, where it sits; closed, the middle of what is buried in
the Mirror's object or the parent) and `tip w|d|h` (its point farthest from
the base).
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
_VALUE = re.compile(r"(-?\d*\.?\d+)(mm)?")
_MAX_UP = 6  # folders walked up from the .blend
_WORDS = {"faces": 1, "verts": 1, "evaluated": 2, "size": 2, "profile": 3, "section": 4,
          "world": 3, "base": 2, "tip": 2}


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
        span = abs(self.value) * self.amount / 100 if self.unit == "%" else self.amount
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


def _one_side(obj):
    """World points (m) of one side of obj (Mirror modifiers off), and the
    middle of its open border (None when closed)."""
    from . import shape

    mirrors = [m for m in obj.modifiers if m.type == "MIRROR" and m.show_viewport]
    try:
        for m in mirrors:
            m.show_viewport = False
        with shape._levels(obj, shape.DENSE_LEVELS):
            ev = obj.evaluated_get(shape._depsgraph())
            me = ev.to_mesh()
            try:
                co = np.empty(len(me.vertices) * 3)
                me.vertices.foreach_get("co", co)
                edge_of_loop = np.empty(len(me.loops), dtype=int)
                me.loops.foreach_get("edge_index", edge_of_loop)
                verts_of_edge = np.empty(len(me.edges) * 2, dtype=int)
                me.edges.foreach_get("vertices", verts_of_edge)
            finally:
                ev.to_mesh_clear()
    finally:
        for m in mirrors:
            m.show_viewport = True
        shape._depsgraph()
    co = co.reshape(-1, 3)
    mw = np.array(obj.matrix_world)
    co = co @ mw[:3, :3].T + mw[:3, 3]
    border = np.nonzero(np.bincount(edge_of_loop, minlength=len(verts_of_edge) // 2) == 1)[0]
    ends = np.unique(verts_of_edge.reshape(-1, 2)[border])
    if len(ends):
        return co, co[ends].mean(axis=0)
    # Closed: the middle of the part buried in the object it sits on.
    host = next((m.mirror_object for m in mirrors if m.mirror_object), None) or obj.parent
    inside = _inside(host, co) if host is not None and host.type == "MESH" else None
    return co, (co[inside].mean(axis=0) if inside is not None and inside.any() else None)


def _inside(host, co):
    """Which world points lie inside the evaluated mesh of host."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    from . import shape

    tree = BVHTree.FromObject(host, shape._depsgraph())
    inv = host.matrix_world.inverted()
    out = np.zeros(len(co), dtype=bool)
    for i, p in enumerate(co):
        local = inv @ Vector(p)
        hit, normal, _, _ = tree.find_nearest(local)
        out[i] = hit is not None and (hit - local).dot(normal) > 0
    return out


def _measure(obj, measure, cache):
    from . import shape

    words = measure.split()
    if measure in COUNTS:
        return _count(obj, measure)
    if words[0] in ("world", "base", "tip") and words[-1] in ("w", "d", "h"):
        if "side" not in cache:
            cache["side"] = _one_side(obj)
        co, base = cache["side"]
        k = "wdh".index(words[-1])
        if words[0] == "world" and len(words) == 3 and words[1] in ("min", "max", "size"):
            v = {"min": co[:, k].min(), "max": co[:, k].max(), "size": np.ptp(co[:, k])}[words[1]]
            return round(float(v) * 1000, 1)
        if len(words) == 2:
            if base is None:
                return None
            if words[0] == "base":
                return round(float(base[k]) * 1000, 1)
            tip = co[np.argmax(np.linalg.norm(co - base, axis=1))]
            return round(float(tip[k]) * 1000, 1)
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
        unit = "mm" if t.measure.startswith(("size", "profile", "world", "base", "tip")) else ""
        shown = "none" if value is None else f"{value:g}{unit}"
        results.append(f"{'in ' if ok else 'OUT'} {t.obj} {t.measure} = {shown} (target {t.text()})"
                       + (f"  {t.why}" if t.why else ""))
    return {"target": str(path), "in": n_in, "out": len(results) - n_in, "results": results}
