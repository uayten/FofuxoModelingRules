"""Three-way sync between the cage text, the mesh and the last synced state.

text changed, mesh not  -> push (text to mesh)
mesh changed, text not  -> pull (mesh to text)
both changed            -> conflict: nothing is written until someone decides
"""

import json
import re
from pathlib import Path

import bpy

from . import cage_format, mesh_io, topology, validate
from . import concept as concept_mod
from .lock import took_over
from . import object_ops
from . import marks as marks_mod
from . import targets as targets_mod
from . import ops as ops_mod
from . import render as render_mod
from .cage_format import CageFormatError, normalize_face
from .frame import AxisFrame, Frame

STATE_VERSION = 2
TEXT_TOL = 1e-6  # permille, between values parsed from text
MESH_TOL = 1e-7  # m, between exact mesh positions
TARGET_TOL = 0.25  # permille: a target op stops once every sub value is this close
TARGET_STEPS = 40


class SyncError(RuntimeError):
    pass


def paths(obj):
    blend = bpy.data.filepath
    if not blend:
        raise SyncError("Save the .blend first: the cage text lives next to it.")
    root = Path(blend).with_suffix(".cage")
    safe = re.sub(r'[<>:"/\\|?*]', "_", obj.name)
    return {
        "text": root / f"{safe}.txt",
        "render": root / f"{safe}.png",
        "state": root / ".state" / f"{safe}.json",
        "rejected": root / f"{safe}.rejected.txt",
    }


def _load_state(path):
    if not path.exists():
        return None
    data = json.loads(path.read_text("utf-8"))
    return {
        "co": {int(k): tuple(v) for k, v in data["co"].items()},
        "faces": [tuple(f) for f in data["faces"]],
        "next_id": data["next_id"],
        "frame": Frame.from_json(data["frame"]) if "frame" in data else None,
        "concept": data.get("concept"),
        "text": data["text"],
        "annotations": data.get("annotations", []),
    }


def _save_state(path, now, text, frame, concept=None, annotations=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": STATE_VERSION,
        "next_id": max(now["co"], default=-1) + 1,
        "co": {str(k): list(v) for k, v in sorted(now["co"].items())},
        "faces": [list(f) for f in now["faces"]],
        "frame": frame.to_json(),
        "concept": concept,
        "text": text,
        "annotations": list(annotations),
    }
    path.write_text(json.dumps(data), "utf-8")


def _differs(a, b, tol):
    return any(abs(x - y) > tol for x, y in zip(a, b))


def _text_diff(cur, prev):
    common = [vid for vid in cur.verts if vid in prev.verts]

    def sub_edited(vid):
        # Dropping the sub columns from a line is fine; changing them is not.
        a, b = cur.verts[vid].sub, prev.verts[vid].sub
        return a is not None and b is not None and _differs(a, b, TEXT_TOL)

    diff = {
        "moved": {vid: cur.verts[vid].base for vid in common
                  if _differs(cur.verts[vid].base, prev.verts[vid].base, TEXT_TOL)},
        "added": sorted(set(cur.verts) - set(prev.verts)),
        "removed": sorted(set(prev.verts) - set(cur.verts)),
        "faces": sorted(map(normalize_face, cur.faces)) != sorted(map(normalize_face, prev.faces)),
        "ops": list(cur.ops),
        "sub_edited": sorted(vid for vid in common if sub_edited(vid)),
        "edges_edited": cur.edges != prev.edges,
        "modifiers_edited": cur.modifiers != prev.modifiers,
        "frame_edited": cur.header.get("frame") != prev.header.get("frame"),
    }
    diff["changed"] = bool(diff["moved"] or diff["added"] or diff["removed"] or diff["faces"] or diff["ops"])
    return diff


def _mesh_diff(now, state):
    diff = {
        "moved": sorted(vid for vid, co in now["co"].items()
                        if vid in state["co"] and _differs(co, state["co"][vid], MESH_TOL)),
        "added": sorted(set(now["co"]) - set(state["co"])),
        "removed": sorted(set(state["co"]) - set(now["co"])),
        "faces": now["faces"] != sorted(map(normalize_face, state["faces"])),
    }
    diff["changed"] = bool(diff["moved"] or diff["added"] or diff["removed"] or diff["faces"])
    return diff


