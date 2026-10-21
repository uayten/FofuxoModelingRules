"""Tests for the by-id surgery calls on a synthetic scene.

Run from the repository root:
    blender -b --factory-startup --python extension/fofuxo-bridge/tests/test_surgery.py --python-exit-code 1
"""

import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2]))

import llm_modeling_bridge as fc  # noqa: E402

fc.register()

failures = []


def check(condition, message):
    if condition:
        print("PASS", message)
    else:
        failures.append(message)
        print("FAIL", message)


def two_quads():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
    a = bpy.context.object
    a.name = "QuadA"
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(2.0, 0.0, 0.0))
    b = bpy.context.object
    b.name = "QuadB"
    bpy.ops.object.select_all(action="DESELECT")
    a.select_set(True)
    b.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.join()
    a.name = "Quads"
    from llm_modeling_bridge import mesh_io
    mesh_io.ensure_ids(a.data, write=True)
    return a


def two_grids(gap=1.0, segments=4, stacked=False):
    """Two grids side by side (or one above the other), joined into one object:
    borders of 4 * segments vertices, longer than any default id list used to be."""
    bpy.ops.wm.read_homefile(use_empty=True)
    made = []
    spots = ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)) if stacked else ((0.0, 0.0, 0.0), (2.0 + gap, 0.0, 0.0))
    for location in spots:
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=segments, y_subdivisions=segments, size=2.0,
                                        location=location)
        made.append(bpy.context.object)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in made:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = made[0]
    bpy.ops.object.join()
    made[0].name = "Grids"
    from llm_modeling_bridge import mesh_io
    mesh_io.ensure_ids(made[0].data, write=True)
    return made[0]


def ids_where(obj, test):
    attr = obj.data.attributes["llm_modeling_bridge_id"].data
    return [attr[v.index].value for v in obj.data.vertices if test(v.co)]


def raises(call):
    try:
        call()
    except ValueError:
        return True
    return False


def long_loops():
    obj = two_grids(stacked=True)
    report = fc.topology_report("Grids")
    loops = {loop["island"]: loop for loop in report["border_loops"]}
    check(all(loop["closed"] and loop["ids_truncated"] == 0 and len(loop["ids"]) == 16
              for loop in loops.values()), "report gives each 16-vertex border whole and closed")
    gappy = loops[0]["ids"][::2]
    check(raises(lambda: fc.bridge_loops("Grids", gappy, loops[1]["ids"], sync=False)),
          "bridge refuses ids that skip a vertex of the border")
    out = fc.bridge_loops("Grids", loops[0]["ids"], loops[1]["ids"], sync=False)
    check(out["bridged_faces"] == 16 and out["non_manifold"] == 0,
          f"bridge of two stacked 16-vertex loops makes 16 faces, manifold (made {out['bridged_faces']}, "
          f"non-manifold {out['non_manifold']})")


def open_runs():
    obj = two_grids()
    report = fc.topology_report("Grids")
    facing = []
    for island, x in ((0, 1.0), (1, 2.0)):
        loop = next(l for l in report["border_loops"] if l["island"] == island)
        side = set(ids_where(obj, lambda co, x=x: abs(co.x - x) < 1e-6))
        ids = loop["ids"]
        # the facing side as one run in walk order (rotate so it does not wrap)
        start = next(i for i, vid in enumerate(ids) if vid in side and ids[i - 1] not in side)
        facing.append([vid for vid in ids[start:] + ids[:start] if vid in side])
    out = fc.bridge_loops("Grids", facing[0], facing[1], sync=False)
    check(out["bridged_faces"] == 4, f"bridge of two open runs of 5 makes 4 faces (made {out['bridged_faces']})")


