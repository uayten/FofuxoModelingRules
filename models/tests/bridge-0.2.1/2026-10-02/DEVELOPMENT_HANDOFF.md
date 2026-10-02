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

- Interactive MCP controls the AI Blender, last verified PID 32932, Blender
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

Active-transform return failed on the first real attempt: `resume_ai(save=True)`
could not leave Edit Mode while the native move was active. The human cancelled
with Escape; normal return then saved and archived the session, and geometry and
ids matched `modal-recorder-test.active-transform-baseline.json` exactly.

The event-simulation correction was rejected and removed. Twelve focused mocked
state checks and eight activation checks passed, but the real human could not
click: `--enable-event-simulate` makes Blender ignore native mouse/keyboard
events. It is unsuitable for human editing; do not launch with that flag again.
The earlier restart receipt records that failed experiment, not approval.

`instance.py` and its installed copy are restored to the committed implementation.
Active-transform return remains unresolved. The launcher retains only its new
`--native-log` option for capturing stdout/stderr. The rejected test process shut
down normally with output in `modal-recorder-test.active-transform-native.log`;
its tail contains `Blender quit`. This does not establish the cause or resolution
of the historical native access violation.

The test Blender was restarted without event simulation, and geometry and ids
still matched `modal-recorder-test.active-transform-retry-baseline.json`.
Receipt: `modal-recorder-test.input-recovery.json`. Current native capture:
`modal-recorder-test.input-recovery-native.log`.

Human clicking was confirmed after this restart. The human also confirmed a
first Edit Mode move and left a second one active; return failed again with
`Unable to change object mode while transforming`. Instead of Escape, the human
then confirmed the second move and used Undo. Saved return succeeded afterward.
The log's Undo exactly negates the second move; the final mesh matches the first
move within 0.01 mm per component, preserving 36 ids and topology.
Receipt: `modal-recorder-test.active-transform-manual-undo-return.json`.
Example: `human/review-20261002-220300-1790978580258686800/`.

The human explicitly authorized further investigation and corrections without
the cheap-path stopping restriction, continuing until the tooling-validation
roadmap is complete. Do not resume the unrelated hat work.

A new uncommitted implementation uses paired right-button Win32 messages
addressed only to this process's unique Blender window. It checks the native
Cancel binding, never moves the cursor or changes focus, and leaves native human
input enabled. Fourteen isolated native Object Mode checks passed, including a
real unfinished preview, cancellation, preservation of the confirmed move,
saved immutable example and separate cancellation receipts. Eight failure-path
checks, eight activation checks and 26 recorder checks passed. Do not substitute
the isolated Object Mode fixture for the pending human Edit Mode confirmation.

After installation and restart, PID 32932 has event simulation disabled,
unchanged geometry/ids and matching installed sources. Receipt:
`modal-recorder-test.native-cancel-restart.json`; baseline:
`modal-recorder-test.native-cancel-baseline.json`; current native capture:
`modal-recorder-test.native-cancel-native.log`. The preceding process's captured
shutdown contains `Blender quit`, without matching crash/access-violation markers;
that does not settle the cause or resolution of the historical diagnostic.

The real human Edit Mode repeat passed: the next prompt cancelled the active
translate, saved and returned AI access. The confirmed move of nine vertices was
preserved within 0.000010 mm per component. All 36 ids, 26 faces, modifier settings,
regions and seven marked loop edges survived. The archived after-object matched
the live object, and borrowed comparison data were removed.
Receipt: `modal-recorder-test.native-cancel-return.json`.
Example: `human/review-20261002-222251-1790979771806778600/`.

Current ownership is AI. Next prepare only the same-window added/removed-object
check. On future human returns with an active transform, first execute:

```python
result = bridge.resume_ai(save=True)
if result.get("pending"):
    def check_is_finished():
        return None if result.get("pending") else result
```

Check `error`, saved result, cancelled native handler, confirmed edit, stable ids,
topology and archived receipts before validation or committing. Input during
return is marked `during_return` and cannot create replay drags. Do not count the
withdrawn simulation checks or manual confirm/Undo as active native takeover.

1. Same-window added/removed objects: geometry replacement inside TestMesh did
   not establish separate-object handover behavior.
2. Human judgment of focused Workbench crop and evenness thresholds for
   intentional tight spacing versus unwanted unevenness. Do not automatically
   repair intentional geometry because of warnings.
3. Real legacy-copy migration, including its sidecar, normal save/reopen,
   unchanged geometry, modifier order/settings, stable ids, labels and data.
4. Normal shutdown with native output captured, then final focused checks and
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
