# Modeling session card

Read the task's handoff first, then only the skill sections and decisions
the current stage needs. The full skill remains authoritative.

## Contents

- [Start](#start)
- [Build and review](#build-and-review)
- [Tool gap](#tool-gap)
- [End](#end)

## Start

- Read `ROADMAP.md`, the run's `NEXT.md` or `HANDOFF.md`, and the plan's current stage.
- Import `llm_modeling_bridge`; check `instance()` and the open file. A failed
  MCP or missing helper stops the task; do not replace it with raw modeling scripts.
- Read the saved example measures instead of measuring again. Look up one
  relevant technique; confirm its body, proportions, topology, mirror axes
  and expected outcome fit this case. A similar silhouette alone is insufficient.
- Write the short plan in the conversation and review it with the modeler.
  Open the round with `round_start`; resume a persisted round with `round_resume`.
  Do not invent a past token count or assume an in-memory round survived restart.

## Build and review

- Fewest vertices first; add a loop only where the stage's check needs it.
- Use Blender's checked operations; name meaningful regions with `name_region`.
  Read one command with `mesh_help("translate", compact=False)` or the
  [operator card](../../extension/fofuxo-bridge/OPS.md), not the full README.
- Keep symmetry, Subdivision, thickness and repetition in live modifiers.
  Applying the hat's temporary Mirror Y remains a specific approved exception.
- Shape in small steps. Check numbers first; use one small Workbench view of
  the changed region when a view is necessary. Inspect both cage and result.
- Stop after a silhouette/form render for the modeler's correction. Use
  `review` and `collect`, or `human_access` and the human's return button.
- Read recorder summaries, not raw logs. Treat replay candidates as provisional.
  Record the reason for a correction when the modeler supplies it.

## Tool gap

Save the `.blend`, then `stage_handoff` with the current state, exact next
action, files/sections to read, files to avoid and `tool_need`. Develop the
tool in a separate session. Return with its API and test result, read the
brief and resume the checkpoint; do not pull tool-development history into
the modeling stage. No chat creation or plan approval is implied by the helper.

## End

Write the handoff. End the round only when its work is complete; otherwise
checkpoint it. Record actual supplied usage with `round_end(tokens=...)`.
Report and image receipts cannot establish billed token savings by themselves.
Keep the roadmap limited to remaining work, and wait for the modeler's verdict
before treating a finished build or replay as an approved method.
