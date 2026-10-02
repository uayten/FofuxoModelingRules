"""Generate the short operator reference from the implemented whitelist (run in Blender)."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from llm_modeling_bridge.mesh_ops import OPS

lines = ["# Operator card", "", "One line per checked Blender operator. Read parameter meanings only for the operation you need with",
         '`mesh_help("translate", compact=False)`. Sizes use mm, m or frame percentages as documented.', "",
         "## Contents", "", "- [Operations](#operations)", "- [Selections](#selections)", "- [Other calls](#other-calls)", "",
         "## Operations", "", "| Operation | Parameters | Purpose |", "|---|---|---|"]
for name, operation in OPS.items():
    lines.append(f"| `{name}` | {', '.join(operation.params) or 'none'} | {operation.doc.replace('|', '/')} |")
lines += ["", "## Selections", "", '`vN`, `vA-vB`, `L1`, `region Upper`, `loop vA-vB`, `ring vA-vB`,',
          '`path vA vB`, `faces vA vB vC vD`, `h>500`, `faces h>500`, `border`,',
          '`plane-x/y/z`, `sharp`, `seam`, `crease`, `all`.', "",
          'Preview with `select(name, selection)`. Quote a region name containing spaces.', "",
          "## Other calls", "", "See [Session tools](README.md#session-tools) for absolute positions, regions, Workbench,",
          "recordings, examples, cost receipts, handover and stage checkpoints.", ""]
destination = root / "fofuxo-bridge" / "OPS.md"
destination.write_text("\n".join(lines), "utf-8")
print(f"Operator card: {len(OPS)} operators")