def _deltas(frame, before, after):
    """Moves in percent of the frame, e.g. "v7 h+4.0%". On a mirrored axis a
    positive change moves away from the plane."""
    out = []
    for vid in sorted(after):
        if vid not in before:
            continue
        a, b = frame.to_values(before[vid]), frame.to_values(after[vid])
        parts = [f"{n}{(y - x) / 10:+.1f}%" for n, x, y in zip("wdh", a, b) if abs(y - x) >= 0.5]
        if parts:
            out.append(f"v{vid} " + " ".join(parts))
    return out


def _by_loop(frame, groups, before, after, moved):
    """The human's moves grouped by the loops of the text, e.g. "L1 7/7 h+4.0%"
    (7 of its 7 vertices moved, h by 4% on average): the shape of an edit,
    for the AI to read an intent from and ask about."""
    moved = set(moved)
    out = []
    for label, ids in groups:
        hit = [v for v in ids if v in moved and v in before and v in after]
        if len(hit) < 2:
            continue
        d = [[(b - a) / 10 for a, b in zip(frame.to_values(before[v]), frame.to_values(after[v]))] for v in hit]
        mean = [sum(col) / len(col) for col in zip(*d)]
        parts = [f"{n}{m:+.1f}%" for n, m in zip("wdh", mean) if abs(m) >= 0.05]
        out.append(f"{label or 'rest'} {len(hit)}/{len(ids)} " + (" ".join(parts) or "moved, no mean shift"))
    return out


def _warn(code, msg, vids=()):
    return validate._issue("WARN", code, msg, vids)


def _undo_push(message):
    try:
        bpy.ops.ed.undo_push(message=message)
    except Exception:  # no undo stack in background mode
        pass


def _depsgraph():
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


