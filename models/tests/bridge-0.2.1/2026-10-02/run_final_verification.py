"""Capture native regression output and distinguish assertions from clean shutdown."""

import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parent
project = root.parents[3]
binary = Path("C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe")
tests = (("roundtrip", "test_roundtrip.py", 244), ("roadmap", "test_roadmap.py", 43))
results = []
diagnostics = r"EXCEPTION_ACCESS_VIOLATION|access[- ]violation|EXCEPTION_ILLEGAL_INSTRUCTION|Fatal Python error|Segmentation fault"
for name, filename, expected in tests:
    log_path = root / f"final-{name}-native.log"
    with log_path.open("xb") as output:
        process = subprocess.run([str(binary), "-b", "--factory-startup", "--python",
                                  str(project / "extension/fofuxo-bridge/tests" / filename),
                                  "--python-exit-code", "1"], cwd=project, stdout=output,
                                 stderr=subprocess.STDOUT, timeout=300)
    content = log_path.read_text(encoding="utf-8", errors="replace")
    counts = [int(value) for value in re.findall(r"ALL PASSED\s*\((\d+) checks\)", content)]
    markers = re.findall(diagnostics, content, re.IGNORECASE)
    result = {"test": filename, "exit_code": process.returncode, "assertion_counts": counts,
              "expected_checks": expected, "native_diagnostic_markers": markers,
              "native_output": str(log_path),
              "passed": process.returncode == 0 and expected in counts and not markers}
    results.append(result)
    print(json.dumps(result), flush=True)
report = {"reason_for_roundtrip_rerun": "the previous 244-check run printed a native access violation at shutdown",
          "tests": results, "passed": all(result["passed"] for result in results),
          "historical_access_violation_cause": "unknown; no cause is inferred from exit codes"}
(root / "final-regression-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
raise SystemExit(0 if report["passed"] else 1)
