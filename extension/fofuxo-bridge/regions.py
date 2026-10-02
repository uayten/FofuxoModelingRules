"""Named vertex groups shared by selections, reports and the recorder."""

import bpy

from .mesh_io import ensure_ids


def groups(obj, ids=None):
    if obj.mode == "EDIT":
        import bmesh
        from .mesh_io import ID_ATTR
        bm = bmesh.from_edit_mesh(obj.data)
        id_layer = bm.verts.layers.int.get(ID_ATTR)
        weights = bm.verts.layers.deform.active
        result = {group.name: [] for group in obj.vertex_groups}
        names = {group.index: group.name for group in obj.vertex_groups}
        if weights:
            for vertex in bm.verts:
                for index, weight in vertex[weights].items():
                    if weight > 0 and index in names:
                        result[names[index]].append(vertex[id_layer] if id_layer else vertex.index)
        return result
    ids = ids if ids is not None else ensure_ids(obj.data)[0]
    names = {group.index: group.name for group in obj.vertex_groups}
    result = {name: [] for name in names.values()}
    for vertex, vid in zip(obj.data.vertices, ids):
        for membership in vertex.groups:
            if membership.weight > 0 and membership.group in names:
                result[names[membership.group]].append(vid)
    return result


def region_ids(name, region=None):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH" or obj.mode != "OBJECT":
        raise ValueError("regions require a mesh in Object Mode")
    result = groups(obj)
    if region is None:
        return {label: [f"v{vid}" for vid in ids] for label, ids in result.items()}
    if region not in result:
        raise ValueError(f"no region {region!r}")
    return [f"v{vid}" for vid in result[region]]


def motion(regions, before, after):
    result = {}
    for name, ids in regions.items():
        deltas = [[(b - a) * 1000 for a, b in zip(before[vid], after[vid])]
                  for vid in ids if vid in before and vid in after and any(abs(a - b) > 1e-7 for a, b in zip(before[vid], after[vid]))]
        if deltas:
            result[name] = {"moved": len(deltas), "total": len(ids),
                            "mean_local_mm": [round(sum(delta[axis] for delta in deltas) / len(deltas), 3) for axis in range(3)],
                            "max_mm": round(max(sum(value * value for value in delta) ** 0.5 for delta in deltas), 3)}
    return result


def axis_signs(obj):
    from .mesh_io import mirror_setup, kept_sides
    mirror = mirror_setup(obj)
    sides = kept_sides(obj.data, mirror)
    return {axis: -1 if sides.get(local) == "-" else 1 for axis, local in zip("wdh", "XYZ")}


def name_region(name, region, selection, replace=True):
    from .mesh_ops import select
    from .instance import assert_ai_access
    assert_ai_access()
    obj = bpy.data.objects.get(name)
    if not region or obj is None or obj.type != "MESH":
        raise ValueError("provide a mesh and a nonempty region name")
    if any(group.name.casefold() == region.casefold() and group.name != region for group in obj.vertex_groups):
        raise ValueError("region names must be distinguishable without letter case")
    selected = select(name, selection)["verts"]
    ids = ensure_ids(obj.data)[0]
    wanted = {int(vid[1:]) for vid in selected}
    indices = [i for i, vid in enumerate(ids) if vid in wanted]
    group = obj.vertex_groups.get(region) or obj.vertex_groups.new(name=region)
    if replace and obj.data.vertices:
        group.remove(list(range(len(obj.data.vertices))))
    group.add(indices, 1.0, "REPLACE")
    from .sync import sync
    sync(name, render=False)
    return {"region": region, "verts": selected}
