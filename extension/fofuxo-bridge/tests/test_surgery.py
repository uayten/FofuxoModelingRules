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

    print("FAILURES", len(failures))
    if failures:
        raise SystemExit(1)


main()
