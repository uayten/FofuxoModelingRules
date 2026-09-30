"""Round-trip tests on a temporary copy of models/example/laco/human/Laço.blend.

Run from the repository root:
    blender -b --factory-startup --python extension/fofuxo_cage/tests/test_roundtrip.py --python-exit-code 1
"""

import faulthandler
import json
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
SOURCE = REPO / "models" / "example" / "laco" / "human" / "Laço.blend"
sys.path.insert(0, str(HERE.parents[2]))

import fofuxo_cage as fc  # noqa: E402

faulthandler.enable()  # a crash inside Blender prints the Python line that caused it

fc.register()  # operators and panel, as when Blender enables the extension
SYNC = sys.modules["fofuxo_cage.sync"]

failures = []


checks = []


def check(cond, what):
    checks.append(what)
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        failures.append(what)


def co_list(obj):
    return [tuple(v.co) for v in obj.data.vertices]


def untouched_signature(obj):
    """Everything sync must never change."""
    mods = [(m.name, m.type, tuple((p.identifier, str(getattr(m, p.identifier)))
                                   for p in m.bl_rna.properties if not p.is_readonly))
            for m in obj.modifiers]
    attrs = sorted((a.name, a.domain, a.data_type) for a in obj.data.attributes
                   if a.name != fc.mesh_io.ID_ATTR and not a.name.startswith("."))
    crease = obj.data.attributes.get("crease_edge")
    return {
        "mods": mods,
        "materials": [s.material.name if s.material else None for s in obj.material_slots],
        "parent": obj.parent.name if obj.parent else None,
        "matrix": [tuple(r) for r in obj.matrix_world],
        "attrs": attrs,
        "crease": [d.value for d in crease.data] if crease else None,
    }


def edit_text_line(path, vid, w=None, d=None, h=None):
    """Rewrite one vertex line the way an AI would: new numbers, loose spacing."""
    text = path.read_text("utf-8")
    pattern = re.compile(rf"^(\S*\s+)?v{vid}\s+(\S+)\s+(\S+)\s+(\S+).*$", re.M)
    m = pattern.search(text)
    assert m, f"v{vid} not found"
    vals = [w if w is not None else m[2], d if d is not None else m[3], h if h is not None else m[4]]
    new = f"{m[1] or ''}v{vid}  {vals[0]} {vals[1]} {vals[2]}"
    path.write_text(text[:m.start()] + new + text[m.end():], "utf-8")


def frame_of(obj):
    """The exact frame from the sync state."""
    return SYNC._load_state(SYNC.paths(obj)["state"])["frame"]


def near(values, co, frame, tol=0.5):
    """Text values (permille) match a position (m) within tol permille."""
    return all(abs(a - b) <= tol for a, b in zip(values, frame.to_values(co)))


def index_of(obj):
    """Vertex index of each stable id."""
    return {d.value: i for i, d in enumerate(obj.data.attributes[fc.mesh_io.ID_ATTR].data)}


def base_of(path, vid):
    return fc.cage_format.parse(path.read_text("utf-8")).verts[vid].base


