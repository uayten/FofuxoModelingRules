"""Relative edits written in the ops section, in percent of the frame.

    move <targets> <axes> <+N%>        move by N% of the frame (1% = 10 permille)
    scale <targets> <axes> <N%>        scale around the targets' center
    scale <targets> <axes> <N%> from 0 scale from the frame's 0 (the mirror plane)

targets: vertex ids (v7), loop labels from the verts section (L1, rest) or
all. axes: any of w, d, h (e.g. wh). Coordinates on a mirror plane stay on it.
Ops run in order, after any line edits, and are cleared once applied.

    target <vid> <axis> <value> [<axis> <value> ...]

sets where a vertex lands after the stack (its sub column, in permille), e.g.
target v22 w 944 d 606. The sync solves the base positions after every other
op (sync.solve_targets); axes not named keep their base value.
"""

import re

AXES = "wdh"
_AMOUNT = re.compile(r"([+-]?\d+(?:\.\d+)?)%")


class OpError(ValueError):
    pass


def parse(line):
    tokens = line.replace(",", " ").split()
    if not tokens or tokens[0].lower() not in ("move", "scale"):
        raise OpError(f"unknown op {line!r}: use move, scale or target")
    verb, rest = tokens[0].lower(), tokens[1:]
    from_zero = False
    if verb == "scale" and [t.lower() for t in rest[-2:]] == ["from", "0"]:
        from_zero, rest = True, rest[:-2]
    if len(rest) < 3:
        raise OpError(f"{line!r}: expected '{verb} <targets> <axes> <amount>%'")
    *targets, axes, amount = rest
    if not re.fullmatch(r"[wdh]{1,3}", axes.lower()):
        raise OpError(f"{line!r}: axes must be letters from w, d, h, not {axes!r}")
    m = _AMOUNT.fullmatch(amount)
    if not m:
        raise OpError(f"{line!r}: amount must be a percentage like +4% or 105%, not {amount!r}")
    return verb, targets, axes.lower(), float(m[1]), from_zero


def is_target(line):
    tokens = line.split()
    return bool(tokens) and tokens[0].lower() == "target"


def parse_target(line, cage, keep_on_plane):
    """(vid, {axis index: sub value}) from a target line."""
    tokens = line.replace(",", " ").split()[1:]
    if len(tokens) < 3 or len(tokens) % 2 == 0:
        raise OpError(f"{line!r}: expected 'target <vid> <axis> <value> [<axis> <value> ...]'")
    vid_token, pairs = tokens[0].lower(), tokens[1:]
    if not re.fullmatch(r"v\d+", vid_token) or int(vid_token[1:]) not in cage.verts:
        raise OpError(f"{line!r}: no vertex {tokens[0]}")
    vid = int(vid_token[1:])
    goal = {}
    for axis, value in zip(pairs[::2], pairs[1::2]):
        axis = axis.lower()
        if axis not in AXES:
            raise OpError(f"{line!r}: axis must be w, d or h, not {axis!r}")
        try:
            goal[AXES.index(axis)] = float(value)
        except ValueError:
            raise OpError(f"{line!r}: value must be permille like 606, not {value!r}") from None
        if keep_on_plane(vid, AXES.index(axis)):
            raise OpError(f"{line!r}: v{vid} lies on the mirror plane of {axis}; that value stays 0")
    return vid, goal


def _targets(tokens, cage, line):
    groups = {label.lower(): ids for label, ids in cage.groups if label}
    out = []
    for t in tokens:
        low = t.lower()
        if low == "all":
            out += list(cage.verts)
        elif re.fullmatch(r"v\d+", low):
            vid = int(low[1:])
            if vid not in cage.verts:
                raise OpError(f"{line!r}: no vertex {t}")
            out.append(vid)
        elif low in groups:
            out += groups[low]
        else:
            raise OpError(f"{line!r}: unknown target {t!r}; use vN, a loop label or all")
    return list(dict.fromkeys(out))


def apply(cage, lines, keep_on_plane, precise):
    """Apply ops to the cage's base values in place.

    keep_on_plane(vid, k) is true when coordinate k of vid lies on a mirror
    plane and must stay there. precise(vid) gives the vertex's exact values
    (the text rounds to whole permille), so an op never adds rounding drift.
    Returns a summary per op.
    """
    done = []
    touched = set()
    for line in lines:
        verb, targets, axes, amount, from_zero = parse(line)
        ids = _targets(targets, cage, line)
        for vid in ids:
            if vid not in touched:
                cage.verts[vid].base = tuple(precise(vid))
                touched.add(vid)
        for a in axes:
            k = AXES.index(a)
            vals = {vid: cage.verts[vid].base[k] for vid in ids if not keep_on_plane(vid, k)}
            if not vals:
                continue
            if verb == "move":
                new = {vid: v + amount * 10 for vid, v in vals.items()}
            else:
                c = 0.0 if from_zero else (min(vals.values()) + max(vals.values())) / 2
                new = {vid: c + (v - c) * amount / 100 for vid, v in vals.items()}
            for vid, v in new.items():
                base = list(cage.verts[vid].base)
                base[k] = v
                cage.verts[vid].base = tuple(base)
        done.append(f"{line}  ({len(ids)} verts)")
    return done