def sync(name, resolve=None, dry_run=False, render=True, verbose=False):
    """Bring the cage text and the mesh of object `name` to the same state.

    resolve: None stops at a conflict; "mesh" keeps the Blender edit and saves
    the text edit to <object>.rejected.txt; "text" applies the text edit over
    the Blender edit. Only resolve a conflict when the human has decided.
    dry_run: report what would happen, write nothing.
    render: write the view sheet <object>.png next to the text.
    verbose: always include the modifiers section; by default it comes only
    when the stack changed (fewer tokens for the reader).
    Returns a JSON-ready report.
    """
    if resolve not in (None, "mesh", "text"):
        raise SyncError(f"resolve must be None, 'mesh' or 'text', not {resolve!r}")
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise SyncError(f"no mesh object named {name!r}")
    if obj.mode == "EDIT":
        raise SyncError(f"{name} is in Edit Mode: take control with lock({name!r}) (it leaves Edit Mode and keeps "
                        "the edits), or leave it (Tab), then sync again.")

    p = paths(obj)
    state = _load_state(p["state"])
    ids, fresh = mesh_io.ensure_ids(obj.data, state and state["co"], state["next_id"] if state else 0,
                                    write=not dry_run)
    now = mesh_io.mesh_state(obj.data, ids)
    mirror = mesh_io.mirror_setup(obj)
    sides = mesh_io.kept_sides(obj.data, mirror)
    report = {"object": name, "text": str(p["text"]), "action": None, "issues": []}
    if took_over():
        report["issues"].append(_warn("human_took_over", "the human released the AI lock (Esc or Unlock): "
                                                         "stop and ask before editing on"))

    text = p["text"].read_text("utf-8") if p["text"].exists() else None
    cur = None
    if text is not None:
        try:
            cur = cage_format.parse(text)
        except CageFormatError as e:
            report.update(action="error", error=f"cage text: {e}")
            return report

    # The frame is frozen at the first sync and only changes through set_frame.
    frame = state["frame"] if state else None
    if frame is None and cur is not None:
        frame = Frame.parse(cur.header.get("frame", ""))
    if frame is None:
        frame = mesh_io.default_frame(obj, _depsgraph())

    appliers = []
    targets = {}
    if cur is not None and cur.ops:
        object_lines = [line for line in cur.ops if object_ops.verb(line) in object_ops.VERBS]
        try:
            next_id = max([state["next_id"] if state else 0, *[i + 1 for i in ids]])
            appliers = object_ops.check_all(obj, object_lines, cur, frame, next_id)
        except object_ops.ObjectOpError as e:
            report.update(action="error", error=f"ops: {e}. Nothing was written.")
            return report
        target_lines = [line for line in cur.ops if ops_mod.is_target(line)]
        position_lines = [line for line in cur.ops if line not in object_lines and line not in target_lines]

        def keep_on_plane(vid, k):
            co = now["co"].get(vid)
            return co is not None and topology.AXES[k] in topology.on_planes(co, mirror)
        def precise(vid):
            # Exact values from the mesh, unless the line itself was edited.
            text_vals = cur.verts[vid].base
            co = now["co"].get(vid)
            if co is None:
                return text_vals
            exact = frame.to_values(co)
            same = all(abs(round(e) - t) < TEXT_TOL for e, t in zip(exact, text_vals))
            return exact if same else text_vals

        try:
            report["ops"] = ops_mod.apply(cur, position_lines, keep_on_plane, precise)
            for line in target_lines:
                vid, goal = ops_mod.parse_target(line, cur, keep_on_plane)
                targets.setdefault(vid, {}).update(goal)
            if targets and not appliers and mesh_io.evaluated(obj, _depsgraph())[0] is None:
                raise ops_mod.OpError("target needs the sub columns (a Mirror and Subdivision stack)")
        except ops_mod.OpError as e:
            report.update(action="error", error=f"ops: {e}. Nothing was written.")
            return report
        cur.ops = []

    push = None
    if cur is None:
        report["action"] = "init" if state is None else "pulled"
    else:
        if state is None:
            # No sync state yet: the text is compared with the mesh itself,
            # and any difference is a conflict.
            prev = cage_format.parse(cage_format.write(mesh_io.build_cage(obj, ids, _depsgraph(), frame)))
            md = {"changed": True, "moved": [], "added": [], "removed": [], "faces": False}
        else:
            prev = cage_format.parse(state["text"])
            md = _mesh_diff(now, state)
        td = _text_diff(cur, prev)
        if appliers or targets:
            td["changed"] = True
        if td["sub_edited"]:
            report["issues"].append(_warn("sub_read_only", "sub columns are read-only; the edit was ignored",
                                          td["sub_edited"]))
        if td["edges_edited"]:
            report["issues"].append(_warn("edges_read_only", "the edges section is read-only; the edit was ignored"))
        if td["modifiers_edited"]:
            report["issues"].append(_warn("modifiers_read_only",
                                          "the modifiers section is read-only; change a modifier with a set op"))
        if td["frame_edited"]:
            report["issues"].append(_warn("frame_read_only", "the frame line is read-only; use set_frame"))

        if not td["changed"]:
            report["action"] = "init" if state is None else "pulled" if md["changed"] else "unchanged"
        elif md["changed"] and resolve is None:
            both = sorted(set(td["moved"]) & set(md["moved"]))
            report.update(
                action="conflict",
                text_edits=[f"v{v}" for v in sorted(td["moved"])] + (["topology/ops"] if td["changed"] and not td["moved"] else []),
                blender_edits=([f"v{v}" for v in md["moved"]] + [f"+v{v}" for v in md["added"]]
                               + [f"-v{v}" for v in md["removed"]] + (["faces"] if md["faces"] else []))
                              or ["no sync state: text and mesh differ"],
                both=[f"v{v}" for v in both],
                hint="Nothing was written. Ask the human: resolve='mesh' keeps the Blender edit "
                     "(the text edit is saved aside); resolve='text' applies the text edit over it.",
            )
            return report
        elif md["changed"] and resolve == "mesh":
            report["action"] = "pulled"
            report["rejected"] = str(p["rejected"])
        else:
            push = td
            report["action"] = "pushed"
        if state is not None and md["changed"]:
            report["blender_edits"] = ([f"v{v}" for v in md["moved"]] + [f"+v{v}" for v in md["added"]]
                                       + [f"-v{v}" for v in md["removed"]])
            report["blender_deltas"] = _deltas(frame, state["co"], {v: now["co"][v] for v in md["moved"]})
            by_loop = _by_loop(frame, cage_format.parse(state["text"]).groups, state["co"], now["co"], md["moved"])
            if by_loop:
                report["blender_by_loop"] = by_loop

    if push is not None:
        if push["added"] or push["removed"] or push["faces"]:
            report.update(action="error", error="topology edits are not implemented yet; only base w d h "
                                                "and move/scale ops can change. Nothing was written.")
            return report
        new_co, snapped, gone = {}, [], []
        for vid, base in push["moved"].items():
            if vid not in now["co"]:
                gone.append(vid)
                continue
            co = list(frame.to_local(base))
            for a in topology.on_planes(now["co"][vid], mirror):
                k = topology.AXES.index(a)
                if abs(co[k]) >= topology.PLANE_TOL:
                    snapped.append(vid)
                    co[k] = 0.0
            new_co[vid] = tuple(co)
        issues = validate.check_positions(new_co, mirror, sides)
        if snapped:
            issues.append(_warn("kept_on_plane", "on a mirror plane: the coordinate across it stays 0", set(snapped)))
        if gone:
            issues.append(_warn("deleted_in_blender", "deleted in Blender; the text edit was skipped", gone))
        report["issues"] += issues
        if any(i["level"] == "ERROR" for i in issues):
            report.update(action="error", error="position rules broken. Nothing was written.")
            return report
        report["moved"] = [f"v{v}" for v in sorted(new_co)]
        report["deltas"] = _deltas(frame, now["co"], new_co)
        if not dry_run:
            mesh_io.write_positions(obj, ids, new_co)
            for line, run in appliers:
                try:
                    note = run()
                except object_ops.ObjectOpError as e:
                    report["issues"].append(validate._issue("ERROR", "op_failed", f"{line!r}: {e}; later ops skipped"))
                    break
                report.setdefault("ops", []).append(f"{line}  ({note})" if note else line)
            if appliers:
                # apply can add vertices (e.g. Mirror): give them ids before writing.
                ids, more = mesh_io.ensure_ids(obj.data, now["co"], max([state["next_id"] if state else 0,
                                                                        max(now["co"], default=-1) + 1]))
                fresh = list(fresh) + more
            if targets:
                _run_targets(obj, ids, frame, targets, target_lines, now, report)
            _undo_push(f"Fofuxo Cage: sync {name}")

    if fresh:
        report["issues"].append(_warn("new_ids", "vertices new since the last sync got fresh ids", fresh))
    if dry_run:
        report["dry_run"] = True
        return report

    if report.get("rejected"):
        p["rejected"].write_text(text, "utf-8")
    _write(obj, p, ids, frame, cur.forms if cur else (), report, state and state.get("concept"), render)
    if appliers:  # the stack may have changed
        mirror = mesh_io.mirror_setup(obj)
        sides = mesh_io.kept_sides(obj.data, mirror)
    has_subsurf = any(m.type == "SUBSURF" and m.show_viewport for m in obj.modifiers)
    report["issues"] += validate.check_mesh(obj, ids, mirror, sides, has_subsurf)
    if has_subsurf and not any(i["level"] == "ERROR" for i in report["issues"]):
        report["issues"] += validate.check_editability(obj, ids, _depsgraph(), mirror)
    report["issues"] += targets_mod.budget_issues(obj)  # the task's poly budget (target.md)
    if "Y" in mirror and sides.get("Y") == "+":
        report["issues"].append(_warn("modeled_behind", "the base mesh is on +Y, behind its mirror copy in the "
                                                        "front view: model on -Y (flip(name, 'd'), D-055)"))
    # The push already ran the position checks that check_mesh repeats.
    unique = []
    for issue in report["issues"]:
        if issue not in unique:
            unique.append(issue)
    report["issues"] = unique
    if not verbose and "stack_changes" not in report:
        report.pop("modifiers", None)
    return report


