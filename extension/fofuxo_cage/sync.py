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
        "text": data["text"],
    }


def _save_state(path, now, text, frame):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": STATE_VERSION,
        "next_id": max(now["co"], default=-1) + 1,
        "co": {str(k): list(v) for k, v in sorted(now["co"].items())},
        "faces": [list(f) for f in now["faces"]],
        "frame": frame.to_json(),
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


def sync(name, resolve=None, dry_run=False):
    """Bring the cage text and the mesh of object `name` to the same state.

    resolve: None stops at a conflict; "mesh" keeps the Blender edit and saves
    the text edit to <object>.rejected.txt; "text" applies the text edit over
    the Blender edit. Only resolve a conflict when the human has decided.
    dry_run: report what would happen, write nothing.
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

    if push is not None:
        if push["added"] or push["removed"] or push["faces"] or push["ops"]:
            report.update(action="error", error="topology edits and ops are not implemented yet; "
                                                "only base x y z can change. Nothing was written.")
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
        if not dry_run:
            mesh_io.write_positions(obj, ids, new_co)
            _undo_push(f"Fofuxo Cage: sync {name}")

    if fresh:
        report["issues"].append(_warn("new_ids", "vertices new since the last sync got fresh ids", fresh))
    if dry_run:
        report["dry_run"] = True
        return report

    if report.get("rejected"):
        p["rejected"].write_text(text, "utf-8")
    _write(obj, p, ids, frame, cur.forms if cur else (), report)
    has_subsurf = any(m.type == "SUBSURF" and m.show_viewport for m in obj.modifiers)
    report["issues"] += validate.check_mesh(obj, ids, mirror, sides, has_subsurf)
    return report


def _write(obj, p, ids, frame, forms, report):
    """Rewrite the text from the mesh and record it as the synced state."""
    cage = mesh_io.build_cage(obj, ids, _depsgraph(), frame, forms)
    new_text = cage_format.write(cage)
    p["text"].parent.mkdir(parents=True, exist_ok=True)
    p["text"].write_text(new_text, "utf-8")
    _save_state(p["state"], mesh_io.mesh_state(obj.data, ids), new_text, frame)
    report["frame"] = cage.header["frame"]
    report["size"] = cage.header["size"]
    report["count"] = cage.header["count"]


def set_frame(name, w=None, d=None, h=None):
    """Resize the frame to full visible sizes in mm, e.g. measured on the concept.

    On a mirrored axis the size spans both sides of the plane. None keeps an
    axis. Syncs first; a conflict or error stops here and nothing changes.
    The mesh never moves: only the numbers in the text change.
    """
    report = sync(name)
    if report["action"] in ("conflict", "error"):
        report["error"] = "sync first: " + report.get("error", report["action"])
        return report
    obj = bpy.data.objects[name]
    p = paths(obj)
    state = _load_state(p["state"])
    ids, _ = mesh_io.ensure_ids(obj.data, state["co"], state["next_id"])
    forms = cage_format.parse(p["text"].read_text("utf-8")).forms
    _write(obj, p, ids, state["frame"].resized(w, d, h), forms, report)
    report["action"] = "reframed"
    return report
