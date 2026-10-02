# Roadmap implementation — 2026-10-02

LLM Modeling Bridge 0.2.0 implements the tooling that could be built without
the modeler's participation. The open models and human judgments remain pending.

## Contents

- [Delivered](#delivered)
- [Verification](#verification)
- [Pending](#pending)
- [Install and resume](#install-and-resume)

## Delivered

| Original roadmap scope | Result |
|---|---|
| Cost measurement and shorter reports | Report characters before/after compaction, generated image pixels, explicit read/text receipts and supplied session usage in the round journal |
| Session growth and tool gaps | Stage briefs and persisted round checkpoints, excluding idle time until resume; short modeling session card |
| Regions | Vertex groups, stable-id lookup, quoted-name selections, mesh-text round trip, cage labels and regional movement summaries |
| Evenness | Neighbour face-area and opposite-edge spacing checks on cage and evaluated result, with provisional warning thresholds |
| Mouse and keys | Pass-through input listener, modifiers, surface/id hits, bounded drags and brush-radius receipts; provisional Grab and Smooth candidates |
| Review recorder | Compact operator/input summaries, undo/redo, region attribution and retained raw logs; C1's historical 343 operators have a saved compact summary |
| Same-window editing | Human handover, guards on extension edits, save/return action and automatic correction archive |
| Workbench | One view, optional region crop and cage wire overlay, disposable scene and cleanup after success or failure |
| Extension rename | Canonical source folder, llm_modeling_bridge package id/import, new metadata/sidecar names, conflict-preserving legacy migration and compatibility imports/launcher |
| Human corrections | Immutable saved before/after files, stable-id deltas, added/removed-object receipts, recorder artifacts and an explicit pending-interview status |
| Example measures | E1 top-hat sizes, profiles and cage evenness stored in models/example/chapeu/measures.json |
| Command discovery | Generated card of 50 implemented operators and per-operator help |
| Technique reuse | C1 observed-method index and a proposed context/measurement checklist; successful transfer is still unproven |

Code and API details are in the [extension README](extension/fofuxo-bridge/README.md#session-tools).
The [roadmap](ROADMAP.md) now contains only remaining work and judgments.

## Verification

- Existing round-trip suite: **244 checks passed**, process exit 0.
- Focused roadmap suite: **43 checks passed**, process exit 0; includes cleanup
  after an injected render failure, quoted region names, group replacement,
  mirror-axis replay directions, saved examples and checkpoints.
- Blender 5.2.2 validated the generated extension archive's manifest.
- Registration and legacy import checks passed in background Blender.
- The isolated E1 correction-catalog check passed and exited cleanly.
- No tracked .blend file was changed. Tests operated on temporary files.

The final full-suite run also printed native Windows access-violation
diagnostics during shutdown, with no Python frame, despite its passing
assertions and exit 0. The focused suite and isolated complex-catalog check
did not reproduce that diagnostic. Its cause is unconfirmed: these results
establish assertion coverage, not a fully clean native shutdown of that run.
No broad editor-testing loop was started to chase an unlocated failure.

## Pending

- Real Edit Mode/Sculpt/input recording and same-window interaction tests.
- The hat's side-dent approval, remaining parts/materials and final verdict.
- The modeler's second concept and validation of technique transfer.
- The unavailable skirt-ruffle reference and its example measures.
- Modeler-supplied reasons and measured replay of preserved corrections.
- Real comparable session usage; report characters and pixels do not establish
  billed token savings. Historical C1 usage and exact image billing remain
  unavailable without a supported source.
- Confirm whether the native shutdown diagnostic recurs in normal use or in
  a reproducible short case before expanding its investigation.

The interaction checklist is in [HUMAN_TESTS.md](extension/fofuxo-bridge/HUMAN_TESTS.md).
The MCP connected to the unsaved Plane scene was only inspected; installation
and human interaction checks remain for the modeler's next session.

## Install and resume

Install [llm_modeling_bridge-0.2.0.zip](extension/dist/llm_modeling_bridge-0.2.0.zip)
from Blender's Install from Disk menu, disabling the previous extension before
enabling the new one. The archive is a generated, ignored build artifact;
rebuild it with `python extension/package_extension.py` after source changes.

Read the updated roadmap, the [session card](skill/fofuxo-modeling-rules/SESSION.md)
and the current task's handoff. Preserve old human examples; opening an old
model with the new extension migrates its metadata and sidecar directory.
