"""Modifier settings as text: what the cage file shows and what `set` reads.

Each modifier gets a line with its effect (vertices, faces and size of the
result up to that modifier) and a line of settings: the ones that matter for
its type plus every other one that differs from Blender's default. Setting
names are Blender's property identifiers, so they can go straight into
`set <modifier> <property> <value>`.

Units: lengths in mm (0.1mm), angles in degrees (30deg), booleans on/off,
axis flags as letters (XZ, or - for none).
"""

import math
import re

import bpy

KEY = {
    "MIRROR": ("use_axis", "use_bisect_axis", "use_clip", "use_mirror_merge", "merge_threshold", "mirror_object"),
    "SUBSURF": ("levels", "render_levels", "quality", "use_limit_surface", "boundary_smooth", "use_creases"),
    "SOLIDIFY": ("solidify_mode", "thickness", "offset", "use_even_offset", "use_rim", "use_flip_normals"),
    "BEVEL": ("affect", "offset_type", "width", "segments", "limit_method", "angle_limit", "harden_normals"),
    "WEIGHTED_NORMAL": ("mode", "weight", "keep_sharp", "use_face_influence"),
    "DISPLACE": ("direction", "strength", "mid_level"),
}
SKIP = {"rna_type", "name", "type", "persistent_uid", "execution_time", "use_pin_to_last", "debug_options"}
LENGTH = {"DISTANCE", "LENGTH"}
_UNITS = {"mm": 0.001, "cm": 0.01, "m": 1.0}
_AXES = "XYZ"
WIDTH = 96  # settings wrap past this many characters


class ModifierValueError(ValueError):
    pass


def _is_axis_flags(prop):
    return prop.type == "BOOLEAN" and getattr(prop, "is_array", False) and prop.array_length == 3


def _default(prop):
    if getattr(prop, "is_array", False) and prop.array_length > 0:
        return list(prop.default_array)
    if prop.type == "ENUM":
        return set(prop.default_flag) if prop.is_enum_flag else prop.default
    if prop.type in ("POINTER", "STRING"):
        return None if prop.type == "POINTER" else prop.default
    return prop.default


def _current(mod, prop):
    v = getattr(mod, prop.identifier)
    if getattr(prop, "is_array", False) and prop.array_length > 0:
        return list(v)
    if prop.type == "ENUM" and prop.is_enum_flag:
        return set(v)
    return v