def annotations(name):
    """Every Annotate stroke with the vertices under it (not only the new ones)."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise SyncError(f"no mesh object named {name!r}")
    p = paths(obj)
    state = _load_state(p["state"])
    if state is None:
        raise SyncError(f"sync {name} first: the frame lives in its sync state")
    ids, _ = mesh_io.ensure_ids(obj.data, state["co"], state["next_id"], write=False)
    return marks_mod.read(obj, ids, _depsgraph(), state["frame"], seen=None)[0]


def edit(name, *lines, **kwargs):
    """Write op lines into the text's ops section and sync: one call per edit,
    e.g. edit("Laço", "mesh translate seam d=+2% falloff=smooth radius=20%").
    Syncs once first if there is no text yet. kwargs go to sync."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise SyncError(f"no mesh object named {name!r}")
    path = paths(obj)["text"]
    if not path.exists():
        first = sync(name, render=False)
        if first["action"] in ("conflict", "error"):
            return first
    text = path.read_text("utf-8")
    if "\nops\n" not in text:
        raise SyncError(f"no ops section in {path}")
    path.write_text(text.replace("\nops\n", "\nops\n" + "".join(f"  {line}\n" for line in lines), 1), "utf-8")
    report = sync(name, **kwargs)
    if report["action"] in ("error", "conflict"):
        path.write_text(text, "utf-8")  # a refused edit leaves no lines behind for the next call
        report["note"] = "the text is as before this call"
    return report


