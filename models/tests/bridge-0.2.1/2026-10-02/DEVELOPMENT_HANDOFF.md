# Interactive validation handoff

Continue development and validation of LLM Modeling Bridge 0.2.1. Do not resume
the cowboy-hat modeling task. Human interaction is required for the remaining
modal and visual checks.

## Read first

- `extension/fofuxo-bridge/HUMAN_TESTS.md`.
- README: Two Blenders, Session tools and references needed for the current test.
- ROADMAP: agent instructions and tooling-validation item only.
- This handoff and the exact receipts needed for the next check.

Avoid repository-wide reads, the full DECISIONS file, raw C1 logs and old runs.
Read implementation functions only when needed for a specific observed defect.

## Current instance and file

- Interactive MCP controls the AI Blender, last verified PID 28060, Blender
  5.2.2 LTS, access `ai`. Recheck through `bridge.instance()` before acting.
- Saved file: `models/tests/bridge-0.2.1/2026-10-02/modal-recorder-test.blend`.
- Object: `TestMesh`, a human-built capital-M test fixture, 36 base vertices and
  26 faces, Mirror X/Y and Subdivision. Keep its geometry unless the current
  validation explicitly needs an edit. Preserve any unrelated open work.
- Import `llm_modeling_bridge as bridge` through the interactive MCP. The actual
  package is `bl_ext.user_default.llm_modeling_bridge`.

## Human workflow

Normally keep the AI Blender open, launch a fresh separate human Blender through
`review()`, then `collect(close=True)` when the human finishes. Collection saves,
absorbs, preserves the example and closes only the review. Launch a new review
for the next edit. Manual saving is optional.

Same-window `human_access()` is explicit and currently under validation. After
handover, the next human prompt returns ownership: the first state-changing MCP
action must be `resume_ai(save=True)`, before synchronization or editing. No
"Save and return to LLM" button click is required. Refusal probes must run while
the human holds the window, before that next prompt. The extension does not
receive chat prompts itself; the agent performs this protocol.

Explain one short step, wait for the human, inspect the result, then advance.
The human operates Edit Mode and Sculpt. Never operate Sculpt for them or open
Play Mode/simulation. Operations must be recorded on completion without imposed
one-second pauses.

## Validated

- Activation fix c45e080 and 8 activation checks; original 43 tool checks.
- Event recorder: 26 focused checks, real Edit Mode operators, selection,
  movements, paired mouse input and brush metadata, Grab and temporary
  Shift/Smooth, actual undo/redo. Replay suggestions remain provisional.
- Stable topology ids: 14 focused identity-history checks and real cut/undo/redo
  retained exact ids 281–288. Five summary checks fixed empty-region attribution.
- Save/collect/close, modifier transfer and immutable before/after examples.
- TestRegion membership/labels survived a loop cut and absorb.
- Labeled base-cage/subdivision sheets and the single loop label are approved.
  Approved loop path: 281, 283, 288, 287, 286, 282, 284, 285. Use `views()` for
  cage review; Workbench result views do not replace these panels.
- Same-window Edit Mode and Sculpt: layout, extension-edit refusal, saved
  prompt return, synchronization and immutable examples passed.
- Latest Sculpt comparison used existing `catalog.borrowed_objects` and
  `catalog.snapshot_delta` through interactive MCP, with explicit human
  authorization. Two Grab and four Shift/Smooth strokes moved 13 vertices.
  Maximum recorded-versus-received component error: 0.006432 mm. All 36 ids,
  topology, modifier settings, regions and loop annotations survived; temporary
  data were removed and the live scene was unchanged by comparison.

Latest receipt:
`modal-recorder-test.same-window-sculpt-return.json` beside the saved file.
Latest immutable example:
`human/review-20261002-204403-1790973843261434300/`.
Prior Edit Mode receipt: `modal-recorder-test.same-window-return.json`.
Restart receipts: `modal-recorder-test.restart-baseline.json` and
`modal-recorder-test.restart-result.json`.

## Remaining work

1. Same-window return while a native transform is still active. The prior
   refusal happened during a live translate, but that translate had ended
   before the saved return. Do not claim modal takeover is validated. Prepare
   only this short human check next; verify that ownership return ends further
   mouse-driven changes and preserves a clearly recorded result.
2. Same-window added/removed objects: geometry replacement inside TestMesh did
   not establish separate-object handover behavior.
3. Human judgment of focused Workbench crop and evenness thresholds for
   intentional tight spacing versus unwanted unevenness. Do not automatically
   repair intentional geometry because of warnings.
4. Real legacy-copy migration, including its sidecar, normal save/reopen,
   unchanged geometry, modifier order/settings, stable ids, labels and data.
5. Normal shutdown with native output captured, then final focused checks and
   verification that installed sources and generated ZIP contain validated fixes.

## Connection and native diagnostic limitations

Interactive MCP works after saving and restarting only the AI Blender. Restart
retained ids, coordinates, faces and modifiers. The previous AI process exited
with code 0, but its native output was not captured.

`execute_blender_code_for_cli` repeatedly timed out after 120 seconds, including
after restart. Direct short background startup probes succeeded. Cause unknown;
do not blame model response latency or other add-ons without evidence. Do not
repeat this failing tool unnecessarily. The human authorized the existing
catalog APIs through interactive MCP for the comparison. If that cheap path
also fails, report and stop instead of scanning or writing extensive scripts.

The earlier full suite passed 244 assertions but printed a native access
violation at shutdown. The cause remains unknown; neither activation fix
c45e080 nor exit code 0 establishes that it is resolved.

## Editing and commits

Respond in Portuguese. New identifiers, comments, logs and commit messages are
English. Use focused checks after corrections; do not rerun broad suites without
a concrete reason. Update HUMAN_TESTS and ROADMAP only for actual validation.

Honor the human's AGENTS instructions: corrections stay uncommitted until the
feature is validated; on validation or a topic change commit all pending work
with `git add -A`, including user changes identified by status. Do not mix
unvalidated new feature implementation into a validation commit.
