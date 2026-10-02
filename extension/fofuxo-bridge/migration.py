"""Lossless legacy metadata and sidecar migration, refusing conflicting destinations."""

import json
from pathlib import Path

import bpy

NAMES = {"fofuxo_cage_id": "llm_modeling_bridge_id", "fofuxo_cage_lock": "llm_modeling_bridge_lock",
         "fofuxo_show_vertex": "llm_bridge_show_vertex", "fofuxo_loop": "llm_bridge_loop",
         "fofuxo_show_face": "llm_bridge_show_face", "fofuxo_review": "llm_bridge_review",
         "fofuxo_on": "llm_bridge_on", "fofuxo_perspective": "llm_bridge_perspective"}


class MigrationError(RuntimeError):
    pass


def _replace_paths(value, old, new):
    if isinstance(value, str):
        return value.replace(str(old), str(new)).replace(old.as_posix(), new.as_posix())
    if isinstance(value, list):
        return [_replace_paths(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: _replace_paths(item, old, new) for key, item in value.items()}
    return value


def data_root(blend=None, migrate=True):
    filename = blend or bpy.data.filepath
    if not filename:
        raise MigrationError("save the .blend before using sidecars")
    source = Path(filename).resolve()
    old, new = source.with_suffix(".cage"), source.with_suffix(".bridge")
    if migrate and old.exists():
        if new.exists():
            raise MigrationError(f"both {old.name} and {new.name} exist; reconcile them before migrating")
        if old.resolve().parent != source.parent or new.resolve().parent != source.parent:
            raise MigrationError("sidecars must remain beside the explicitly opened .blend")
        repairs = []
        for relative in ("review.json", ".state/review.json", "review.update.json"):
            path = old / relative
            if path.exists():
                data = json.loads(path.read_text("utf-8"))
                repairs.append((Path(relative), _replace_paths(data, old, new)))
        old.rename(new)
        for relative, data in repairs:
            (new / relative).write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
    return new


def migrate_scene():
    changes = []
    attributes = []
    properties = []
    owners = [*bpy.data.objects, *bpy.data.scenes, *bpy.data.meshes]
    # Preflight all conflicts before changing any metadata.
    for mesh in bpy.data.meshes:
        for old, new in NAMES.items():
            attribute = mesh.attributes.get(old)
            if attribute is not None:
                if mesh.attributes.get(new) is not None:
                    raise MigrationError(f"{mesh.name}: both {old} and {new} exist")
                attributes.append((attribute, old, new))
    for owner in owners:
        for old, new in NAMES.items():
            if old in owner:
                if new in owner:
                    raise MigrationError(f"{owner.name}: both {old} and {new} exist")
                properties.append((owner, old, new))
    if bpy.data.filepath:
        data_root()
    for attribute, old, new in attributes:
        attribute.name = new
        changes.append({"attribute": old, "renamed": new})
    for owner, old, new in properties:
        owner[new] = owner[old]
        del owner[old]
        changes.append({"owner": owner.name, "property": old, "renamed": new})
    return {"migrated": changes, "saved": False}


@bpy.app.handlers.persistent
def on_load(*_args):
    try:
        migrate_scene()
    except (MigrationError, OSError, ValueError) as error:
        print(f"LLM Modeling Bridge: migration blocked: {error}")


def register():
    if on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_load)
    # Blender restricts scene access during add-on activation.
    if not bpy.app.timers.is_registered(on_load):
        bpy.app.timers.register(on_load, first_interval=0.1)


def unregister():
    if bpy.app.timers.is_registered(on_load):
        bpy.app.timers.unregister(on_load)
    if on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_load)
