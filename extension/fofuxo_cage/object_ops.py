"""Ops that change the object instead of vertex positions.

    add <type> [as <name>] [at <place>]   add a modifier (default name, at the end)
    remove <modifier>                     remove a modifier
    reorder <modifier> to <place>         move a modifier in the stack
    set <modifier> <property> <value>     change a setting, e.g. set Subdivision levels 2,
                                          set Mirror merge_threshold 0.1mm, set Mirror use_axis XZ
    apply <modifier>                      apply a modifier to the mesh (destructive)
    crease <selection> <value>            e.g. crease plane-x 1.0, crease v2-v16 0.5
    bevel_weight <selection> <value>      the edges' bevel weight, for a Bevel limited by weight
    dissolve <selection>                  remove an edge loop (see mesh_ops)
    cut <vA-vB> [N]                       cut N loops across the ring of edge vA-vB
    mesh <operator> <selection> [k=v ...] run a Blender mesh operator (see mesh_ops)
    join <object>                         join another mesh object into this one (it goes away)

Values: lengths with a unit (0.1mm, 2cm), angles with a unit (30deg), on/off,
axis flags as letters (XZ, - for none), an object name or - for none.
type: a Blender modifier type, e.g. SUBSURF, MIRROR, BEVEL, SOLIDIFY,
WEIGHTED_NORMAL (case does not matter). place: first, last, a 1-based
position, before <modifier> or after <modifier>. Names with spaces go in
quotes. Selections: the grammar of selection.py (vN, vA-vB, loop labels,
plane-x/y/z, sharp, seam, crease, loop vA-vB, ring vA-vB, path vA vB,
faces ..., all).

The whole batch is checked against a simulated stack before anything runs,
and its mesh ops run first on a temporary copy, so a bad op changes nothing.
"""

import shlex

import bpy

from . import mesh_ops, modifier_info, selection

VERBS = ("add", "remove", "reorder", "set", "apply", "crease", "bevel_weight", "dissolve", "cut", "mesh", "join")
# Names Blender gives new modifiers (checked on 5.2), so a batch can refer to
# a modifier it adds and new modifiers keep their default names (D-006).
DEFAULT_NAMES = {
    "SUBSURF": "Subdivision", "WEIGHTED_NORMAL": "WeightedNormal", "SIMPLE_DEFORM": "SimpleDeform",
    "EDGE_SPLIT": "EdgeSplit", "CORRECTIVE_SMOOTH": "CorrectiveSmooth", "LAPLACIANSMOOTH": "LaplacianSmooth",
    "NODES": "GeometryNodes",
}


class ObjectOpError(ValueError):
    pass


def verb(line):
    tokens = line.split()
    return tokens[0].lower() if tokens else ""


def _types():
    return {i.identifier for i in bpy.types.Modifier.bl_rna.properties["type"].enum_items}


def _default_name(kind):
    return DEFAULT_NAMES.get(kind, kind.replace("_", " ").title().replace(" ", ""))


def _struct(kind):
    """RNA struct of a modifier type, for checking settings before it exists."""
    camel = "".join(part.title() for part in kind.split("_"))
    return getattr(bpy.types, f"{camel}Modifier", None)


def _unique(name, names):
    if name not in names:
        return name
    k = 1
    while f"{name}.{k:03d}" in names:
        k += 1
    return f"{name}.{k:03d}"


def _place(tokens, names, line, moving=None):
    """Index in the stack for first / last / N / before X / after X."""
    others = [n for n in names if n != moving]
    if not tokens or tokens == ["last"]:
        return len(others)
    if tokens == ["first"]:
        return 0
    if len(tokens) == 1 and tokens[0].isdigit():
        return min(max(int(tokens[0]) - 1, 0), len(others))
    if len(tokens) == 2 and tokens[0] in ("before", "after"):
        if tokens[1] not in others:
            raise ObjectOpError(f"{line!r}: no modifier {tokens[1]!r} to place it {tokens[0]}")
        k = others.index(tokens[1])
        return k if tokens[0] == "before" else k + 1
    raise ObjectOpError(f"{line!r}: place must be first, last, a position, before <name> or after <name>")


