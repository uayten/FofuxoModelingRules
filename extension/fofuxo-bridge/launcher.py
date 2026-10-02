"""Start the AI's own Blender: black screen, MCP server on port 9876.

    python extension/fofuxo-bridge/launcher.py <file.blend> [--blender PATH] [--timeout 120]

Plain Python (no bpy): it runs outside Blender. If an AI instance is alive
it says so and starts nothing. It waits until the new Blender writes its
marker and the MCP port answers, then prints a JSON line: the AI's pid and
the processes listening on the port (a human's Blender with LLM Modeling Bridge
stops its own server within a few seconds; an older one needs
llm_modeling_bridge.release_mcp(), or the MCP server stopped by hand).
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MARKER = Path(tempfile.gettempdir()) / "llm_modeling_bridge_ai.json"
PORT = 9876
STEAM = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe")


def _alive(pid):
    if not pid:
        return False
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(handle, ctypes.byref(code))
        k32.CloseHandle(handle)
        return bool(ok) and code.value == 259
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def ai_instance():
    for path in (MARKER, MARKER.with_name("fofuxo_cage_ai.json")):
        try:
            data = json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if _alive(data.get("pid")):
            return data
    return None


def port_open(port=PORT):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def listeners(port=PORT):
    """Pids listening on the port (Windows: netstat), or None if unknown."""
    if os.name != "nt":
        return None
    out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
    pids = set()
    for line in out.splitlines():
        m = re.search(rf"[\d.]+:{port}\s+\S+\s+LISTENING\s+(\d+)", line)
        if m:
            pids.add(int(m[1]))
    return sorted(pids)


def blender_path(arg):
    for candidate in (arg, os.environ.get("FOFUXO_BLENDER"), STEAM if STEAM.exists() else None, "blender"):
        if candidate:
            return str(candidate)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("blend")
    ap.add_argument("--blender")
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args(argv)
    running = ai_instance()
    if running:
        print(json.dumps({"started": False, "ai": running, "note": "an AI instance is already running; open the "
                          "file there (bpy.ops.wm.open_mainfile) instead", "listeners": listeners()}))
        return 0
    before = listeners()
    flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    proc = subprocess.Popen([blender_path(args.blender), str(Path(args.blend).resolve()), "--", "--llm-bridge-ai"],
                            creationflags=flags, close_fds=True, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + args.timeout
    ai = None
    while time.time() < end:
        ai = ai_instance()
        if ai and ai["pid"] == proc.pid and port_open():
            break
        if proc.poll() is not None:
            print(json.dumps({"started": False, "error": f"Blender exited with {proc.returncode}"}))
            return 1
        time.sleep(1)
    else:
        print(json.dumps({"started": False, "error": "timed out waiting for the AI instance", "pid": proc.pid}))
        return 1
    # A human's Blender on the same port stops its server at its next poll.
    others = []
    for _ in range(10):
        now = listeners()
        others = [p for p in (now or []) if p != proc.pid]
        if not others:
            break
        time.sleep(1)
    print(json.dumps({"started": True, "pid": proc.pid, "listeners_before": before, "listeners": listeners(),
                      "others_on_port": others}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