def cut_across():
    obj = two_grids()
    a = ids_where(obj, lambda co: abs(co.x + 1) < 1e-6 and abs(co.y + 1) < 1e-6)[0]
    b = ids_where(obj, lambda co: abs(co.x - 1) < 1e-6 and abs(co.y - 1) < 1e-6)[0]
    out = fc.cut_between("Grids", a, b, sync=False)
    check(out["new_edges"] >= 4 and out["new_faces"] >= 4,
          f"cut walks corner to corner across the grid (edges {out['new_edges']}, faces {out['new_faces']})")
    other = ids_where(obj, lambda co: co.x > 2.5)[0]
    check(raises(lambda: fc.cut_between("Grids", a, other, sync=False)), "cut refuses two islands")


def make_face_back():
    obj = two_grids()
    attr = obj.data.attributes["llm_modeling_bridge_id"].data
    poly = obj.data.polygons[5]
    ids = [attr[i].value for i in poly.vertices]
    normal = poly.normal.copy()
    faces = len(obj.data.polygons)
    fc.delete_faces("Grids", ids=ids, sync=False)
    # walk the hole the other way round: make_face must still match the neighbours
    out = fc.make_face("Grids", list(reversed(ids)), sync=False)
    attr = obj.data.attributes["llm_modeling_bridge_id"].data  # the mesh was rewritten
    made = next(p for p in obj.data.polygons
                if sorted(attr[i].value for i in p.vertices) == sorted(ids))
    check(len(obj.data.polygons) == faces and out["non_manifold"] == 0 and made.normal.dot(normal) > 0.99,
          "make_face fills the hole with the neighbours' winding")
    check(raises(lambda: fc.make_face("Grids", ids, sync=False)), "make_face refuses a face that exists")


def ring_cut():
    obj = two_grids()
    attr = obj.data.attributes["llm_modeling_bridge_id"].data
    a = ids_where(obj, lambda co: abs(co.x + 1) < 1e-6 and abs(co.y + 1) < 1e-6)[0]
    b = ids_where(obj, lambda co: abs(co.x + 0.5) < 1e-6 and abs(co.y + 1) < 1e-6)[0]
    faces = len(obj.data.polygons)
    out = fc.loop_cut("Grids", a, b, factor=0.25, sync=False)
    xs = {round(obj.data.vertices[i].co.x, 4) for i, v in enumerate(obj.data.attributes["llm_modeling_bridge_id"].data)
          if v.value in out["cut_ids"]}
    check(len(out["cut_ids"]) == 5 and len(obj.data.polygons) == faces + 4 and xs == {-0.875}
          and out["non_manifold"] == 0,
          f"loop_cut cuts the whole ring at the factor (ids {out['cut_ids']}, x {xs})")


def notch():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=2.0)
    obj = bpy.context.object
    obj.name = "Notch"
    from llm_modeling_bridge import mesh_io
    mesh_io.ensure_ids(obj.data, write=True)
    attr = obj.data.attributes["llm_modeling_bridge_id"].data
    center = next(attr[v.index].value for v in obj.data.vertices if v.co.length < 1e-6)
    corner = obj.data.polygons[0]
    fc.delete_faces("Notch", ids=[attr[i].value for i in corner.vertices], sync=False)
    out = fc.fill_notch("Notch", center, sync=False)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    inside = not any(v.is_boundary for v in bm.verts if v.co.length < 1e-6)
    bm.free()
    check(len(obj.data.polygons) == 4 and inside and out["non_manifold"] == 0,
          "fill_notch closes the wedge and the vertex ends inside")


def weld_seam():
    obj = two_grids(gap=0.0)
    left = ids_where(obj, lambda co: abs(co.x - 1) < 1e-6 and co.z == 0)
    attr = obj.data.attributes["llm_modeling_bridge_id"].data
    island0 = {attr[v.index].value for v in obj.data.vertices if v.co.x < 1.5 and v.index < 25}
    side_a = [vid for vid in left if vid in island0]
    side_b = [vid for vid in left if vid not in island0]
    check(len(side_a) == 5 and len(side_b) == 5, "the seam has five coincident pairs")
    check(raises(lambda: fc.weld_region("Grids", left, left, sync=False)), "weld_region refuses one set twice")
    out = fc.weld_region("Grids", side_a, side_b, threshold=1e-4, sync=False)
    report = fc.topology_report("Grids")
    check(len(out["pairs"]) == 5 and out["non_manifold"] == 0 and len(report["islands"]) == 1,
          f"weld_region closes the seam into one island ({len(out['pairs'])} pairs)")