def _value(prop, raw):
    try:
        return modifier_info.parse_value(prop, raw)
    except modifier_info.ModifierValueError as e:
        raise ObjectOpError(str(e)) from None


def _context(obj):
    return bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj],
                                     selected_editable_objects=[obj])


def _run(op, **kwargs):
    if "FINISHED" not in op(**kwargs):
        raise ObjectOpError(f"Blender refused {op.idname_py()} {kwargs}")


def check_all(obj, lines, cage, frame=None, next_id=0):
    """Check a batch against a simulated stack; returns [(line, run)].

    Each run() applies its op and returns a short result for the report.
    frame: for lengths in % of the frame; next_id: the first fresh vertex id.
    """
    counter = {"next_id": next_id}
    runners = []
    applied = False
    names = [m.name for m in obj.modifiers]
    kinds = {m.name: m.type for m in obj.modifiers}
    types = _types()
    out = []
    for line in lines:
        try:
            tokens = shlex.split(line)
        except ValueError as e:
            raise ObjectOpError(f"{line!r}: {e}") from None
        v, args = tokens[0].lower(), tokens[1:]

        def need(name):
            if name not in names:
                raise ObjectOpError(f"{line!r}: no modifier {name!r}; the stack would be {names}")

        if v == "add":
            if not args:
                raise ObjectOpError(f"{line!r}: expected 'add <type> [as <name>] [at <place>]'")
            kind = args[0].upper()
            if kind not in types:
                raise ObjectOpError(f"{line!r}: unknown modifier type {args[0]!r}")
            rest = args[1:]
            name = None
            if rest[:1] == ["as"]:
                if len(rest) < 2:
                    raise ObjectOpError(f"{line!r}: 'as' needs a name")
                name, rest = rest[1], rest[2:]
            if rest[:1] == ["at"]:
                rest = rest[1:]
            elif rest:
                raise ObjectOpError(f"{line!r}: expected 'at <place>' after the type and name")
            index = _place(rest, names, line)
            final = _unique(name or _default_name(kind), names)
            names.insert(index, final)
            kinds[final] = kind
            out.append((line, _adder(obj, kind, name, rest)))
        elif v == "remove":
            if len(args) != 1:
                raise ObjectOpError(f"{line!r}: expected 'remove <modifier>'")
            need(args[0])
            names.remove(args[0])
            out.append((line, _remover(obj, args[0])))
        elif v == "reorder":
            if len(args) < 3 or args[1] != "to":
                raise ObjectOpError(f"{line!r}: expected 'reorder <modifier> to <place>'")
            need(args[0])
            index = _place(args[2:], names, line, moving=args[0])
            names.remove(args[0])
            names.insert(index, args[0])
            out.append((line, _reorderer(obj, args[0], args[2:])))
        elif v == "set":
            if len(args) != 3:
                raise ObjectOpError(f"{line!r}: expected 'set <modifier> <property> <value>'")
            name, prop_name, raw = args
            need(name)
            mod = obj.modifiers.get(name)
            rna = mod.bl_rna if mod is not None and mod.type == kinds[name] else getattr(_struct(kinds[name]), "bl_rna", None)
            value = raw
            if rna is not None:
                prop = rna.properties.get(prop_name)
                if prop is None or prop.is_readonly:
                    raise ObjectOpError(f"{line!r}: {name} has no settable property {prop_name!r}")
                value = _value(prop, raw)
            out.append((line, _setter(obj, name, prop_name, value)))
        elif v == "apply":
            if len(args) != 1:
                raise ObjectOpError(f"{line!r}: expected 'apply <modifier>'")
            need(args[0])
            names.remove(args[0])
            out.append((line, _applier(obj, args[0])))
        elif v in ("crease", "bevel_weight"):
            if len(args) < 2:
                raise ObjectOpError(f"{line!r}: expected '{v} <edges> <value>'")
            try:
                value = float(args[-1])
            except ValueError:
                raise ObjectOpError(f"{line!r}: the {v} value must be a number from 0 to 1") from None
            if not 0.0 <= value <= 1.0:
                raise ObjectOpError(f"{line!r}: the {v} value must be from 0 to 1")
            try:
                terms = selection.parse(args[:-1], cage)
                selection.check(obj.data, [t for t in terms if t[0] != "mark"])
            except selection.SelectionError as e:
                raise ObjectOpError(f"{line!r}: {e}") from None
            out.append((line, lambda terms=terms, value=value, v=v: f"{_set_crease(obj, terms, value, v)} edges"))
        elif v == "join":
            if len(args) != 1:
                raise ObjectOpError(f"{line!r}: expected 'join <object>'")
            other = bpy.data.objects.get(args[0])
            if other is None or other.type != "MESH" or other is obj:
                raise ObjectOpError(f"{line!r}: no other mesh object named {args[0]!r}")
            out.append((line, _joiner(obj, args[0])))
        elif v in ("mesh", "dissolve", "cut"):
            try:
                runner = mesh_ops.check_line(obj, v, args, line, cage, frame, counter)
            except mesh_ops.MeshOpError as e:
                raise ObjectOpError(f"{line!r}: {e}") from None
            if not applied:  # the copy cannot follow an apply earlier in the batch
                runners.append(runner)
            out.append((line, _mesh_runner(runner)))
        else:
            raise ObjectOpError(f"{line!r}: unknown op")
        applied = applied or v == "apply"
    if runners:
        try:
            mesh_ops.precheck(obj, runners)
        except mesh_ops.MeshOpError as e:
            raise ObjectOpError(str(e)) from None
    return out