def _same(a, b):
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) <= 1e-9 * max(1.0, abs(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def _num(v):
    return f"{v:.4g}"


def format_value(prop, v):
    if _is_axis_flags(prop):
        return "".join(a for a, on in zip(_AXES, v) if on) or "-"
    if isinstance(v, list):
        return ",".join(format_value_scalar(prop, x) for x in v)
    return format_value_scalar(prop, v)


def format_value_scalar(prop, v):
    if prop.type == "BOOLEAN":
        return "on" if v else "off"
    if prop.type == "POINTER":
        return f'"{v.name}"' if v is not None and " " in v.name else (v.name if v is not None else "-")
    if prop.type == "ENUM":
        return ",".join(sorted(v)) or "-" if isinstance(v, set) else str(v)
    if prop.type == "FLOAT":
        if prop.subtype in LENGTH:
            return f"{_num(v * 1000)}mm"
        if prop.subtype == "ANGLE":
            return f"{_num(math.degrees(v))}deg"
        return _num(v)
    if prop.type == "STRING":
        return f'"{v}"'
    return str(v)


def settings(mod):
    """[(identifier, text)]: the type's key settings, then any other non-default one."""
    props = mod.bl_rna.properties
    keys = [k for k in KEY.get(mod.type, ()) if k in props]
    out = [(k, format_value(props[k], _current(mod, props[k]))) for k in keys]
    for prop in props:
        ident = prop.identifier
        if ident in SKIP or ident in keys or ident.startswith(("show_", "is_")) or prop.is_readonly:
            continue
        if prop.type == "COLLECTION":
            continue
        cur = _current(mod, prop)
        if prop.type == "POINTER":
            if cur is None or not isinstance(cur, bpy.types.ID):
                continue
        elif _same(cur, _default(prop)):
            continue
        out.append((ident, format_value(prop, cur)))
    return out


def parse_value(prop, raw):
    """A text value for prop, in Blender units. Raises ModifierValueError with a hint."""
    ident = prop.identifier
    if _is_axis_flags(prop):
        letters = raw.upper()
        if letters != "-" and not re.fullmatch(r"[XYZ]{1,3}", letters):
            raise ModifierValueError(f"{ident} takes axis letters like XZ, or - for none, not {raw!r}")
        return [a in letters for a in _AXES]
    if getattr(prop, "is_array", False) and prop.array_length > 0:
        parts = raw.split(",")
        if len(parts) != prop.array_length:
            raise ModifierValueError(f"{ident} takes {prop.array_length} comma-separated values, not {raw!r}")
        return [_scalar(prop, p.strip()) for p in parts]
    return _scalar(prop, raw)


def _scalar(prop, raw):
    ident, kind = prop.identifier, prop.type
    if kind == "BOOLEAN":
        low = raw.lower()
        if low in ("true", "on", "1", "yes"):
            return True
        if low in ("false", "off", "0", "no"):
            return False
        raise ModifierValueError(f"{ident} takes on or off, not {raw!r}")
    if kind == "FLOAT" and prop.subtype in LENGTH:
        m = re.fullmatch(r"([-+]?[\d.]+(?:e-?\d+)?)\s*(mm|cm|m)", raw.lower())
        if not m:
            raise ModifierValueError(f"{ident} is a length: write it with a unit, e.g. 0.1mm, not {raw!r}")
        return float(m[1]) * _UNITS[m[2]]
    if kind == "FLOAT" and prop.subtype == "ANGLE":
        m = re.fullmatch(r"([-+]?[\d.]+)\s*(deg|rad)", raw.lower())
        if not m:
            raise ModifierValueError(f"{ident} is an angle: write it with a unit, e.g. 30deg, not {raw!r}")
        return math.radians(float(m[1])) if m[2] == "deg" else float(m[1])
    try:
        if kind == "INT":
            return int(raw)
        if kind == "FLOAT":
            return float(raw)
    except ValueError:
        raise ModifierValueError(f"{ident} takes a number, not {raw!r}") from None
    if kind == "ENUM":
        items = [i.identifier for i in prop.enum_items]
        chosen = raw.split(",") if prop.is_enum_flag else [raw]
        bad = [c for c in chosen if c not in items]
        if bad:
            raise ModifierValueError(f"{ident} takes one of {items}, not {raw!r}")
        return set(chosen) if prop.is_enum_flag else raw
    if kind == "STRING":
        return raw
    if kind == "POINTER" and prop.fixed_type.identifier == "Object":
        if raw == "-":
            return None
        obj = bpy.data.objects.get(raw)
        if obj is None:
            raise ModifierValueError(f"{ident} takes an object name or -, and there is no object {raw!r}")
        return obj
    raise ModifierValueError(f"{ident} cannot be set from text")


def describe(obj, depsgraph_fn, size_fn):
    """Lines for the modifiers section: per modifier its effect, then its settings.

    The effect is measured by evaluating the stack up to each modifier (later
    ones are switched off for the measure and restored right after).
    depsgraph_fn() returns an updated depsgraph; size_fn(coords) a size text.
    """
    mods = list(obj.modifiers)
    effects = {}
    shown = [m.show_viewport for m in mods]
    try:
        for i, mod in enumerate(mods):
            if not shown[i]:
                continue
            for j, other in enumerate(mods):
                other.show_viewport = shown[j] and j <= i
            ev = obj.evaluated_get(depsgraph_fn())
            me = ev.to_mesh()
            try:
                co = [tuple(v.co) for v in me.vertices]
                effects[mod.name] = f"v {len(co)}  f {len(me.polygons)}  size {size_fn(co)} mm"
            finally:
                ev.to_mesh_clear()
    finally:
        for m, s in zip(mods, shown):
            if m.show_viewport != s:
                m.show_viewport = s
        depsgraph_fn()
    lines = []
    for mod in mods:
        name = f'"{mod.name}"' if " " in mod.name else mod.name
        effect = f"  -> {effects[mod.name]}" if mod.name in effects else "  (off in the viewport)"
        lines.append(f"{name} ({mod.type}){effect}")
        row = "   "
        for k, v in settings(mod):
            item = f" {k} {v} "
            if len(row) + len(item) > WIDTH and row.strip():
                lines.append(row.rstrip())
                row = "   "
            row += item
        if row.strip():
            lines.append(row.rstrip())
    return lines