def crossing_ids():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_plane_add(size=2.0)
    a = bpy.context.object
    bpy.ops.mesh.primitive_plane_add(size=2.0, rotation=(1.5708, 0.0, 0.0))
    b = bpy.context.object
    bpy.ops.object.select_all(action="DESELECT")
    a.select_set(True)
    b.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.join()
    a.name = "Cross"
    report = fc.topology_report("Cross")
    crossing = report["crossings"][0]
    check(crossing["face_pairs"] == 1 and len(crossing["ids_a"]) == 4 and len(crossing["ids_b"]) == 4,
          "report names the vertex ids of the faces that cross")
    from llm_modeling_bridge import mesh_io
    mesh_io.ensure_ids(a.data, write=True)
    out = fc.intersect("Cross", crossing["ids_a"][0], sync=False)
    report = fc.topology_report("Cross")
    check(len(report["islands"]) == 1 and out["non_manifold"] >= 1 and len(out["cut_ids"]) >= 2,
          f"intersect shares the cut line (islands {len(report['islands'])}, "
          f"4-face edges {out['non_manifold']}, cut ids {out['cut_ids']})")


def sidecars():
    import tempfile
    two_grids()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    names = sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH")
    folder = Path(tempfile.mkdtemp(prefix="sidecars_"))
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / "s.blend"))
    for name in names:
        fc.sync(name, render=False)
    root = folder / "s.bridge"
    foreign = root / "notes.txt"
    foreign.write_text("the modeler's own notes\n", "utf-8")
    check(all((root / f"{n}.txt").exists() and (root / ".state" / f"{n}.json").exists() for n in names),
          "sync writes a text and a state per object")
    out = fc.join_meshes(names, into=names[0])
    gone = names[1]
    check(f"{gone}.txt" in out["pruned"] and f".state/{gone}.json" in out["pruned"],
          f"join removes the joined object's text and state ({out['pruned']})")
    check((root / f"{names[0]}.txt").exists() and foreign.exists(),
          "the kept object's text and a file the bridge did not write stay")

    instance_mod = fc.instance_mod  # `fc.instance` is the function of that name
    obj = bpy.data.objects[names[0]]
    sig = instance_mod._object_signature(obj)
    copy = obj.copy()
    copy.data = obj.data.copy()
    check(instance_mod._object_signature(copy) == sig, "an untouched copy has the same signature")
    copy.data.edges[0].use_edge_sharp = True
    check(instance_mod._object_signature(copy) != sig, "a sharp mark changes the signature")


def fold_continues():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4, size=2.0)
    obj = bpy.context.object
    obj.name = "Fold"
    from llm_modeling_bridge import mesh_io
    mesh_io.ensure_ids(obj.data, write=True)
    row = sorted(ids_where(obj, lambda co: abs(co.y) < 1e-6),
                 key=lambda vid: next(v.co.x for v in obj.data.vertices
                                      if obj.data.attributes["llm_modeling_bridge_id"].data[v.index].value == vid))
    fc.mark_fold("Fold", row[:3], sync=False)  # from the border to the middle: it stops inside
    ends = fc.topology_report("Fold")["fold_ends"]
    check([e["id"] for e in ends] == [row[2]], f"report lists the fold that stops inside ({ends})")
    fc.mark_fold("Fold", row[2:], sync=False)
    check(fc.topology_report("Fold")["fold_ends"] == [], "a fold run on to the border leaves no end")