def _joiner(obj, name):
    def run():
        other = bpy.data.objects.get(name)
        if other is None:
            raise ObjectOpError(f"no object {name!r}")
        before = len(obj.data.vertices)
        with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj, other],
                                       selected_editable_objects=[obj, other]):
            _run(bpy.ops.object.join)
        return f"joined {name}: {before} -> {len(obj.data.vertices)} vertices"
    return run


def _mesh_runner(runner):
    def run():
        try:
            return runner()
        except (mesh_ops.MeshOpError, RuntimeError) as e:
            raise ObjectOpError(str(e)) from None
    return run


def _adder(obj, kind, name, place):
    def run():
        with _context(obj):
            _run(bpy.ops.object.modifier_add, type=kind)
            mod = obj.modifiers[-1]
            if name:
                mod.name = name
            index = _place(place, [m.name for m in obj.modifiers], "add", moving=mod.name)
            if index != len(obj.modifiers) - 1:
                _run(bpy.ops.object.modifier_move_to_index, modifier=mod.name, index=index)
        return f"added {mod.name} at {index + 1}"
    return run


def _remover(obj, name):
    def run():
        obj.modifiers.remove(obj.modifiers[name])
        return "removed"
    return run


def _reorderer(obj, name, place):
    def run():
        index = _place(place, [m.name for m in obj.modifiers], "reorder", moving=name)
        with _context(obj):
            _run(bpy.ops.object.modifier_move_to_index, modifier=name, index=index)
        return f"now at {index + 1}"
    return run


def _setter(obj, name, prop_name, value):
    def run():
        mod = obj.modifiers[name]
        if isinstance(value, str) and mod.bl_rna.properties.get(prop_name) is not None:
            setattr(mod, prop_name, _value(mod.bl_rna.properties[prop_name], value))
        else:
            setattr(mod, prop_name, value)
        return None
    return run


def _applier(obj, name):
    def run():
        before = len(obj.data.vertices)
        with _context(obj):
            _run(bpy.ops.object.modifier_apply, modifier=name)
        return f"applied: {before} -> {len(obj.data.vertices)} vertices"
    return run


def _set_crease(obj, terms, value, kind="crease"):
    """Set the crease (or bevel weight) of the edges the selection names; returns how many."""
    try:
        return mesh_ops.crease(obj, terms, value, kind)
    except mesh_ops.MeshOpError as e:
        raise ObjectOpError(str(e)) from None
