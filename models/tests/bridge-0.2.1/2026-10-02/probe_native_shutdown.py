"""Separate Blender/NumPy startup diagnostics from extension use in isolated processes."""

import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parent
project = root.parents[3]
binary = "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe"
prefix = "import faulthandler; faulthandler.enable(); "
cases = {
    "bare-fauldhandler": prefix + "print('PROBE_READY: bare Blender',flush=True)",
    "numpy-fauldhandler": prefix + "import numpy; print('PROBE_READY: NumPy imported',flush=True)",
    "bridge-import-fauldhandler": prefix + "import sys; sys.path.insert(0," + repr(str(project / "extension")) +
        "); import llm_modeling_bridge; print('PROBE_READY: bridge imported',flush=True)",
}
results = []
for name, code in cases.items():
    log = root / f"probe-{name}.log"
    with log.open("xb") as output:
        process = subprocess.run([binary,"-b","--factory-startup","--python-expr",code,
                                  "--python-exit-code","1"],cwd=project,stdout=output,
                                 stderr=subprocess.STDOUT,timeout=60)
    content = log.read_text(encoding="utf-8",errors="replace")
    result = {"case":name,"exit_code":process.returncode,"ready":'PROBE_READY:' in content,
              "access_violation_count":len(re.findall('access violation',content,re.IGNORECASE)),
              "log":str(log)}
    results.append(result)
    print(json.dumps(result),flush=True)
(root / "native-shutdown-probes.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
