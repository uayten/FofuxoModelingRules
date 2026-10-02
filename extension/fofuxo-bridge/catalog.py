"""Immutable human-edit examples with stable-id deltas and stored shape measures."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time
import tempfile

import bpy


@contextmanager
def borrowed_objects(source, names=None, allow_missing=False):
    kinds = tuple(kind for kind in ("objects", "meshes", "materials", "images", "textures", "node_groups", "collections",
                                   "curves", "armatures", "actions", "shape_keys", "cameras", "lights", "annotations", "libraries")
                  if hasattr(bpy.data, kind))
    before = {kind: set(getattr(bpy.data, kind)) for kind in kinds}
    temporary = None
    try:
        if bpy.data.filepath and Path(source).resolve() == Path(bpy.data.filepath).resolve():
            temporary = tempfile.TemporaryDirectory(prefix="llm_bridge_snapshot_")
            snapshot = Path(temporary.name) / "snapshot.blend"
            shutil.copy2(source, snapshot)
            source = snapshot
        with bpy.data.libraries.load(str(source), link=False) as (src, dst):
            wanted = list(names) if names is not None else list(src.objects)
            missing = set(wanted) - set(src.objects)
            if missing and not allow_missing:
                raise ValueError(f"objects missing from {source}: {sorted(missing)}")
            wanted = [name for name in wanted if name in src.objects]
            dst.objects = list(wanted)
        yield dict(zip(wanted, dst.objects))
    finally:
        for kind in kinds:
            collection = getattr(bpy.data, kind)
            for item in set(collection) - before[kind]:
                if kind == "objects":
                    collection.remove(item, do_unlink=True)
                else:
                    collection.remove(item, do_unlink=True)
        if temporary:
            temporary.cleanup()


def _positions(obj):
    if obj.type != "MESH":
        return None
    from .mesh_io import ID_ATTR
    attribute = obj.data.attributes.get(ID_ATTR) or obj.data.attributes.get("fofuxo_cage_id")
    if attribute is None:
        return None
    ids = [item.value for item in attribute.data]
    if len(set(ids)) != len(ids):
        return None
    return {vid: [round(value * 1000, 5) for value in vertex.co] for vid, vertex in zip(ids, obj.data.vertices)}


def snapshot_delta(before, after, names):
    with borrowed_objects(before, names, allow_missing=True) as objects:
        initial = {name: _positions(obj) for name, obj in objects.items()}
    with borrowed_objects(after, names, allow_missing=True) as objects:
        final = {name: _positions(obj) for name, obj in objects.items()}
    result = {}
    for name in names:
        if name not in initial or name not in final:
            result[name] = {"status": "object_added" if name in final else "object_removed" if name in initial else "object_missing"}
            continue
        a, b = initial[name], final[name]
        if a is None or b is None:
            result[name] = {"status": "unavailable", "reason": "stable ids missing or duplicated; do not infer correspondence from indices"}
            continue
        moved = {f"v{vid}": [round(y - x, 5) for x, y in zip(a[vid], b[vid])] for vid in a.keys() & b.keys() if any(abs(y - x) > 0.001 for x, y in zip(a[vid], b[vid]))}
        result[name] = {"moved_mm": moved, "added": [f"v{vid}" for vid in sorted(b.keys() - a.keys())],
                        "removed": [f"v{vid}" for vid in sorted(a.keys() - b.keys())]}
    return result


def catalog_edit(before, after, out, names, why=None, operators=None, inputs=None):
    """Preserve the human's saved file, never invent a reason or a verdict."""
    target = Path(out).resolve()
    sources = [Path(before).resolve(), Path(after).resolve()]
    if not names or any(not path.is_file() for path in sources):
        raise ValueError("provide named objects and existing before/after files")
    if target.exists():
        raise FileExistsError(f"example already exists: {target}")
    deltas = snapshot_delta(*sources, names)
    target.mkdir(parents=True)
    shutil.copy2(sources[0], target / "before.blend")
    shutil.copy2(sources[1], target / "after.blend")
    logs = {}
    from .recording import recording_summary
    for kind, source in (("operators", operators), ("inputs", inputs)):
        if source and Path(source).is_file():
            filename = f"{kind}.jsonl"
            shutil.copy2(source, target / filename)
            logs[kind] = recording_summary(target / filename, candidates=kind == "inputs")
    data = {"before_source": str(sources[0]), "after_source": str(sources[1]), "objects": list(names),
            "why": why, "status": "recorded; awaiting interview and replay validation", "deltas": deltas, "recordings": logs}
    (target / "edit.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    explanation = why or "The modeler has not supplied the reason. Ask during the next review; do not promote this example to a rule yet."
    (target / "EXAMPLE.md").write_text("# Human edit\n\nA preserved correction with stable-id deltas and recorder receipts.\n\n## Contents\n\n- [Files](#files)\n- [Why](#why)\n- [Validation](#validation)\n\n## Files\n\n- `before.blend`: the saved AI file before the correction.\n- `after.blend`: the human's saved review.\n- `edit.json`: deltas in local mm, provenance, recorder summary.\n\n## Why\n\n" + explanation + "\n\n## Validation\n\nRecorded only. Replay and artistic approval are pending.\n", "utf-8")
    return {"example": str(target), "status": data["status"]}


def human_directory(blend):
    source = Path(blend).resolve()
    task_root = next((parent.parent for parent in source.parents if parent.name == "ai"), source.parent)
    return task_root / "human"


def archive_review(before, after, names, why=None, human_dir=None, recording_root=None):
    root = Path(human_dir) if human_dir else human_directory(before)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    logs = Path(recording_root) if recording_root else Path(after).parent
    prefix = "handover" if recording_root else "review"
    return catalog_edit(before, after, root / f"review-{stamp}-{time.time_ns()}", names, why=why,
                        operators=logs / f"{prefix}.ops.jsonl", inputs=logs / f"{prefix}.input.jsonl")


def catalog_measures(source, names, out):
    """Measure in background so appending reference objects cannot disturb a live scene."""
    if not bpy.app.background:
        raise RuntimeError("catalog_measures runs in a background Blender; keep the review window intact")
    target = Path(out)
    if target.exists():
        raise FileExistsError(f"measures already exist: {target}")
    from .evenness import measure
    from .shape import dense, profile, Surface
    result = {"source": str(source), "how": "local mm; evaluated limit surface at Subdivision level 3", "objects": {}}
    with borrowed_objects(source, names) as objects:
        for name, obj in objects.items():
            if obj.type != "MESH":
                continue
            bpy.context.scene.collection.objects.link(obj)
            co, triangles = dense(obj)
            surface = Surface(co, triangles, name)
            result["objects"][name] = {"cage": {"verts": len(obj.data.vertices), "faces": len(obj.data.polygons)},
                                        "stack": [f"{modifier.name} ({modifier.type})" for modifier in obj.modifiers],
                                        "size_mm": surface.size_mm(), "evenness_cage": measure(obj.data),
                                        "profiles": {view: profile(None, view, co=co) for view in ("front", "top", "side")}}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    return {"measures": str(target), "objects": list(result["objects"])}