def solve_targets(obj, ids, frame, targets, tol=TARGET_TOL, steps=TARGET_STEPS):
    """Move base vertices until their evaluated positions reach the targets.

    targets: {vid: {axis index: sub value in permille}}. Each step adds the
    remaining error to the base value: a vertex moves its own evaluated
    position by a positive fraction of its move under Subdivision (and its
    neighbours by less), so the steps converge. Returns (steps, worst error
    in permille).
    """
    index = {vid: i for i, vid in enumerate(ids)}
    verts = obj.data.vertices
    # A base value may not come closer to a mirror plane than 1.5 x the merge
    # distance: a weld changes the evaluated vertex order and the solve with it.
    floor = {}
    for a, merge in mesh_io.mirror_setup(obj).items():
        k = topology.AXES.index(a)
        floor[k] = abs(frame.axes[k].to_value(merge * 1.5))
    worst = 0.0
    for step in range(steps + 1):
        per_vertex = mesh_io.evaluated(obj, _depsgraph())[0]
        if per_vertex is None:
            raise SyncError("target needs the sub columns (a Mirror and Subdivision stack)")
        worst, moves = 0.0, {}
        for vid, goal in targets.items():
            i = index[vid]
            sub = frame.to_values(per_vertex[i])
            base = list(frame.to_values(verts[i].co))
            for k, value in goal.items():
                worst = max(worst, abs(value - sub[k]))
                base[k] += value - sub[k]
                if k in floor:
                    base[k] = max(base[k], floor[k])
            moves[vid] = frame.to_local(base)
        if worst < tol or step == steps:
            return step, worst
        mesh_io.write_positions(obj, ids, moves)


