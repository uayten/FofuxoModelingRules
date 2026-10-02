"""Focused roadmap regressions, using temporary files and one small render."""

import json
import math
from pathlib import Path
import sys
import tempfile
import importlib
from unittest.mock import patch

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm_modeling_bridge as bridge
from llm_modeling_bridge import migration, reports, rounds, evenness, recording, input_recorder

checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1
    print(f"ok {message}", flush=True)


def refuses(callback, error=Exception):
    try:
        callback()
    except error:
        return True
    return False


def signature():
    return {kind: {item.as_pointer() for item in getattr(bpy.data, kind)} for kind in ("objects", "meshes", "cameras", "scenes", "node_groups", "images")}


def main():
    import fofuxo_cage
    check(fofuxo_cage is bridge, "legacy import shares bridge state")
    bridge.register()
    root = Path(tempfile.mkdtemp(prefix="llm_bridge_roadmap_"))
    bpy.ops.wm.save_as_mainfile(filepath=str(root / "test.blend"))
    obj = bpy.data.objects["Cube"]
    initial = bridge.sync("Cube", render=False)
    check(initial["action"] == "init" and "evenness" in initial, "sync checks cage and evaluated evenness")
    bridge.name_region("Cube", "Upper", "v0 v1 v2 v3")
    check(bridge.region_ids("Cube", "Upper") == ["v0", "v1", "v2", "v3"], "vertex groups store stable ids")
    check(set(bridge.select("Cube", "region Upper")["verts"]) == {"v0", "v1", "v2", "v3"}, "selection grammar uses named regions")
    cage = bridge.cage_format.parse(Path(initial["text"]).read_text("utf-8"))
    check(cage.regions["Upper"] == [0, 1, 2, 3], "region names survive the text round trip")
    bridge.name_region("Cube", "Upper Crown", "v0 v1")
    check(set(bridge.select("Cube", 'region "Upper Crown"')["verts"]) == {"v0", "v1"}, "quoted region names work in selection previews")
    region_view = bridge.views("Cube", ["front"])
    check(Path(region_view["render"]).is_file(), "named regions render on cage panels")
    frame = bridge.frame.Frame.parse(cage.header["frame"])
    wanted = list(frame.to_values(obj.data.vertices[0].co))
    wanted[0] += 20
    result = bridge.set_positions("Cube", {"v0": wanted})
    check(result["action"] == "pushed" and abs(frame.to_values(obj.data.vertices[0].co)[0] - wanted[0]) < 0.001, "absolute positions use checked edits")
    unchanged = [tuple(vertex.co) for vertex in obj.data.vertices]
    check(refuses(lambda: bridge.set_positions("Cube", {"v999": (0, 0, 0)}), ValueError)
          and unchanged == [tuple(vertex.co) for vertex in obj.data.vertices], "unknown ids cannot modify a batch")
    check(refuses(lambda: bridge.set_positions("Cube", {"v0": (math.nan, 0, 0)}), ValueError), "nonfinite positions are rejected")

    obj.data.attributes[bridge.mesh_io.ID_ATTR].name = "fofuxo_cage_id"
    obj["fofuxo_on"] = "Body"
    migration.migrate_scene()
    check(obj["llm_bridge_on"] == "Body" and bridge.mesh_io.ID_ATTR in obj.data.attributes, "legacy metadata migrates")
    old = root / "legacy.cage"
    old.mkdir()
    (old / "review.json").write_text(json.dumps({"review": str(old / "review.blend")}), "utf-8")
    (old / "sentinel.txt").write_text("keep", "utf-8")
    new = migration.data_root(root / "legacy.blend")
    check(not old.exists() and (new / "sentinel.txt").read_text("utf-8") == "keep", "sidecar migration preserves files")
    check(json.loads((new / "review.json").read_text("utf-8"))["review"] == str(new / "review.blend"), "review state follows the new directory")
    old.mkdir()
    check(refuses(lambda: migration.data_root(root / "legacy.blend"), migration.MigrationError)
          and old.exists() and new.exists(), "sidecar conflicts preserve both folders")
    obj["fofuxo_on"] = "Other"
    check(refuses(migration.migrate_scene, migration.MigrationError) and obj["fofuxo_on"] == "Other", "metadata conflicts are preserved")
    del obj["fofuxo_on"]

    rounds.round_start("metrics")
    full = {"ops": ["mesh translate v0 h=1mm; v0 h+2.0%"], "deltas": [str(i) for i in range(40)]}
    short = reports.finish("edit", full)
    check(len(short["deltas"]) == 20 and short["omitted"]["deltas"] == 20 and ";" not in short["ops"][0], "compact reports bound lists")
    check(reports.finish("edit", full, True) == full, "verbose reports retain details")
    bridge.record_read("excerpt.md", characters=123)
    bridge.record_read("view.png", kind="image", width=100, height=200)
    bridge.record_agent_text("ten chars!")
    rounds.record_image(64, 64)
    checkpoint = bridge.round_checkpoint()
    check(Path(checkpoint["checkpoint"]).is_file() and rounds._round["start"] is None, "checkpoints pause measured active time")
    bridge.round_resume()
    cost = bridge.round_end(tokens=0)
    metrics = cost["cost_by_kind"]
    check(metrics["reports"]["edit"]["returned_chars"] < metrics["reports"]["edit"]["full_chars"], "metrics count returned report characters")
    check(metrics["images"]["render"]["pixels"] == 4096 and metrics["external_reads"]["image"]["pixels"] == 20000, "render pixels and external reads are separate")
    check(cost["tokens"] == 0 and cost["token_source"] == "session_usage", "zero tokens differ from unavailable usage")

    text_before = Path(initial["text"]).read_bytes()
    bridge.instance_mod._state["human_editing"] = True
    check(refuses(lambda: bridge.edit("Cube", "move v0 h +1%"), bridge.InstanceError)
          and Path(initial["text"]).read_bytes() == text_before, "human access blocks edits before text writes")
    check(refuses(lambda: bridge.start_part("Blocked", "cube", (10, 10, 10)), bridge.InstanceError)
          and "Blocked" not in bpy.data.objects, "human access blocks new parts")
    check(refuses(lambda: bridge.name_region("Cube", "Blocked", "all"), bridge.InstanceError), "human access blocks region edits")
    bridge.instance_mod._state["human_editing"] = False

    mesh = bpy.data.meshes.new("Evenness test")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (11, 0, 0), (11, 1, 0)], [], [(0, 1, 2, 3), (1, 4, 5, 2)])
    check(evenness.measure(mesh)["area_pairs_over"] == 1, "unequal neighbouring patches warn")
    mesh.vertices[4].co.x = mesh.vertices[5].co.x = 2
    check(evenness.measure(mesh)["area_pairs_over"] == 0, "uniform patches do not warn")
    bpy.data.meshes.remove(mesh)
    drag = {"event": "DRAG", "points": [{"object": "Cube", "vertex": "v0", "point_mm": [0, 0, 0], "brush": "Grab", "radius_mm": 40, "axis_signs": {"w": 1, "d": 1, "h": 1}},
                                          {"object": "Cube", "vertex": "v1", "point_mm": [0, 2, 12]}]}
    candidates = recording.replay_candidates([drag])
    check(len(candidates) == 1 and "h=+12.000mm" in candidates[0]["op"] and candidates[0]["status"] == "provisional", "Grab gestures produce provisional replay candidates")
    drag["points"][0]["axis_signs"]["d"] = -1
    check("d=-2.000mm" in recording.replay_candidates([drag])[0]["op"], "Grab replay respects the mirrored frame's axis directions")
    smooth = {"op": "SCULPT", "object": "Cube", "brush": "Smooth", "strength": 0.4, "moved": {"0": [0, 0, 1]}}
    check("factor=0.4" in recording.replay_candidates([smooth])[0]["op"], "Smooth strokes produce provisional operator candidates")
    summary = recording.summarize([{"op": "SCULPT", "regions": {"Upper": [0]}, "moved": {"0": [0, 2, 12]}}, {"op": "UNDO"}])
    check(summary["undos"] == 1 and summary["moves_by_region"]["Upper"]["net_mm"] == [0, 2, 12], "summaries retain undo and region motion")
    log = root / "input.jsonl"
    log.write_text(json.dumps(drag) + "\ninvalid\n", "utf-8")
    check(recording.recording_summary(log, candidates=True)["parse_errors"][0]["line"] == 2, "bad records do not discard good records")
    check(input_recorder.start_recording()["reason"] == "background", "background tests do not start input capture")

    bpy.ops.wm.save_as_mainfile(filepath=str(root / "before.blend"))
    obj.data.vertices[0].co.z += 0.001
    obj.vertex_groups["Upper"].name = "Reviewed"
    bpy.ops.wm.save_as_mainfile(filepath=str(root / "after.blend"))
    scene_before = signature()
    example = bridge.catalog_edit(root / "before.blend", root / "after.blend", root / "example", ["Cube"], why="Test correction")
    check(signature() == scene_before, "cataloguing cleans imported objects and data")
    receipt = json.loads((Path(example["example"]) / "edit.json").read_text("utf-8"))
    check(abs(receipt["deltas"]["Cube"]["moved_mm"]["v0"][2] - 1) < 0.001, "catalogue stores measured stable-id deltas")
    check(refuses(lambda: bridge.catalog_edit(root / "before.blend", root / "after.blend", root / "example", ["Cube"]), FileExistsError), "catalogue preserves saved examples")
    bridge.catalog_measures(root / "after.blend", ["Cube"], root / "measures.json")
    check("size_mm" in json.loads((root / "measures.json").read_text("utf-8"))["objects"]["Cube"] and signature() == scene_before, "measures are stored without scene changes")
    bridge.instance_mod.replace_from(root / "before.blend", ["Cube"])
    check("Upper" in obj.vertex_groups and "Reviewed" not in obj.vertex_groups, "review replacement copies vertex group definitions and weights")
    scene_before = signature()
    settings = (bpy.context.scene.camera, bpy.context.scene.render.engine, bpy.context.scene.render.resolution_x)
    render = bridge.workbench("Cube", out=root, size=128, cage=True)
    check(Path(render["render"]).is_file() and signature() == scene_before, "Workbench cleans all temporary datablocks")
    check(settings == (bpy.context.scene.camera, bpy.context.scene.render.engine, bpy.context.scene.render.resolution_x), "Workbench preserves original settings")
    workbench_module = importlib.import_module("llm_modeling_bridge.workbench")
    with patch.object(workbench_module, "_render_scene", side_effect=RuntimeError("injected render failure")):
        check(refuses(lambda: bridge.workbench("Cube", out=root, size=128, cage=True), RuntimeError)
              and signature() == scene_before, "failed renders also clean all temporary datablocks")
    check(refuses(lambda: bridge.workbench("Cube", out=root, focus=[999], size=128), ValueError) and signature() == scene_before, "invalid render focus preserves the scene")
    check(bridge.mesh_help("translate").count("\n") == 0 and "falloff" in bridge.mesh_help("translate", compact=False), "operator help works one operation at a time")
    bridge.round_start("handoff")
    brief = bridge.stage_handoff("Test stage", "The shape is saved.", "Review the crown.", ["plan.md#changes"],
                                decisions=["Keep Mirror live."], avoid=["old runs"], tool_need="Add a measured region render.")
    check(Path(brief["handoff"]).is_file() and "Tool request" in Path(brief["handoff"]).read_text("utf-8"), "stage handoffs preserve the tool request and next action")
    bridge.round_resume()
    bridge.round_end()
    bridge.unregister()
    print(f"ROADMAP ALL PASSED ({checks} checks)", flush=True)


main()
