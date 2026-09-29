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
from . import object_ops
from . import ops as ops_mod
from . import render as render_mod
from .cage_format import CageFormatError, normalize_face
from .frame import Frame

STATE_VERSION = 2
TEXT_TOL = 1e-6  # permille, between values parsed from text
MESH_TOL = 1e-7  # m, between exact mesh positions


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
    }


def _save_state(path, now, text, frame, concept=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": STATE_VERSION,
        "next_id": max(now["co"], default=-1) + 1,
        "co": {str(k): list(v) for k, v in sorted(now["co"].items())},
        "faces": [list(f) for f in now["faces"]],
        "frame": frame.to_json(),
        "concept": concept,
        "text": text,
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


def sync(name, resolve=None, dry_run=False, render=True):
    """Bring the cage text and the mesh of object `name` to the same state.

    resolve: None stops at a conflict; "mesh" keeps the Blender edit and saves
    the text edit to <object>.rejected.txt; "text" applies the text edit over
    the Blender edit. Only resolve a conflict when the human has decided.
    dry_run: report what would happen, write nothing.
    render: write the view sheet <object>.png next to the text.
    Returns a JSON-ready report.
    """
    if resolve not in (None, "mesh", "text"):
        raise SyncError(f"resolve must be None, 'mesh' or 'text', not {resolve!r}")
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise SyncError(f"no mesh object named {name!r}")
    if obj.mode == "EDIT":
        raise SyncError(f"{name} is in Edit Mode: leave it (Tab) so the mesh data is current, then sync again.")

    p = paths(obj)
    state = _load_state(p["state"])
    ids, fresh = mesh_io.ensure_ids(obj.data, state and state["co"], state["next_id"] if state else 0,
                                    write=not dry_run)
    now = mesh_io.mesh_state(obj.data, ids)
    mirror = mesh_io.mirror_setup(obj)
    sides = mesh_io.kept_sides(obj.data, mirror)
    report = {"object": name, "text": str(p["text"]), "action": None, "issues": []}

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
    if cur is not None and cur.ops:
        object_lines = [line for line in cur.ops if object_ops.verb(line) in object_ops.VERBS]
        try:
            appliers = object_ops.check_all(obj, object_lines, cur)
        except object_ops.ObjectOpError as e:
            report.update(action="error", error=f"ops: {e}. Nothing was written.")
            return report
        position_lines = [line for line in cur.ops if line not in object_lines]

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
        if appliers:
            td["changed"] = True
        if td["sub_edited"]:
            report["issues"].append(_warn("sub_read_only", "sub columns are read-only; the edit was ignored",
                                          td["sub_edited"]))
        if td["edges_edited"]:
            report["issues"].append(_warn("edges_read_only", "the edges section is read-only; the edit was ignored"))
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
                ids, more = mesh_io.ensure_ids(obj.data, now["co"], max(now["co"], default=-1) + 1)
                fresh = list(fresh) + more
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
    # The push already ran the position checks that check_mesh repeats.
    unique = []
    for issue in report["issues"]:
        if issue not in unique:
            unique.append(issue)
    report["issues"] = unique
    return report


def _write(obj, p, ids, frame, forms, report, concept=None, render=True):
    """Rewrite the text from the mesh, record it as the synced state, render."""
    dg = _depsgraph()
    cage = mesh_io.build_cage(obj, ids, dg, frame, forms)
    new_text = cage_format.write(cage)
    p["text"].parent.mkdir(parents=True, exist_ok=True)
    p["text"].write_text(new_text, "utf-8")
    _save_state(p["state"], mesh_io.mesh_state(obj.data, ids), new_text, frame, concept)
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


def views(name, views=None, render_name=None):
    """Render any cameras of the current mesh without syncing.

    views: preset names ("front", "back", "left", "right", "top", "bottom"),
    "yaw,pitch" strings or (yaw, pitch) pairs in degrees; yaw 0 looks from the
    front, 90 from the right; pitch > 0 looks from above. Default: 3/4 views
    from above, from below and from the back. Writes <object>.views.png (or
    <object>.<render_name>.png) next to the text and returns its path.
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
    return {"render": str(render_mod.render_views(obj, ids, _depsgraph(), views, path, title))}