def _run_targets(obj, ids, frame, targets, lines, now, report):
    """Solve the target ops after every other op; undo them if they break a position rule."""
    index = {vid: i for i, vid in enumerate(ids)}
    gone = sorted(vid for vid in targets if vid not in index)
    if gone:  # removed by a dissolve in the same batch
        report["issues"].append(_warn("target_gone", "the vertex no longer exists; target skipped", gone))
        targets = {vid: goal for vid, goal in targets.items() if vid in index}
        if not targets:
            return
    before = {vid: tuple(obj.data.vertices[index[vid]].co) for vid in targets}
    try:
        steps, worst = solve_targets(obj, ids, frame, targets)
    except SyncError as e:
        mesh_io.write_positions(obj, ids, before)
        report["issues"].append(validate._issue("ERROR", "target_failed", f"{e}; targets skipped", targets))
        return
    after = {vid: tuple(obj.data.vertices[index[vid]].co) for vid in targets}
    mirror = mesh_io.mirror_setup(obj)
    issues = validate.check_positions(after, mirror, mesh_io.kept_sides(obj.data, mirror))
    if any(i["level"] == "ERROR" for i in issues):
        mesh_io.write_positions(obj, ids, before)
        report["issues"] += issues
        report["issues"].append(validate._issue("ERROR", "target_failed",
                                                "the solved base breaks a position rule; targets undone", targets))
        return
    report["issues"] += issues
    if worst >= TARGET_TOL:
        report["issues"].append(_warn("target_not_reached",
                                      f"worst error {worst:.1f} permille after {steps} steps", targets))
    report.setdefault("ops", []).extend(f"{line}  ({steps} steps, worst {worst:.1f})" for line in lines)
    moved = {int(v[1:]) for v in report.get("moved", [])} | set(targets)
    final = {vid: tuple(obj.data.vertices[index[vid]].co) for vid in moved}
    report["moved"] = [f"v{v}" for v in sorted(moved)]
    report["deltas"] = _deltas(frame, now["co"], final)


def _write(obj, p, ids, frame, forms, report, concept=None, render=True):
    """Rewrite the text from the mesh, record it as the synced state, render."""
    dg = _depsgraph()
    before = _load_state(p["state"])
    cage = mesh_io.build_cage(obj, ids, dg, frame, forms)
    new_text = cage_format.write(cage)
    report["modifiers"] = cage.modifiers
    if before is not None:
        old = cage_format.parse(before["text"]).modifiers
        now = [line.strip() for line in cage.modifiers]
        if old and old != now:  # a set op, or a change made in Blender
            report["stack_changes"] = [line for line in now if line not in old]
    p["text"].parent.mkdir(parents=True, exist_ok=True)
    p["text"].write_text(new_text, "utf-8")
    # The modeler points: marks new or cleared since the last sync, strokes not seen before.
    found = marks_mod.diff(cage_format.parse(before["text"]).edges if before else None, cage.edges)
    if found:
        report["marks"] = found
    strokes, seen = marks_mod.read(obj, ids, dg, frame, before["annotations"] if before else [])
    if strokes:
        report["annotations"] = strokes
    _save_state(p["state"], mesh_io.mesh_state(obj.data, ids), new_text, frame, concept, seen)
    report["frame"] = cage.header["frame"]
    report["size"] = cage.header["size"]
    report["count"] = cage.header["count"]
    if render:
        title = f"{obj.name}   frame {frame.text()}"
        try:
            report["render"] = str(render_mod.render_sheet(obj, ids, dg, frame, p["render"], title, concept))
        except Exception as e:  # a failed render never blocks the sync
            report["issues"].append(_warn("render_failed", f"render failed: {e!r}"))


def set_frame(name, w=None, d=None, h=None, concept=None, render=True):
    """Resize the frame to full visible sizes in mm, e.g. measured on the concept.

    On a mirrored axis the size spans both sides of the plane. None keeps an
    axis. concept={"image": name, "box": [x0, x1, y0, y1]} (pixels, top-left,
    inclusive; optional "mm_per_px", else read from the Image Empty) sets w and
    h from that box unless given, and ties the box to the frame so the render
    shows it behind the model. Syncs first; a conflict or error stops here.
    The mesh never moves: only the numbers in the text change.
    """
    report = sync(name, render=False)
    if report["action"] in ("conflict", "error"):
        report["error"] = "sync first: " + report.get("error", report["action"])
        return report
    obj = bpy.data.objects[name]
    p = paths(obj)
    state = _load_state(p["state"])
    kept_concept = state.get("concept")
    if concept is not None:
        cw, ch = concept_mod.box_size_mm(concept)
        w = cw if w is None else w
        h = ch if h is None else h
        kept_concept = {"image": concept["image"], "box": list(concept["box"]),
                        "mm_per_px": concept.get("mm_per_px") or concept_mod.mm_per_px(concept["image"])}
    ids, _ = mesh_io.ensure_ids(obj.data, state["co"], state["next_id"])
    forms = cage_format.parse(p["text"].read_text("utf-8")).forms
    _write(obj, p, ids, state["frame"].resized(w, d, h), forms, report, kept_concept, render)
    report["action"] = "reframed"
    return report


