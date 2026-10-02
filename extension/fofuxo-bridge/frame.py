"""The frame: a fixed box that vertex values are measured in, in permille.

w = width (X), d = depth (Y), h = height (Z). On a mirrored axis the value
is the distance from the mirror plane toward the kept side, so it has no
sign: 0 is on the plane and 1000 is the frame edge. On any other axis 0 is
the low edge and 1000 the high edge. Values past 1000 or below 0 are fine
for the frame; below 0 on a mirrored axis means crossing the plane.

The frame only changes through set_frame, never because a vertex moved.
"""

import re
from dataclasses import dataclass

AXES = "XYZ"
NAMES = "wdh"
SCALE = 1000.0
MIN_EXTENT = 1e-3  # m; a flat axis still gets a 1 mm frame


def _mm(value_m):
    s = f"{value_m * 1000:.1f}"
    return "0.0" if s == "-0.0" else s


@dataclass
class AxisFrame:
    axis: str  # "X", "Y" or "Z"
    side: str  # "+" or "-": measured from the mirror plane; "": a range
    start: float  # m: 0 on a mirror plane, else the low edge
    extent: float  # m: the distance that reads as 1000

    def to_value(self, c):
        if self.side == "-":
            return -c / self.extent * SCALE
        if self.side == "+":
            return c / self.extent * SCALE
        return (c - self.start) / self.extent * SCALE

    def to_local(self, value):
        d = value / SCALE * self.extent
        if self.side == "-":
            return -d
        if self.side == "+":
            return d
        return self.start + d

    def text(self):
        name = NAMES[AXES.index(self.axis)]
        if self.side:
            return f"{name} {self.axis}{self.side} {_mm(self.extent)}"
        return f"{name} {self.axis} {_mm(self.start)}..{_mm(self.start + self.extent)}"

    def resized(self, size_m):
        """Same frame with a new full visible size (m)."""
        if self.side:
            return AxisFrame(self.axis, self.side, 0.0, max(size_m / 2, MIN_EXTENT))
        center = self.start + self.extent / 2
        size_m = max(size_m, MIN_EXTENT)
        return AxisFrame(self.axis, "", center - size_m / 2, size_m)


@dataclass
class Frame:
    axes: tuple  # AxisFrame for X, Y, Z

    def to_values(self, co):
        return tuple(a.to_value(c) for a, c in zip(self.axes, co))

    def to_local(self, values):
        return tuple(a.to_local(v) for a, v in zip(self.axes, values))

    def text(self):
        return "   ".join(a.text() for a in self.axes) + "   (mm)"

    def resized(self, w=None, d=None, h=None):
        """Frame with new full sizes in mm; None keeps an axis."""
        sizes = (w, d, h)
        return Frame(tuple(a if s is None else a.resized(s / 1000) for a, s in zip(self.axes, sizes)))

    def to_json(self):
        return [[a.axis, a.side, a.start, a.extent] for a in self.axes]

    @classmethod
    def from_json(cls, data):
        return cls(tuple(AxisFrame(*item) for item in data))

    @classmethod
    def around(cls, coords, sides):
        """Frame that just holds coords (m). sides: kept side per mirrored axis."""
        axes = []
        for k, axis in enumerate(AXES):
            vals = [c[k] for c in coords] or [0.0]
            side = sides.get(axis)
            if side in ("+", "-", "0"):
                extent = max(abs(v) for v in vals)
                axes.append(AxisFrame(axis, "+" if side == "0" else side, 0.0, max(extent, MIN_EXTENT)))
            else:
                lo, hi = min(vals), max(vals)
                axes.append(AxisFrame(axis, "", lo, max(hi - lo, MIN_EXTENT)))
        return cls(tuple(axes))

    @classmethod
    def parse(cls, text):
        """Read the header line written by text(); None if it does not parse."""
        axes = []
        for name, axis in zip(NAMES, AXES):
            m = re.search(rf"\b{name}\s+{axis}([+-])\s+([-\d.]+)", text)
            if m:
                axes.append(AxisFrame(axis, m[1], 0.0, float(m[2]) / 1000))
                continue
            m = re.search(rf"\b{name}\s+{axis}\s+([-\d.]+)\.\.([-\d.]+)", text)
            if not m:
                return None
            lo, hi = float(m[1]) / 1000, float(m[2]) / 1000
            axes.append(AxisFrame(axis, "", lo, max(hi - lo, MIN_EXTENT)))
        return cls(tuple(axes))