def edit_beside_triangle():
    """A triangle already accepted (D-080) does not block an op; a new one does."""
    import tempfile
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=3, y_subdivisions=3, size=2.0)
    obj = bpy.context.object
    obj.name = "Tri"
    obj.modifiers.new("Subdivision", "SUBSURF")
    from llm_modeling_bridge import mesh_io
    mesh_io.ensure_ids(obj.data, write=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(tempfile.mkdtemp(prefix="tri_")) / "t.blend"))
    corner = ids_where(obj, lambda co: abs(co.x + 1) < 1e-6 and abs(co.y + 1) < 1e-6)[0]
    beside = ids_where(obj, lambda co: abs(co.x + 1 / 3) < 1e-6 and abs(co.y + 1) < 1e-6)[0]
    fc.weld("Tri", corner, beside, at="b", sync=False)
    fc.sync("Tri", render=False)
    far = ids_where(obj, lambda co: abs(co.x - 1) < 1e-6 and abs(co.y - 1) < 1e-6)[0]
    r = fc.edit("Tri", f"mesh translate v{far} h=+1mm", render=False)
    check(r.get("action") != "error", f"an op beside an accepted triangle runs ({r.get('error')})")
    a = ids_where(obj, lambda co: abs(co.x - 1) < 1e-6 and abs(co.y + 1) < 1e-6)[0]
    b = ids_where(obj, lambda co: abs(co.x - 1 / 3) < 1e-6 and abs(co.y + 1) < 1e-6)[0]
    r = fc.edit("Tri", f"mesh merge v{a} v{b}", render=False)
    check(r.get("action") == "error" and "not quads" in r.get("error", ""), "an op that makes a new triangle is refused")


def main():
    obj = two_quads()
    report = fc.topology_report("Quads")
    check(len(report["islands"]) == 2, "report finds two islands")
    check(len(report["border_loops"]) == 2, "report finds two border loops")
    check(report["nearest"][0]["mm"] > 0, "report measures the nearest pair")
    check(report["nearest"][0]["a"] >= 0 and report["nearest"][0]["b"] >= 0, "report gives both ids")

    loops = {loop["island"]: loop["ids"] for loop in report["border_loops"]}
    before = len(obj.data.polygons)
    out = fc.bridge_loops("Quads", loops[0], loops[1], sync=False)
    check(out["bridged_faces"] == 4, f"bridge makes four faces (made {out['bridged_faces']})")
    check(len(obj.data.polygons) == before + 4, "face count grows by four")

    # Cut between two vertices of the same face that are not connected by an edge.
    mesh = obj.data
    quad = max(mesh.polygons, key=lambda p: len(p.vertices))
    ids = [mesh.attributes["llm_modeling_bridge_id"].data[i].value for i in quad.vertices]
    out = fc.cut_between("Quads", ids[0], ids[2], sync=False)
    check(out["new_faces"] >= 1, f"cut splits a face (new faces {out['new_faces']})")

    # Delete one face by ids.
    mesh = obj.data
    attr = mesh.attributes["llm_modeling_bridge_id"].data
    face = list(mesh.polygons[0].vertices)
    face_ids = [attr[i].value for i in face]
    faces_before = len(mesh.polygons)
    out = fc.delete_faces("Quads", ids=face_ids, sync=False)
    check(out.get("deleted") == 1, "delete removes exactly one face")
    check(len(obj.data.polygons) == faces_before - 1, "face count drops by one")

    # Weld two vertices.
    mesh = obj.data
    attr = mesh.attributes["llm_modeling_bridge_id"].data
    verts_before = len(mesh.vertices)
    a, b = attr[0].value, attr[1].value
    out = fc.weld("Quads", a, b, at="mid", sync=False)
    check(out["verts"] == verts_before - 1, "weld merges one vertex pair")
    left = {v.value for v in obj.data.attributes["llm_modeling_bridge_id"].data}
    check(b in left and a not in left, "weld keeps id_b and drops id_a")

    long_loops()
    open_runs()
    cut_across()
    make_face_back()
    ring_cut()
    notch()
    weld_seam()
    crossing_ids()
    sidecars()
    edit_beside_triangle()
    fold_continues()

    print("FAILURES", len(failures))
    if failures:
        raise SystemExit(1)


main()