def flip(name, axis="d", render=True):
    """Move the modeled part to the other side of a mirror plane.

    Every base vertex is mirrored across the plane of `axis` (w, d or h) and
    the faces are rewound, so the evaluated result is the same model. The
    frame measures from the plane toward the new side, so the values in the
    text do not change. Used to model on -Y: the part the AI edits then faces
    the front view instead of hiding behind its mirror copy (D-055). Syncs
    first; a conflict or error stops here.
    """
    report = sync(name, render=False)
    if report["action"] in ("conflict", "error"):
        report["error"] = "sync first: " + report.get("error", report["action"])
        return report
    if axis not in "wdh" or len(axis) != 1:
        raise SyncError(f"axis must be w, d or h, not {axis!r}")
    obj = bpy.data.objects[name]
    p = paths(obj)
    state = _load_state(p["state"])
    k = "wdh".index(axis)
    old = state["frame"].axes[k]
    if not old.side or topology.AXES[k] not in mesh_io.mirror_setup(obj):
        raise SyncError(f"{axis} is not a mirrored axis of {name}")
    import bmesh
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        for v in bm.verts:
            v.co[k] = -v.co[k]
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
    finally:
        bm.free()
    obj.data.update()
    axes = list(state["frame"].axes)
    axes[k] = AxisFrame(old.axis, "-" if old.side == "+" else "+", 0.0, old.extent)
    ids, _ = mesh_io.ensure_ids(obj.data, None, state["next_id"], write=False)
    forms = cage_format.parse(p["text"].read_text("utf-8")).forms
    _write(obj, p, ids, Frame(tuple(axes)), forms, report, state.get("concept"), render)
    _undo_push(f"Fofuxo Cage: flip {name} {axis}")
    report["issues"] = [i for i in report["issues"] if i["code"] != "modeled_behind"]  # from the sync before
    report["action"] = "flipped"
    report["frame"] = Frame(tuple(axes)).text()
    return report


def views(name, views=None, render_name=None, focus=None, ghost=False, normals=False):
    """Render any cameras of the current mesh without syncing.

    views: preset names ("front", "back", "left", "right", "top", "bottom"),
    "yaw,pitch" strings or (yaw, pitch) pairs in degrees; yaw 0 looks from the
    front, 90 from the right; pitch > 0 looks from above. Default: 3/4 views
    from above, from below and from the back. Writes <object>.views.png (or
    <object>.<render_name>.png) next to the text and returns its path.
    focus: ids to label, the rest drawn as small gray dots (e.g. [13, 14]);
    ghost: only the base part filled, the mirror copies as faint wire;
    normals: a tick along the result's normal at each vertex.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise SyncError(f"no mesh object named {name!r}")
    if obj.mode == "EDIT":
        raise SyncError(f"{name} is in Edit Mode: leave it (Tab) first.")
    p = paths(obj)
    state = _load_state(p["state"])
    ids, _ = mesh_io.ensure_ids(obj.data, state and state["co"], state["next_id"] if state else 0, write=False)
    views = list(views or render_mod.DEFAULT_VIEWS)
    path = p["render"].with_name(f"{p['render'].stem}.{render_name or 'views'}.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    title = f"{obj.name}   " + "   ".join(render_mod.Camera(v).name for v in views)
    return {"render": str(render_mod.render_views(obj, ids, _depsgraph(), views, path, title,
                                                  focus=focus, ghost=ghost, normals=normals))}
