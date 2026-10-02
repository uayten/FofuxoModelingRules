"""Neighbour area and opposite-edge spacing checks on cage and evaluated mesh."""

import bmesh

AREA_RATIO = 4.0
SPACING_RATIO = 3.0
EPSILON = 1e-16


def measure(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.index_update()
        areas = {face.index: face.calc_area() for face in bm.faces}
        area_pairs, spacing = [], []
        for edge in bm.edges:
            if len(edge.link_faces) == 2:
                a, b = (areas[face.index] for face in edge.link_faces)
                area_pairs.append(max(a, b) / max(min(a, b), EPSILON))
        for face in bm.faces:
            if len(face.verts) == 4:
                lengths = [(loop.link_loop_next.vert.co - loop.vert.co).length for loop in face.loops]
                spacing.extend(max(lengths[i], lengths[i + 2]) / max(min(lengths[i], lengths[i + 2]), EPSILON)
                               for i in (0, 1))
        return {"faces": len(bm.faces), "area_ratio_max": round(max(area_pairs, default=1), 3),
                "area_pairs_over": sum(ratio > AREA_RATIO for ratio in area_pairs),
                "spacing_ratio_max": round(max(spacing, default=1), 3),
                "spacing_pairs_over": sum(ratio > SPACING_RATIO for ratio in spacing),
                "degenerate_faces": sum(area <= EPSILON for area in areas.values())}
    finally:
        bm.free()


def check(obj, depsgraph):
    result = {"cage": measure(obj.data)}
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        result["result"] = measure(mesh)
    finally:
        evaluated.to_mesh_clear()
    issues = []
    for name, row in result.items():
        if row["area_pairs_over"] or row["spacing_pairs_over"] or row["degenerate_faces"]:
            issues.append({"level": "WARN", "code": f"{name}_evenness", "verts": [],
                           "msg": f"{name}: neighbour area ratio {row['area_ratio_max']:g}, "
                                  f"opposite-edge spacing ratio {row['spacing_ratio_max']:g}; inspect this region"})
    return result, issues
