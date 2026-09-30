"""Parse and write the cage text format. Pure Python: no bpy here."""

import re
from dataclasses import dataclass, field

FORMAT_VERSION = 1
SECTIONS = ("modifiers", "verts", "faces", "edges", "ops", "forms")

HELP = (
    "# Values are permille of the frame: w = width (X), d = depth (Y), h = height (Z).",
    "# A mirrored axis counts from the mirror plane (0) to the frame edge (1000).",
    "# Edit \"base w d h\", then run sync. sub = where the vertex lands after the",
    "# modifier stack (read-only). frame, modifiers, faces and edges are written by",
    "# the plugin; change a modifier with a set op (set Mirror merge_threshold 0.1mm).",
)

_NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"
_VERT_RE = re.compile(
    rf"^(?:(?P<label>\S+)\s+)?v(?P<id>\d+)\s+(?P<x>{_NUM})\s+(?P<y>{_NUM})\s+(?P<z>{_NUM})"
    rf"(?:\s*\|\s*(?:(?P<sx>{_NUM})\s+(?P<sy>{_NUM})\s+(?P<sz>{_NUM})|-))?"
    rf"(?:\s*\|(?P<flags>.*))?$"
)
_FACE_RE = re.compile(r"^f\d+\s+((?:v\d+\s*)+)$")


class CageFormatError(ValueError):
    pass


@dataclass
class Vertex:
    id: int
    base: tuple  # permille of the frame (w, d, h)
    sub: tuple = None  # same, after the modifier stack; read-only
    flags: tuple = ()


@dataclass
class Cage:
    header: dict = field(default_factory=dict)  # key -> raw value, in file order
    groups: list = field(default_factory=list)  # [(label, [ids])]
    verts: dict = field(default_factory=dict)  # id -> Vertex
    faces: list = field(default_factory=list)  # [tuple of ids]
    modifiers: list = field(default_factory=list)  # raw lines, read-only
    edges: list = field(default_factory=list)  # raw lines, read-only
    ops: list = field(default_factory=list)  # raw lines
    forms: list = field(default_factory=list)  # raw lines, kept verbatim


def _strip_comment(line):
    """Drop a comment: '#' at the start or after whitespace."""
    m = re.search(r"(^|\s)#", line)
    return line[: m.start()] if m else line


def normalize_face(face):
    """Rotate a face so it starts at its lowest id, keeping the winding."""
    k = face.index(min(face))
    return tuple(face[k:] + face[:k])


def parse(text):
    cage = Cage()
    section = None
    group = None
    for n, raw in enumerate(text.splitlines(), 1):
        if section == "forms":
            if raw.strip() in SECTIONS:
                section = raw.strip()
                continue
            cage.forms.append(raw.rstrip())
            continue
        line = _strip_comment(raw).strip()
        if not line:
            continue
        if line in SECTIONS:
            section = line
            continue
        if section is None:
            key, _, value = line.partition(" ")
            cage.header[key] = value.strip()
        elif section == "verts":
            m = _VERT_RE.match(line)
            if not m:
                raise CageFormatError(f"line {n}: not a vertex line: {raw.strip()!r}")
            vid = int(m["id"])
            if vid in cage.verts:
                raise CageFormatError(f"line {n}: v{vid} appears twice")
            sub = (float(m["sx"]), float(m["sy"]), float(m["sz"])) if m["sx"] else None
            flags = tuple((m["flags"] or "").split())
            cage.verts[vid] = Vertex(vid, (float(m["x"]), float(m["y"]), float(m["z"])), sub, flags)
            if m["label"] or group is None:
                group = (m["label"] or "", [])
                cage.groups.append(group)
            group[1].append(vid)
        elif section == "faces":
            m = _FACE_RE.match(line)
            if not m:
                raise CageFormatError(f"line {n}: not a face line: {raw.strip()!r}")
            cage.faces.append(tuple(int(t[1:]) for t in m[1].split()))
        elif section == "edges":
            cage.edges.append(line)
        elif section == "modifiers":
            cage.modifiers.append(line)
        elif section == "ops":
            cage.ops.append(line)
    while cage.forms and not cage.forms[-1].strip():
        cage.forms.pop()
    while cage.forms and not cage.forms[0].strip():
        cage.forms.pop(0)
    return cage


def fmt(value):
    """A length in mm, one decimal."""
    s = f"{value:.1f}"
    return "0.0" if s == "-0.0" else s


def fmt_value(value):
    """A frame value: whole permille."""
    return str(round(value) + 0)


def _whd(values):
    if values is None:
        return f"{'-':>6}" + " " * 12
    return "".join(f" {fmt_value(c):>5}" for c in values)  # a space always: wide values never run together


def write(cage):
    out = [f"# fofuxo_cage {FORMAT_VERSION}", *HELP, ""]
    for key, value in cage.header.items():
        out.append(f"{key:<8} {value}")
    if cage.modifiers:
        out += ["", "modifiers"] + [f"  {line}" for line in cage.modifiers]
    out += ["", "verts", f"# {'loop':<6}{'id':<5}{'base w':>6}{'d':>6}{'h':>6} |{'sub w':>6}{'d':>6}{'h':>6} | flags"]
    for label, ids in cage.groups:
        for k, vid in enumerate(ids):
            v = cage.verts[vid]
            lab = label if k == 0 else ""
            line = f"{lab:<8}{'v' + str(vid):<5}{_whd(v.base)} |{_whd(v.sub)} | {' '.join(v.flags)}"
            out.append(line.rstrip())
    out += ["", "faces"]
    out += [f"  f{i:<3} " + " ".join(f"v{vid}" for vid in face) for i, face in enumerate(cage.faces)]
    out += ["", "edges"] + [f"  {line}" for line in cage.edges]
    out += ["", "ops"] + [f"  {line}" for line in cage.ops]
    out += ["", "forms"] + list(cage.forms)
    return "\n".join(out) + "\n"
