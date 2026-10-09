"""Capture first/second-chance native exception stacks in a bridge-free NumPy probe."""

import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
debugger = "C:/Program Files (x86)/Windows Kits/10/Debuggers/x64/cdb.exe"
binary = "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe"
commands = ('sxe -c ".echo FIRST_CHANCE_AV; .exr -1; .ecxr; kb 12; gn" '
            '-c2 ".echo SECOND_CHANCE_AV; .exr -1; .ecxr; kb 12; gn" av; '
            'sxe -c ".echo PROCESS_EXIT; .lastevent; q" epr; g')
mode = sys.argv[1] if len(sys.argv) > 1 else "numpy"
if mode.startswith("roundtrip"):
    project = root.parents[3]
    arguments = ["--python", str(project / "extension/fofuxo-bridge/tests/test_roundtrip.py")]
else:
    code = "import faulthandler; faulthandler.enable(); import numpy; print('PROBE_READY: NumPy imported',flush=True)"
    arguments = ["--python-expr", code]
log = root / f"native-{mode}-debugger{'-normal-heap' if mode.startswith('roundtrip') else ''}.log"
with log.open("xb") as output:
    process = subprocess.run([debugger,"-hd","-c",commands,binary,"-b","--factory-startup",
                              *arguments,"--python-exit-code","1"],
                             stdout=output,stderr=subprocess.STDOUT,timeout=180,
                             creationflags=subprocess.CREATE_NO_WINDOW)
content = log.read_text(encoding="utf-8",errors="replace")
report = {"debugger_exit_code":process.returncode,
          "first_chance_events":content.count("\nFIRST_CHANCE_AV"),
          "second_chance_events":content.count("\nSECOND_CHANCE_AV"),
          "probe_ready":"PROBE_READY: NumPy imported" in content,
          "log":str(log)}
(log.with_suffix(".json")).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report),flush=True)