def loop_cut(obj, start_pair):
    """Human-like loop cut: split the edge ring that starts at edge start_pair."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    a, b = (bm.verts[i] for i in start_pair)
    edge = next(e for e in a.link_edges if e.other_vert(a) is b or e.other_vert(a).index == b.index)
    ring, face_seen = [edge], set()
    cur = edge
    while True:
        faces = [f for f in cur.link_faces if f.index not in face_seen]
        if not faces:
            break
        f = faces[0]
        face_seen.add(f.index)
        loops = list(f.loops)
        k = next(i for i, lp in enumerate(loops) if lp.edge.index == cur.index)
        cur = loops[(k + 2) % 4].edge
        ring.append(cur)
    bmesh.ops.subdivide_edges(bm, edges=ring, cuts=1, use_grid_fill=True)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(ring)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="fofuxo_cage_"))
    blend = tmp / "Laço.blend"
    shutil.copy(SOURCE, blend)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    obj = bpy.data.objects["Laço"]
    sig = untouched_signature(obj)

    print("1. init")
    r = fc.sync("Laço")
    text_path = Path(r["text"])
    check(r["action"] == "init", f"action init ({r['action']})")
    check(text_path.exists(), "text written next to the .blend")
    fr = frame_of(obj)
    check([a.side for a in fr.axes] == ["-", "-", "+"], f"frame measured from the planes ({r['frame']})")
    cage = fc.cage_format.parse(text_path.read_text("utf-8"))
    check(len(cage.verts) == 28 and len(cage.faces) == 19, "28 verts, 19 faces")
    check(all(near(cage.verts[i].base, obj.data.vertices[i].co, fr) for i in range(28)),
          "base columns match the mesh within 0.5 permille")
    check(all(min(v.base) >= 0 for v in cage.verts.values()), "no negative values on the kept side")
    # The frame holds the whole evaluated mesh; base vertices land a bit inside it.
    top = max(max(v.sub) for v in cage.verts.values())
    check(950 <= top <= 1000, f"the default frame just holds the sub result (max sub {top})")
    check(abs(fr.to_local(cage.verts[7].sub)[2] * 1000 - 33.6) < 0.1, "v7 sub h = 33.6 mm")
    check("pole3" in cage.verts[10].flags, f"v10 flagged pole3 ({cage.verts[10].flags})")
    check(sum(len(ids) for _, ids in cage.groups) == 28, "every vertex listed once")
    check(fc.cage_format.parse(fc.cage_format.write(cage)) == cage, "parse(write(cage)) == cage")
    check(not [i for i in r["issues"] if i["level"] == "ERROR"], f"no ERROR on the original ({r['issues']})")
    sheet = bpy.data.images.load(r.get("render", ""), check_existing=False) if r.get("render") else None
    check(sheet is not None and tuple(sheet.size) == (3 * 480 + 12, 26 + 3 * 480 + 12),
          f"view sheet written ({r.get('render')}, {tuple(sheet.size) if sheet else None})")
    if sheet:
        bpy.data.images.remove(sheet)
    check(all(g.shape == (7, 5) for g in fc.font.GLYPHS.values()), "every glyph is 5x7")
    text0 = text_path.read_text("utf-8")

    print("2. nothing changed")
    before = co_list(obj)
    r = fc.sync("Laço")
    check(r["action"] == "unchanged", f"action unchanged ({r['action']})")
    check(text_path.read_text("utf-8") == text0, "text byte-identical")
    check(co_list(obj) == before, "mesh identical")

    print("2b. sub columns and the frame line are read-only")
    cage = fc.cage_format.parse(text0)
    cage.verts[5].sub = (0.0, 0.0, 0.0)
    cage.header["frame"] = "w X- 10.0   d Y- 10.0   h Z+ 10.0   (mm)"
    text_path.write_text(fc.cage_format.write(cage), "utf-8")
    r = fc.sync("Laço")
    codes = {i["code"] for i in r["issues"]}
    check(r["action"] == "unchanged" and {"sub_read_only", "frame_read_only"} <= codes,
          f"ignored with warnings ({r['action']}, {codes})")
    check(text_path.read_text("utf-8") == text0, "text restored")

    print("3. AI edits one line")
    edit_text_line(text_path, 7, h="1100")
    r = fc.sync("Laço")
    after = co_list(obj)
    check(r["action"] == "pushed" and r["moved"] == ["v7"], f"pushed v7 ({r['action']}, {r.get('moved')})")
    check(abs(after[7][2] - fr.axes[2].to_local(1100)) < 1e-7, "v7 z = 1.1 x the frame height in the mesh")
    check(all(after[i] == before[i] for i in range(28) if i != 7), "every other vertex bit-identical")
    check(base_of(text_path, 7)[2] == 1100, "text rewritten with v7 h 1100")

    print("4. human edits in Blender")
    obj.data.vertices[10].co.z += 0.002
    r = fc.sync("Laço")
    check(r["action"] == "pulled" and r["blender_edits"] == ["v10"], f"action pulled ({r['action']})")
    check(near(base_of(text_path, 10), obj.data.vertices[10].co, fr), "text shows the human's v10")
    expected = f"v10 h+{0.002 / fr.axes[2].extent * 100:.1f}%"
    check(r.get("blender_deltas") == [expected], f"human edit reported in percent ({r.get('blender_deltas')})")

    print("5. both edited: conflict")
    edit_text_line(text_path, 12, w="900")
    obj.data.vertices[13].co.x -= 0.001
    text_c, mesh_c = text_path.read_text("utf-8"), co_list(obj)
    r = fc.sync("Laço")
    check(r["action"] == "conflict", f"action conflict ({r['action']})")
    check(text_path.read_text("utf-8") == text_c and co_list(obj) == mesh_c, "nothing written")
    check(r["text_edits"] == ["v12"] and r["blender_edits"] == ["v13"], f"edits listed ({r})")
    check(not r["issues"], f"a line without sub columns raises no warning ({r['issues']})")

    print("6. resolve='mesh'")
    r = fc.sync("Laço", resolve="mesh")
    check(r["action"] == "pulled" and Path(r["rejected"]).exists(), "pulled, text edit saved aside")
    check(near(base_of(text_path, 12), obj.data.vertices[12].co, fr), "text follows the mesh")
    check(co_list(obj) == mesh_c, "mesh kept the human edit")

    print("7. vertex on a mirror plane stays on it")
    edit_text_line(text_path, 6, w="50")
    r = fc.sync("Laço")
    check(r["action"] == "pushed", f"pushed ({r['action']})")
    check(obj.data.vertices[6].co.x == 0.0, "v6 x stays 0")
    check(any(i["code"] == "kept_on_plane" for i in r["issues"]), "reported kept_on_plane")

    print("8. crossing a mirror plane is refused")
    before = co_list(obj)
    edit_text_line(text_path, 10, d="-100")
    r = fc.sync("Laço")
    check(r["action"] == "error" and any(i["code"] == "wrong_side" for i in r["issues"]), f"error wrong_side ({r})")
    check(co_list(obj) == before, "mesh unchanged")
    edit_text_line(text_path, 10, d=fc.cage_format.fmt_value(fr.to_values(obj.data.vertices[10].co)[1]))
    r = fc.sync("Laço")
    check(r["action"] in ("unchanged", "pushed"), f"recovered ({r['action']})")

    print("9a. an id of a removed vertex never comes back")
    tiny = bpy.data.meshes.new("tiny")
    tiny.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    tiny.attributes.new(fc.mesh_io.ID_ATTR, "INT", "POINT").data.foreach_set("value", [0, 5, 7])
    got, fresh = fc.mesh_io.ensure_ids(tiny, {0: (0, 0, 0), 5: (1, 0, 0)}, 8)
    check(got == [0, 5, 8] and fresh == [8], f"v7, removed at the last sync, comes back as v8 ({got})")
    bpy.data.meshes.remove(tiny)

    print("9. human loop cut")
    old = {i: tuple(v.co) for i, v in enumerate(obj.data.vertices)}
    n_ring = loop_cut(obj, (3, 22))
    r = fc.sync("Laço")
    cage = fc.cage_format.parse(text_path.read_text("utf-8"))
    check(r["action"] == "pulled", f"pulled ({r['action']})")
    check(len(cage.verts) == 28 + n_ring and len(cage.faces) == 19 + n_ring - 1,
          f"{len(cage.verts)} verts, {len(cage.faces)} faces")
    check(all(vid in cage.verts and near(cage.verts[vid].base, old[vid], fr) for vid in old),
          "original ids kept their positions")
    check(sorted(cage.verts)[-n_ring:] == list(range(28, 28 + n_ring)), "new vertices got fresh ids 28+")
    check(not [i for i in r["issues"] if i["level"] == "ERROR"], f"no ERROR after the cut ({r['issues']})")

    print("10. set_frame from the concept")
    before = co_list(obj)
    ids = [d.value for d in obj.data.attributes[fc.mesh_io.ID_ATTR].data]
    r = fc.set_frame("Laço", w=118.4, h=62.5)
    fr2 = frame_of(obj)
    check(r["action"] == "reframed" and r["frame"].startswith("w X- 59.2"), f"reframed ({r.get('frame')})")
    check(abs(fr2.axes[1].extent - fr.axes[1].extent) < 1e-12, "depth kept")
    check(co_list(obj) == before, "mesh unchanged")
    cage = fc.cage_format.parse(text_path.read_text("utf-8"))
    check(all(near(cage.verts[vid].base, obj.data.vertices[i].co, fr2) for i, vid in enumerate(ids)),
          "values re-measured in the new frame")
    r = fc.sync("Laço")
    check(r["action"] == "unchanged", f"next sync unchanged ({r['action']})")

    print("10b. set_frame from a box found in the concept")
    color = fc.sample("EUA-Frente.png", 560, 750)
    found = fc.find_box("EUA-Frente.png", color, tol=0.25, roi=[480, 760, 650, 850])
    check(found is not None and found["box"][:2] == [528, 722], f"bow found in the concept ({found})")
    r = fc.set_frame("Laço", concept={"image": "EUA-Frente.png", "box": found["box"]})
    check(r["action"] == "reframed" and r["frame"].startswith("w X- 59.2"), f"frame from the box ({r['frame']})")
    check(SYNC._load_state(SYNC.paths(obj)["state"])["concept"]["box"] == found["box"], "concept box kept in the state")
    fr = frame_of(obj)

    print("10c. relative ops")
    cage = fc.cage_format.parse(text_path.read_text("utf-8"))
    loop = cage.groups[0][1]
    idx = index_of(obj)
    old = {vid: tuple(obj.data.vertices[i].co) for vid, i in idx.items()}
    text = text_path.read_text("utf-8").replace("\nops\n", "\nops\n  move L1 h +4%\n")
    text_path.write_text(text, "utf-8")
    r = fc.sync("Laço")
    moved_h = [vid for vid in loop if abs(old[vid][2]) >= 1e-6]
    check(r["action"] == "pushed" and r.get("ops") == [f"move L1 h +4%  ({len(loop)} verts)"], f"op applied ({r.get('ops')})")
    check(all(abs(obj.data.vertices[idx[vid]].co.z - old[vid][2] - fr.axes[2].extent * 0.04) < 1e-7
              for vid in moved_h), "L1 moved up 4% of the frame height")
    check(all(obj.data.vertices[idx[vid]].co.z == 0.0 for vid in loop if vid not in moved_h),
          "Z-plane vertices stayed on it")
    check(all(d.endswith("h+4.0%") for d in r["deltas"]), f"deltas in percent ({r['deltas'][:3]})")
    check(not fc.cage_format.parse(text_path.read_text("utf-8")).ops, "ops section cleared")

    print("10d. a bad op writes nothing")
    before = co_list(obj)
    text_path.write_text(text_path.read_text("utf-8").replace("\nops\n", "\nops\n  move L99 h +4%\n"), "utf-8")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "L99" in r["error"], f"refused ({r.get('error')})")
    check(co_list(obj) == before, "mesh unchanged")
    text_path.write_text(text_path.read_text("utf-8").replace("  move L99 h +4%\n", ""), "utf-8")

    print("10e. scale from the mirror plane")
    old = {i: tuple(v.co) for i, v in enumerate(obj.data.vertices)}
    text_path.write_text(text_path.read_text("utf-8").replace("\nops\n", "\nops\n  scale all w 50% from 0\n"), "utf-8")
    r = fc.sync("Laço")
    check(r["action"] == "pushed", f"pushed ({r['action']})")
    check(all(abs(obj.data.vertices[i].co.x - old[i][0] / 2) < 1e-7 for i in old), "every x halved around the plane")

    print("10f. target: solve the base so the sub lands on a value")
    cage = fc.cage_format.parse(text_path.read_text("utf-8"))
    free = next(v for v in cage.verts.values() if not v.flags and v.sub is not None)
    goal_w, goal_d = free.sub[0] + 30, free.sub[1] - 20
    text_path.write_text(text_path.read_text("utf-8").replace(
        "\nops\n", f"\nops\n  target v{free.id} w {goal_w:.0f} d {goal_d:.0f}\n"), "utf-8")
    r = fc.sync("Laço")
    got = fc.cage_format.parse(text_path.read_text("utf-8")).verts[free.id]
    check(r["action"] == "pushed" and any(o.startswith(f"target v{free.id}") for o in r.get("ops", [])),
          f"target applied ({r.get('ops')})")
    check(abs(got.sub[0] - round(goal_w)) <= 1 and abs(got.sub[1] - round(goal_d)) <= 1,
          f"sub landed on the target ({got.sub[:2]} vs {goal_w:.0f}, {goal_d:.0f})")
    on_z = next(v for v in cage.verts.values() if "Z" in v.flags)
    before = co_list(obj)
    text_path.write_text(text_path.read_text("utf-8").replace("\nops\n", f"\nops\n  target v{on_z.id} h 50\n"), "utf-8")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "mirror plane" in r["error"], f"target across a plane refused ({r.get('error')})")
    check(co_list(obj) == before, "mesh unchanged")
    text_path.write_text(text_path.read_text("utf-8").replace(f"  target v{on_z.id} h 50\n", ""), "utf-8")

    print("11. stack, material, parent and attributes untouched")
    now = untouched_signature(obj)
    for key in ("mods", "materials", "parent", "matrix", "attrs"):
        check(now[key] == sig[key], f"{key} unchanged")

    print("11b. object ops: set a modifier, crease edges")
    sub_mod = next(m for m in obj.modifiers if m.type == "SUBSURF")
    text_path.write_text(text_path.read_text("utf-8").replace(
        "\nops\n", f"\nops\n  set {sub_mod.name} render_levels 3\n  crease plane-x 0.5\n"), "utf-8")
    r = fc.sync("Laço")
    check(r["action"] == "pushed" and sub_mod.render_levels == 3, f"render_levels set ({r.get('ops')})")
    edges = fc.cage_format.parse(text_path.read_text("utf-8")).edges
    check(any(line.startswith("crease 0.5") for line in edges), f"X-plane edges creased 0.5 ({edges})")
    before = co_list(obj)
    text_path.write_text(text_path.read_text("utf-8").replace("\nops\n", "\nops\n  set Subdivision no_such_prop 1\n"), "utf-8")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "no_such_prop" in r["error"] and co_list(obj) == before, f"bad set refused ({r.get('error')})")
    text_path.write_text(text_path.read_text("utf-8").replace("  set Subdivision no_such_prop 1\n", ""), "utf-8")

    print("11c2. modifier settings: shown in the text, set with units")

    def add_ops(*lines):
        text_path.write_text(text_path.read_text("utf-8").replace(
            "\nops\n", "\nops\n" + "".join(f"  {line}\n" for line in lines)), "utf-8")

    cage = fc.cage_format.parse(text_path.read_text("utf-8"))
    mirror_mod = next(m for m in obj.modifiers if m.type == "MIRROR")
    check(any(line.startswith(f"{mirror_mod.name} (MIRROR)  -> v ") for line in cage.modifiers),
          f"modifiers section with the effect ({cage.modifiers[:1]})")
    add_ops(f"set {mirror_mod.name} merge_threshold 0.05mm")
    r = fc.sync("Laço")
    check(r["action"] == "pushed" and abs(mirror_mod.merge_threshold - 0.00005) < 1e-9,
          f"merge_threshold set in mm ({mirror_mod.merge_threshold})")
    check(any("merge_threshold 0.05mm" in line for line in r["modifiers"]), "the text shows the new value")
    check(any("merge_threshold 0.05mm" in line for line in r.get("stack_changes", [])), "reported as a stack change")
    before = co_list(obj)
    add_ops(f"set {mirror_mod.name} merge_threshold 0.001")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "unit" in r["error"] and co_list(obj) == before,
          f"a length without a unit refused ({r.get('error')})")
    text_path.write_text(text_path.read_text("utf-8").replace(
        f"  set {mirror_mod.name} merge_threshold 0.001\n", ""), "utf-8")
    add_ops(f"set {mirror_mod.name} use_axis XY")
    fc.sync("Laço")
    check(list(mirror_mod.use_axis) == [True, True, False], f"axis flags set from letters ({list(mirror_mod.use_axis)})")
    add_ops(f"set {mirror_mod.name} use_axis XYZ")
    fc.sync("Laço")
    check(list(mirror_mod.use_axis) == [True, True, True], "axis flags restored")

    print("11c3. lock and unlock")
    was = obj.hide_select
    st = fc.lock("Laço")
    check(st["locked"] == ["Laço"] and obj.hide_select, f"locked ({st})")
    r = fc.sync("Laço")
    check(r["action"] in ("unchanged", "pulled"), f"sync works while locked ({r['action']})")
    st = fc.unlock()
    check(not st["locked"] and obj.hide_select == was and "fofuxo_cage_lock" not in obj,
          "unlocked, selectability restored")
    fc.lock("Laço")
    bpy.ops.fofuxo_cage.unlock()  # the human's button
    r = fc.sync("Laço")
    check(any(i["code"] == "human_took_over" for i in r["issues"]), "the next sync reports the take-over")
    r = fc.sync("Laço")
    check(not any(i["code"] == "human_took_over" for i in r["issues"]), "reported once")

    print("11c4. flip to the other side of a mirror plane")
    before_vals = {vid: v.base for vid, v in fc.cage_format.parse(text_path.read_text("utf-8")).verts.items()}
    size_before = fc.sync("Laço")["size"]
    old_y = {i: v.co.y for i, v in enumerate(obj.data.vertices)}
    r = fc.flip("Laço", "d")
    check(r["action"] == "flipped" and "d Y+" in r["frame"], f"flipped to +Y ({r.get('frame')})")
    check(all(abs(obj.data.vertices[i].co.y + y) < 1e-9 for i, y in old_y.items()), "every y negated")
    after_vals = {vid: v.base for vid, v in fc.cage_format.parse(text_path.read_text("utf-8")).verts.items()}
    check(after_vals == before_vals, "text values unchanged")
    check(r["size"] == size_before, f"same evaluated size ({r['size']})")
    check(any(i["code"] == "modeled_behind" for i in fc.sync("Laço")["issues"]), "+Y warns: modeled behind")
    r = fc.flip("Laço", "d")
    check("d Y-" in r["frame"] and fc.sync("Laço")["action"] == "unchanged", "flipped back to -Y, in sync")

    print("11d. stack ops: add, reorder, set, remove; a bad batch changes nothing")
    stack0 = [m.name for m in obj.modifiers]
    batch = ("  add BEVEL as Edge at first\n  set Edge width 1mm\n  add WEIGHTED_NORMAL\n"
             "  reorder WeightedNormal to after Edge\n")
    text_path.write_text(text_path.read_text("utf-8").replace("\nops\n", "\nops\n" + batch), "utf-8")
    r = fc.sync("Laço")
    names = [m.name for m in obj.modifiers]
    check(r["action"] == "pushed" and names == ["Edge", "WeightedNormal"] + stack0, f"stack {names} ({r.get('ops')})")
    check(abs(obj.modifiers["Edge"].width - 0.001) < 1e-9, "Edge width set on the new modifier")
    check("sub unavailable" in r["count"], f"sub column off with Bevel in the stack ({r['count']})")
    text_path.write_text(text_path.read_text("utf-8").replace(
        "\nops\n", "\nops\n  remove Edge\n  remove Nope\n"), "utf-8")
    r = fc.sync("Laço")
    check(r["action"] == "error" and [m.name for m in obj.modifiers] == names, f"bad batch refused ({r.get('error')})")
    text_path.write_text(text_path.read_text("utf-8").replace("  remove Nope\n", "  remove WeightedNormal\n"), "utf-8")
    r = fc.sync("Laço")
    check([m.name for m in obj.modifiers] == stack0, f"back to the original stack ({[m.name for m in obj.modifiers]})")

    print("11c. views from any angle")
    v = fc.views("Laço", [(45, 30), "top", "-45,-20"])
    img = bpy.data.images.load(v["render"], check_existing=False)
    check(tuple(img.size) == (2 * 480 + 6, 26 + 3 * 480 + 12), f"3 views x 2 panels ({tuple(img.size)})")
    bpy.data.images.remove(img)

    print("11e. topology ops: cut a loop, dissolve it again")
    n0, f0 = len(obj.data.vertices), len(obj.data.polygons)
    cage = fc.cage_format.parse(text_path.read_text("utf-8"))
    a, b = next((f[0], f[1]) for f in cage.faces)
    add_ops(f"cut v{a}-v{b}")
    r = fc.sync("Laço")
    n1 = len(obj.data.vertices)
    check(r["action"] == "pushed" and n1 > n0 and all(len(p.vertices) == 4 for p in obj.data.polygons),
          f"cut added {n1 - n0} vertices, all quads ({r.get('ops')})")
    new_ids = set(fc.cage_format.parse(text_path.read_text("utf-8")).verts) - set(cage.verts)
    check(len(new_ids) == n1 - n0, f"new vertices got fresh ids ({sorted(new_ids)})")
    idx = index_of(obj)
    sharp = obj.data.attributes.get("sharp_edge") or obj.data.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
    new_idx = {idx[v] for v in new_ids}
    for e in obj.data.edges:
        sharp.data[e.index].value = e.vertices[0] in new_idx and e.vertices[1] in new_idx
    r = fc.sync("Laço")  # marking sharp moves nothing
    add_ops("dissolve sharp")
    r = fc.sync("Laço")
    check(r["action"] == "pushed" and len(obj.data.vertices) == n0 and len(obj.data.polygons) == f0,
          f"the marked loop dissolved back to {n0} vertices ({r.get('ops')})")
    before = co_list(obj)
    add_ops(f"dissolve v{a}-v{b}")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "quads" in r["error"] and co_list(obj) == before,
          f"a dissolve that leaves n-gons refused ({r.get('error')})")
    text_path.write_text(text_path.read_text("utf-8").replace(f"  dissolve v{a}-v{b}\n", ""), "utf-8")

    print("11g. the mesh op: Blender's operators on a selection by id")

    def drop_ops():
        text = text_path.read_text("utf-8")
        head, _, tail = text.partition("\nops\n")
        rest = tail.split("\n")
        while rest and rest[0].startswith("  "):
            rest.pop(0)
        text_path.write_text(head + "\nops\n" + "\n".join(rest), "utf-8")

    looptools = fc.ensure_looptools()
    check(looptools["looptools"].startswith(("enabled", "installed")) and "looptools_circle" in dir(bpy.ops.mesh),
          f"LoopTools ready ({looptools})")
    before = co_list(obj)
    add_ops(f"mesh no_such_op v{a}")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "dissolve_edges" in r["error"] and co_list(obj) == before,
          f"unknown operator refused with the list ({r.get('error', '')[:90]})")
    drop_ops()
    add_ops(f"mesh vertices_smooth v{a} strength=2")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "factor" in r["error"], f"unknown parameter refused ({r.get('error')})")
    drop_ops()
    add_ops(f"mesh vertices_smooth v{a} factor=3")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "0 to 1" in r["error"], f"a factor out of range refused ({r.get('error')})")
    drop_ops()
    seam = obj.data.attributes.get("uv_seam") or obj.data.attributes.new("uv_seam", "BOOLEAN", "EDGE")
    seam.data.foreach_set("value", [False] * len(obj.data.edges))  # the example came with UV seams
    add_ops("mesh dissolve_edges seam")
    r = fc.sync("Laço")
    check(r["action"] == "error" and "seam" in r["error"], f"no seam marked: refused ({r.get('error')})")
    drop_ops()

    ts = bpy.context.tool_settings
    mode0, active0, hide0 = tuple(ts.mesh_select_mode), bpy.context.view_layer.objects.active, obj.hide_select
    loop = fc.select("Laço", f"loop v{a}-v{b}")
    ring = fc.select("Laço", f"ring v{a}-v{b}")
    check(len(loop["edges"]) >= 2 and f"v{min(a, b)}-v{max(a, b)}" in loop["edges"],
          f"loop walker through the edge ({loop['edges']})")
    check(len(ring["edges"]) >= 2 and not set(ring["edges"]) & (set(loop["edges"]) - {f"v{min(a, b)}-v{max(a, b)}"}),
          f"ring walker across it ({ring['edges']})")
    far = loop["verts"][-1] if loop["verts"][-1] != f"v{a}" else loop["verts"][0]
    path = fc.select("Laço", f"path v{a} {far}")
    check(f"v{a}" in path["verts"] and far in path["verts"] and len(path["edges"]) >= 1,
          f"path from v{a} to {far} ({path['edges']})")
    face = fc.select("Laço", "faces " + " ".join(f"v{v}" for v in cage.faces[0]))
    check(len(face.get("faces", [])) == 1, f"a face by its vertices ({face.get('faces')})")
    check(tuple(ts.mesh_select_mode) == mode0 and bpy.context.view_layer.objects.active == active0
          and obj.hide_select == hide0 and obj.mode == "OBJECT" and "fofuxo_cage_lock" not in obj,
          "select left no trace: mode, active object, lock, select mode")

    n0, f0 = len(obj.data.vertices), len(obj.data.polygons)
    known = set(fc.cage_format.parse(text_path.read_text("utf-8")).verts)
    add_ops(f"mesh loopcut_slide ring v{a}-v{b} number_cuts=2")
    r = fc.sync("Laço")
    n1 = len(obj.data.vertices)
    note = (r.get("ops") or [""])[0]
    check(r["action"] == "pushed" and n1 == n0 + 2 * len(ring["edges"]) and f"+{n1 - n0} v" in note
          and "all quads" in note, f"loopcut_slide: 2 loops across the ring ({note})")
    ids_now = fc.cage_format.parse(text_path.read_text("utf-8")).verts
    new_ids = set(ids_now) - known
    check(len(new_ids) == n1 - n0 and min(new_ids) > max(known), f"the new vertices got fresh ids ({sorted(new_ids)})")
    check(fc.sync("Laço")["action"] == "unchanged", "the next sync is unchanged")
    idx = index_of(obj)
    seam = obj.data.attributes.get("uv_seam") or obj.data.attributes.new("uv_seam", "BOOLEAN", "EDGE")
    new_idx = {idx[v] for v in new_ids}
    vs = obj.data.vertices
    links = {}
    for e in obj.data.edges:
        links.setdefault(e.vertices[0], []).append(e.vertices[1])
        links.setdefault(e.vertices[1], []).append(e.vertices[0])

    def rung(i, j):
        # The edge between the two cuts runs along an old ring edge: in line
        # with the old vertex next to one of its ends.
        for p, q in ((i, j), (j, i)):
            for o in links[p]:
                if o not in new_idx:
                    u, w = (vs[p].co - vs[o].co).normalized(), (vs[q].co - vs[p].co).normalized()
                    if u.dot(w) > 0.999:
                        return True
        return False

    for e in obj.data.edges:
        i, j = e.vertices
        seam.data[e.index].value = i in new_idx and j in new_idx and not rung(i, j)
    fc.sync("Laço")
    r = fc.edit("Laço", "mesh dissolve_edges seam")
    check(r["action"] == "pushed" and len(obj.data.vertices) == n0 and len(obj.data.polygons) == f0,
          f"edit(): the seam loops dissolved back to {n0} vertices ({r.get('ops') or r.get('error')})")

    free = [i for i, v in enumerate(obj.data.vertices) if min(abs(c) for c in v.co) > 1e-4]
    ids_list = [d.value for d in obj.data.attributes[fc.mesh_io.ID_ATTR].data]
    pick = free[0]
    nbr = next(e.vertices[1] if e.vertices[0] == pick else e.vertices[0] for e in obj.data.edges if pick in e.vertices)
    on_plane = [i for i, v in enumerate(obj.data.vertices) if abs(v.co.y) < 1e-6]
    fr = frame_of(obj)
    shape0 = co_list(obj)
    d0 = {i: fr.to_values(obj.data.vertices[i].co)[1] for i in (pick, nbr)}
    r = fc.edit("Laço", f"mesh translate v{ids_list[pick]} d=+2% falloff=smooth radius=40%")
    d1 = {i: fr.to_values(obj.data.vertices[i].co)[1] for i in (pick, nbr)}
    note = (r.get("ops") or [""])[0]
    check(r["action"] == "pushed" and abs(d1[pick] - d0[pick] - 20) < 0.01,
          f"translate: the vertex moves d +2% ({d1[pick] - d0[pick]:.2f} permille; {note or r.get('error')})")
    check(0 < abs(d1[nbr] - d0[nbr]) < 20, f"proportional editing: a neighbour follows less ({d1[nbr] - d0[nbr]:.2f})")
    check(all(abs(obj.data.vertices[i].co.y) < 1e-6 for i in on_plane), "vertices on the Y plane stay on it")
    check("surface moved: max" in note and f"v{ids_list[pick]} d+2.0%" in note, "reported: deviation and deltas")
    before = co_list(obj)
    r = fc.edit("Laço", f"mesh vertices_smooth v{ids_list[pick]} factor=0.5 repeat=2")
    check(r["action"] == "pushed" and co_list(obj) != before and "moved 1 v" in r["ops"][0],
          f"vertices_smooth ({r['ops'][0]})")
    print("11h. shaping ops (Phase 2)")
    fa, fb = next((ids_list[e.vertices[0]], ids_list[e.vertices[1]]) for e in obj.data.edges
                  if e.vertices[0] in free and e.vertices[1] in free)
    quad = next(p for p in obj.data.polygons if all(i in free for i in p.vertices))
    quad_ids = " ".join(f"v{ids_list[i]}" for i in quad.vertices)
    for line in (f"mesh edge_slide loop v{fa}-v{fb} factor=0.2",
                 f"mesh vert_slide v{ids_list[pick]} factor=0.2",
                 f"mesh shrink_fatten faces {quad_ids} value=1%",
                 f"mesh push_pull faces {quad_ids} value=0.3mm",
                 f"mesh tosphere faces {quad_ids} factor=0.5 falloff=smooth radius=20%",
                 f"mesh looptools_relax loop v{fa}-v{fb} iterations=3",
                 f"mesh looptools_space loop v{fa}-v{fb}"):
        r = fc.edit("Laço", line)
        note = (r.get("ops") or [""])[0]
        check(r["action"] == "pushed" and "moved" in note and "surface moved" in note,
              f"{line.split()[1]} ({note.split('(', 1)[-1][:110] if note else r.get('error')})")
        for v, co in zip(obj.data.vertices, shape0):
            v.co = co
        obj.data.update()
        fc.sync("Laço")
    r = fc.edit("Laço", "mesh translate all h=+3%")
    check("profile front +" in r["ops"][0] or "profile side +" in r["ops"][0], f"the profiles' change reported ({r['ops'][0][-90:]})")
    r = fc.edit("Laço", "mesh symmetrize all direction=negative_x")
    check(r["action"] == "error" and "mirror plane" in r["error"]
          and not fc.cage_format.parse(text_path.read_text("utf-8")).ops,
          f"symmetrize on a mirrored half refused, the text left clean ({r.get('error', '')[:80]})")

    print("11i. the task's targets and poly budget")
    target_md = Path(bpy.data.filepath).parent / "target.md"
    n_faces = len(obj.data.polygons)
    target_md.write_text("# Target\n\n```targets\n"
                         f"Laço       faces              {n_faces - 5}  +20%  the modeler's wing\n"
                         f"Laço       verts              {len(obj.data.vertices)}  +20%\n"
                         "Laço       size w             63mm   5%    half the modeler's width (10e)\n"
                         "Laço       section w 0.3 n    3.0    0.8\n"
                         "Laço       profile top 0.75   99mm   1mm   far off on purpose\n"
                         "\"Laço Nó\"  faces              5      +20%\n```\n", "utf-8")
    r = fc.sync("Laço")
    budget = [i for i in r["issues"] if i["code"] == "poly_budget"]
    check(len(budget) == 1 and f"{n_faces} faces, over the target" in budget[0]["msg"],
          f"the sync warns past the face budget ({budget[0]['msg'] if budget else r['issues']})")
    tg = fc.check_targets("Laço")
    check(tg["in"] == 3 and tg["out"] == 2 and tg["results"][-1].startswith("OUT Laço profile top 0.75"),
          f"targets measured: {tg['in']} in, {tg['out']} out ({tg['results'][2]})")
    target_md.unlink()
    check(not [i for i in fc.sync("Laço")["issues"] if i["code"] == "poly_budget"], "no target.md, no budget")

    print("11j. the rest of the topology tools (Phase 1)")
    faces0 = sorted(tuple(sorted(ids_list[i] for i in p.vertices)) for p in obj.data.polygons)
    edges0 = {tuple(sorted((ids_list[a], ids_list[b]))) for a, b in (e.vertices for e in obj.data.edges)}
    inner = next(e for e in obj.data.edges if e.vertices[0] in free and e.vertices[1] in free
                 and sum(1 for p in obj.data.polygons if e.key in p.edge_keys) == 2)
    ea, eb = ids_list[inner.vertices[0]], ids_list[inner.vertices[1]]
    r = fc.edit("Laço", f"mesh edge_rotate v{ea}-v{eb}")
    check(r["action"] == "pushed" and "all quads" in r["ops"][0], f"edge_rotate keeps quads ({r['ops'][0][:90]})")
    after_rotate = sorted(tuple(sorted(ids_list[i] for i in p.vertices)) for p in obj.data.polygons)
    check(after_rotate != faces0 and len(after_rotate) == len(faces0), "the faces around it changed")
    edge_ids = lambda: {tuple(sorted((ids_list[a], ids_list[b]))) for a, b in (e.vertices for e in obj.data.edges)}
    turned = next(iter(edge_ids() - edges0))
    r = fc.edit("Laço", f"mesh edge_rotate v{turned[0]}-v{turned[1]} use_ccw=on")
    back = sorted(tuple(sorted(ids_list[i] for i in p.vertices)) for p in obj.data.polygons)
    check(r["action"] == "pushed" and back == faces0, "turned back counter-clockwise: the same faces again")
    quad_verts = quad_ids.split()  # ids, not the polygon: a topology change frees Blender's arrays
    r = fc.edit("Laço", f"mesh delete faces {' '.join(quad_verts)}")
    check(r["action"] == "pushed" and len(obj.data.polygons) == len(faces0) - 1
          and any(i["code"] == "open_edge" for i in r["issues"]), f"delete leaves a hole, warned ({r['ops'][0][:70]})")
    r = fc.edit("Laço", f"mesh edge_face_add {' '.join(quad_verts)}")
    check(r["action"] == "pushed" and len(obj.data.polygons) == len(faces0), "edge_face_add closes it")
    for line in ("mesh remove_doubles all threshold=0.01mm", "mesh tris_convert_to_quads all",
                 "mesh dissolve_limited all angle_limit=0.5deg delimit=seam,sharp"):
        r = fc.edit("Laço", line)
        check(r["action"] == "pushed" and "nothing changed" in r["ops"][0], f"{line.split()[1]}: nothing to do here")
    for line in (f"mesh edge_collapse v{ea}-v{eb}", f"mesh merge v{ea} v{eb}", "mesh unsubdivide all",
                 f"mesh offset_edge_loops_slide loop v{fa}-v{fb}"):
        before = co_list(obj)
        r = fc.edit("Laço", line)
        ok = (r["action"] == "error" and "quads" in r["error"] and co_list(obj) == before) or \
             (r["action"] == "pushed" and all(len(p.vertices) == 4 for p in obj.data.polygons))
        check(ok, f"{line.split()[1]}: never leaves anything but quads ({r['action']}: "
                  f"{(r.get('error') or r['ops'][0])[:80]})")
        if r["action"] == "pushed":
            check(False, f"{line.split()[1]} changed the cage; the later checks need it back")
    r = fc.edit("Laço", "mesh dissolve_limited all angle_limit=5")
    check(r["action"] == "error" and "angle" in r["error"], f"an angle needs a unit ({r.get('error')})")

    # bridge and fill on a plain grid: a row of faces deleted, then closed again
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4, size=0.04, location=(0, 0, 0.3))
    grid = bpy.context.active_object
    grid.name = "Grid"
    fc.sync("Grid")
    gids = [d.value for d in grid.data.attributes[fc.mesh_io.ID_ATTR].data]
    ys = sorted({round(v.co.y, 6) for v in grid.data.vertices})
    row = lambda y: sorted((v for v in grid.data.vertices if round(v.co.y, 6) == y), key=lambda v: v.co.x)
    r1, r2 = row(ys[1]), row(ys[2])
    strip = "faces " + " ".join(f"v{gids[v.index]}" for v in r1 + r2)
    edges = " ".join(f"v{gids[a.index]}-v{gids[b.index]}" for r_ in (r1, r2) for a, b in zip(r_, r_[1:]))
    gf0 = len(grid.data.polygons)
    l2 = f"loop v{gids[row(ys[2])[1].index]}-v{gids[row(ys[2])[2].index]}"
    across = [f"ring v{gids[row(ys[j])[1].index]}-v{gids[row(ys[j + 1])[1].index]}" for j in (1, 2)]
    even = [tuple(v.co) for v in grid.data.vertices]
    fc.edit("Grid", f"mesh translate {l2} d=+3mm")
    r = fc.edit("Grid", f"mesh space_edge_loops_evenly {' '.join(across)}")
    check(r["action"] == "pushed" and all((Vector(a) - v.co).length < 1e-6 for a, v in zip(even, grid.data.vertices)),
          f"space_edge_loops_evenly puts a moved row back ({(r.get('ops') or [r.get('error')])[0][:70]})")
    rd = fc.edit("Grid", f"mesh delete {strip}")
    holes = len(grid.data.polygons)
    r = fc.edit("Grid", f"mesh bridge_edge_loops {edges}")
    check(r["action"] == "pushed" and len(grid.data.polygons) == gf0 and holes < gf0
          and all(len(p.vertices) == 4 for p in grid.data.polygons),
          f"bridge_edge_loops closes a deleted row ({holes} -> {len(grid.data.polygons)} faces)")
    # fill_grid needs a closed border: a 2 x 2 block in the middle, its center vertex goes with it
    by_pos = {(round(v.co.x, 6), round(v.co.y, 6)): gids[v.index] for v in grid.data.vertices}
    xs = sorted({k[0] for k in by_pos})
    ring = [(1, 1), (2, 1), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3), (1, 2)]
    ring_ids = [by_pos[(xs[i], ys[j])] for i, j in ring]
    block = "faces " + " ".join(f"v{v}" for v in ring_ids + [by_pos[(xs[2], ys[2])]])
    border = " ".join(f"v{a}-v{b}" for a, b in zip(ring_ids, ring_ids[1:] + ring_ids[:1]))
    rd = fc.edit("Grid", f"mesh delete {block}")
    holes, nv = len(grid.data.polygons), len(grid.data.vertices)
    r = fc.edit("Grid", f"mesh fill_grid {border}")
    check(r["action"] == "pushed" and holes == gf0 - 4 and len(grid.data.polygons) == gf0
          and all(len(p.vertices) == 4 for p in grid.data.polygons),
          f"fill_grid closes a deleted block ({holes} -> {len(grid.data.polygons)} faces, "
          f"{nv} -> {len(grid.data.vertices)} verts; {rd.get('error') or ''}{r.get('error') or ''})")
    nv, nf = len(grid.data.vertices), len(grid.data.polygons)
    r = fc.edit("Grid", f"mesh subdivide_edgering ring v{by_pos[(xs[0], ys[0])]}-v{by_pos[(xs[1], ys[0])]}")
    check(r["action"] == "pushed" and len(grid.data.vertices) == nv + 5 and len(grid.data.polygons) == nf + 4
          and all(len(p.vertices) == 4 for p in grid.data.polygons),
          f"subdivide_edgering cuts a column of quads ({(r.get('ops') or [r.get('error')])[0][:70]})")
    bpy.data.objects.remove(grid)

    print("11k. the modeler points: marks and annotations")
    fc.sync("Laço")
    # Blender drops the seam attribute when no edge has one left
    seam = obj.data.attributes.get("uv_seam") or obj.data.attributes.new("uv_seam", "BOOLEAN", "EDGE")
    pair_edges = [e for e in obj.data.edges if e.vertices[0] in free and e.vertices[1] in free][:2]
    names = sorted(f"v{min(ids_list[e.vertices[0]], ids_list[e.vertices[1]])}-v{max(ids_list[e.vertices[0]], ids_list[e.vertices[1]])}"
                   for e in pair_edges)
    for e in pair_edges:
        seam.data[e.index].value = True
    obj.data.update()
    r = fc.sync("Laço")
    check(r.get("marks", {}).get("new", {}).get("seam") == names and "this loop" in r["marks"]["reading"],
          f"new seams reported with the proposed reading ({r.get('marks')})")
    check("marks" not in fc.sync("Laço"), "reported once")
    r = fc.edit("Laço", "mesh mark_seam " + " ".join(names) + " clear=on")
    check(r["action"] == "pushed" and r.get("marks", {}).get("cleared", {}).get("seam") == names,
          f"the AI clears them and the sync says so ({r.get('marks')})")
    r = fc.edit("Laço", f"crease {names[0]} 0.5")
    check(r.get("marks", {}).get("new", {}).get("crease 0.5") == [names[0]], f"a crease is a mark too ({r.get('marks')})")
    fc.edit("Laço", f"crease {names[0]} 0")

    dg = bpy.context.evaluated_depsgraph_get()
    per_vertex = fc.mesh_io.evaluated(obj, dg)[0]
    va, vb = pick, nbr
    pts = [obj.matrix_world @ Vector(per_vertex[i]) for i in (va, vb)]
    annot = bpy.data.annotations.new("Annotations")
    bpy.context.scene.annotation = annot
    layer = annot.layers.new("Note")
    stroke = layer.frames.new(1).strokes.new()
    stroke.display_mode = "3DSPACE"
    steps = [pts[0].lerp(pts[1], t / 6) for t in range(7)]
    stroke.points.add(len(steps))
    for p_, c in zip(stroke.points, steps):
        p_.co = c
    mirrored = layer.frames[0].strokes.new()  # the same stroke drawn on the mirror copy (across Y)
    mirrored.display_mode = "3DSPACE"
    mirrored.points.add(len(steps))
    to_local = obj.matrix_world.inverted()
    for p_, c in zip(mirrored.points, steps):
        local = to_local @ c
        local.y = -local.y  # across the object's own Y plane
        p_.co = obj.matrix_world @ local
    r = fc.sync("Laço")
    notes = r.get("annotations", [])
    want = {f"v{ids_list[va]}", f"v{ids_list[vb]}"}
    check(len(notes) == 2 and all(want <= set(n["verts"]) for n in notes),
          f"each stroke names the vertices under it, on either side of the plane ({notes})")
    check("annotations" not in fc.sync("Laço") and len(fc.annotations("Laço")) == 2, "new strokes reported once, all listed on request")
    check(fc.clear_annotations() == 2 and not fc.annotations("Laço"), "the AI clears the strokes it acted on")
    label, loop_ids = fc.cage_format.parse(text_path.read_text("utf-8")).groups[0]
    idx = index_of(obj)
    for vid in loop_ids:  # the human lifts a whole loop in Blender
        obj.data.vertices[idx[vid]].co.z += 0.0005
    obj.data.update()
    r = fc.sync("Laço")
    check(any(s_.startswith(f"{label} {len(loop_ids)}/{len(loop_ids)} ") and " h+" in f" {s_}"
              for s_ in r.get("blender_by_loop", [])), f"the human's moves grouped by loop ({r.get('blender_by_loop')})")

    for v, co in zip(obj.data.vertices, shape0):  # back to the shape the later checks expect
        v.co = co
    obj.data.update()
    check(fc.sync("Laço")["action"] == "pulled", "shape restored from Blender")
    interior = next(i for i in free if len([e for e in obj.data.edges if i in e.vertices]) == 4)
    before = co_list(obj)
    r = fc.edit("Laço", f"mesh dissolve_verts v{ids_list[interior]}")
    check(r["action"] == "error" and "quads" in r["error"] and co_list(obj) == before,
          f"an op that leaves n-gons refused on the copy, nothing written ({r.get('error')})")
    check(len([o for o in bpy.data.objects if o.name.startswith("Laço.")]) == 0, "the checking copy is gone")
    drop_ops()
    r = fc.edit("Laço", f"crease loop v{a}-v{b} 0.5")
    edges = fc.cage_format.parse(text_path.read_text("utf-8")).edges
    check(r["action"] == "pushed" and any(line.startswith("crease 0.5") and f"v{a}" in line for line in edges),
          f"crease through a walker ({r.get('ops')})")
    fc.edit("Laço", f"crease loop v{a}-v{b} 0")
    check(tuple(ts.mesh_select_mode) == mode0 and obj.hide_select == hide0 and "fofuxo_cage_lock" not in obj,
          "the mesh op left no trace: select mode, lock")

    print("11f. shape tools: capture, profile, sections, fit, compare, editability")
    cap = fc.capture("Laço", key="test")
    check(cap["verts"] > 1000, f"captured a dense surface ({cap['verts']} verts)")
    prof = fc.profile("Laço", "top")
    check(len(prof["rows"]) == 21 and prof["rows"][10][1] > 0, "top profile, 21 bands")
    sec = fc.sections("Laço", "w", [150, 300])  # the width was halved in 10e
    check(all(s.get("n") and s.get("waist") for s in sec["sections"]) and Path(sec["render"]).exists(),
          f"sections with exponent and waist ({[(s.get('n'), s.get('waist')) for s in sec['sections']]})")
    add_ops("move all d +3%")
    fc.sync("Laço")
    moved = fc.deviation("Laço", "test")
    fitted = fc.fit("Laço", "test", passes=2)
    check(fitted["deviation_mm"]["mean_abs"] < moved["mean_abs"] / 2,
          f"fit brings the surface back ({moved['mean_abs']} -> {fitted['deviation_mm']['mean_abs']} mm)")
    libs = set(bpy.data.libraries)
    cmp_ = fc.compare("Laço", "Laço", blend=SOURCE)
    check(abs(cmp_["size_mm"]["this"][0] - cmp_["size_mm"]["ref"][0] / 2) < 2.0 and "top" in cmp_,
          f"compare against the source file ({cmp_['size_mm']})")
    check("Laço.001" not in bpy.data.objects and set(bpy.data.libraries) == libs, "the borrowed reference is gone, library too")
    r = fc.sync("Laço")
    check(not any(i["code"] == "cage_dips" for i in r["issues"]), "the modeler's wing has no dips")
    check("modifiers" not in r, "modifiers left out of a quiet report")
    check("modifiers" in fc.sync("Laço", verbose=True), "and included with verbose")
    v = fc.views("Laço", ["front"], render_name="focus", focus=[a, b], ghost=True, normals=True)
    check(Path(v["render"]).exists(), "views with focus, ghost and normals")

    print("12. Laço Nó")
    r = fc.sync("Laço Nó")
    check(r["action"] == "init", f"init ({r['action']})")
    cage = fc.cage_format.parse(Path(r["text"]).read_text("utf-8"))
    check(len(cage.verts) == 10, "10 verts")
    fc.capture("Laço Nó", key="knot")
    rb = fc.rebuild("Laço Nó", "Laço Nó", "knot", blend=SOURCE, passes=2)
    check(len(bpy.data.objects["Laço Nó"].data.vertices) == 10 and rb["deviation_mm"]["mean_abs"] < 0.2,
          f"rebuilt from the source's topology and fitted ({rb['count']}, {rb['deviation_mm']})")
    knot = bpy.data.objects["Laço Nó"]
    knot_text = Path(r["text"])
    knot_text.write_text(knot_text.read_text("utf-8").replace("\nops\n", "\nops\n  apply Mirror\n"), "utf-8")
    r = fc.sync("Laço Nó")
    cage = fc.cage_format.parse(knot_text.read_text("utf-8"))
    n = len(knot.data.vertices)
    check(r["action"] == "pushed" and "Mirror" not in knot.modifiers and n > 10,
          f"Mirror applied: {n} vertices ({r.get('ops')})")
    check(len(cage.verts) == n and len(set(cage.verts)) == n, "every applied vertex has its own id")
    check(fc.sync("Laço Nó")["action"] == "unchanged", "next sync unchanged")

    print("13. Edit Mode refused")
    try:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        entered = obj.mode == "EDIT"
    except Exception:
        entered = False
    if entered:
        try:
            fc.sync("Laço")
            check(False, "sync refused in Edit Mode")
        except fc.SyncError:
            check(True, "sync refused in Edit Mode")
        st = fc.lock("Laço")  # the AI takes control: out of Edit Mode, edits kept
        check(obj.mode == "OBJECT" and st.get("left_edit_mode") == "Laço", f"lock leaves Edit Mode ({st})")
        fc.unlock()
    else:
        print("  skip (no Edit Mode in background)")

    print("14. review in the human's Blender, absorb back")
    ai_file = bpy.data.filepath
    fc.sync("Laço")
    fc.lock("Laço", ui=False)
    rv = fc.review(["Laço", "Laço Nó"], launch=False)
    review_path = Path(rv["review"])
    check(rv["command"][1] == "--python-expr" and "open_review" in rv["command"][2]
          and review_path.parent == Path(ai_file).with_suffix(".cage"), f"review command ready ({review_path.name})")
    fc.unlock()
    # The human's Blender runs the command: here, in this same session.
    fc.instance_mod.open_review(ai_file, ["Laço", "Laço Nó"], review_path, {"length_unit": "MILLIMETERS"})
    info = fc.instance()
    names = sorted(o.name for o in bpy.context.scene.objects)
    human = bpy.data.objects["Laço"]
    check(names == ["Laço", "Laço Nó"] and info.get("review_of") == ai_file and bpy.data.filepath == str(review_path),
          f"the review holds the objects and knows its source ({names})")
    check(fc.lock_mod.PROP not in human and not human.hide_select
          and [m.type for m in human.modifiers][:2] == ["MIRROR", "SUBSURF"]
          and bpy.context.scene.unit_settings.length_unit == "MILLIMETERS", "unlocked, with its modifiers and units")
    hid = index_of(human)
    moved_vid = sorted(hid)[5]
    human.data.vertices[hid[moved_vid]].co.z += 0.002
    human.modifiers["Subdivision"].render_levels = 3
    # the human also marks a seam and draws a stroke over the moved vertex
    hseam = human.data.attributes.get("uv_seam") or human.data.attributes.new("uv_seam", "BOOLEAN", "EDGE")
    hedge = next(e for e in human.data.edges if hid[moved_vid] in e.vertices)
    hseam.data[hedge.index].value = True
    hpair = "v%d-v%d" % tuple(sorted(d.value for d in (human.data.attributes[fc.mesh_io.ID_ATTR].data[i]
                                                       for i in hedge.vertices)))
    note = bpy.data.annotations.new("Annotations")
    bpy.context.scene.annotation = note
    st = note.layers.new("Note").frames.new(1).strokes.new()
    st.display_mode = "3DSPACE"
    st.points.add(2)
    where = human.matrix_world @ human.data.vertices[hid[moved_vid]].co
    st.points[0].co, st.points[1].co = where, where
    time.sleep(1.1)  # a save the file's time can tell from the first one
    bpy.ops.wm.save_mainfile()
    bpy.ops.wm.open_mainfile(filepath=ai_file)  # back in the AI's Blender
    mats0 = len(bpy.data.materials)
    ab = fc.absorb()
    rep = ab.get("Laço", {})
    check(ab["changed"] and rep.get("action") == "pulled" and f"v{moved_vid}" in rep.get("blender_edits", []),
          f"absorb: the human's move comes back as a Blender edit ({rep})")
    check(bpy.data.objects["Laço"].modifiers["Subdivision"].render_levels == 3, "and the modifier change")
    check(rep.get("marks", {}).get("new", {}).get("seam") == [hpair], f"the human's seam comes back as a mark ({rep.get('marks')})")
    check(any(f"v{moved_vid}" in n["verts"] for n in rep.get("annotations", [])),
          f"and the stroke, with the vertex under it ({rep.get('annotations')})")
    check(not [o for o in bpy.data.objects if o.name.startswith("Laço.")] and len(bpy.data.materials) == mats0
          and not [m for m in bpy.data.meshes if m.users == 0], "no leftover objects, meshes or materials")
    check(fc.absorb()["changed"] is False, "a second absorb finds nothing new")
    obj = bpy.data.objects["Laço"]
    state_path = Path(ai_file).with_suffix(".cage") / "review.json"
    state = json.loads(state_path.read_text("utf-8"))
    state["pid"] = os.getpid()  # pretend the human's Blender is still open
    state_path.write_text(json.dumps(state), "utf-8")
    fc.edit("Laço", f"move v{moved_vid} h +5%")
    rv = fc.review(["Laço", "Laço Nó"], launch=False)
    check(rv.get("update") is True, f"with the review open, a newer version is announced ({rv})")
    ai_co = tuple(obj.data.vertices[index_of(obj)[moved_vid]].co)
    bpy.ops.wm.open_mainfile(filepath=str(review_path))
    check(bpy.ops.fofuxo_cage.load_update() == {"FINISHED"}, "the human loads it")
    human = bpy.data.objects["Laço"]
    co = tuple(human.data.vertices[index_of(human)[moved_vid]].co)
    check(all(abs(a - b) < 1e-7 for a, b in zip(co, ai_co))
          and not [o for o in bpy.data.objects if o.name.startswith("Laço.")], "the review now shows the AI's version")
    try:
        spent = bpy.ops.fofuxo_cage.load_update() == {"CANCELLED"}
    except RuntimeError:  # a cancelled operator with a warning raises in background
        spent = True
    check(spent, "and the notice is spent")
    bpy.ops.wm.open_mainfile(filepath=ai_file)
    obj = bpy.data.objects["Laço"]

    print(f"\nsidecar: {text_path.parent}")
    print(text_path.read_text("utf-8")[:2400])


try:
    main()
except Exception:
    traceback.print_exc()
    failures.append("exception")
# The last line is the verdict: Blender exits 0 when this file fails to parse,
# so read it rather than trusting the exit code alone.
print(f"\n{'FAILED: ' + str(len(failures)) if failures else 'ALL PASSED'} ({len(checks)} checks)")
sys.exit(1 if failures else 0)
