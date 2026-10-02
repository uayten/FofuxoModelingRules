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

Native return was committed as 63f0e62. Same-window object addition/removal then
passed: the human removed `BridgeRemoveFixture`, added `BridgeAddedFixture`,
and saved prompt return archived both statuses. TestMesh geometry, ids, topology,
labels, matrix, modifier settings and regions were unchanged. The archived added
cube matched its live geometry and transform; eight unique ids were initialized
on sync and saved afterward. Receipt: `modal-recorder-test.same-window-objects-return.json`.
Example: `human/review-20261002-223059-1790980259602036700/`.

Object addition/removal was committed as c53816d. Current ownership is AI.
The focused Workbench result image is prepared at
`workbench-loop-review/model.workbench.high.png`, high view, 768 pixels, margin
1.25, focused on the eight approved loop ids. Receipt:
`modal-recorder-test.workbench-loop-review.json`. Scene objects, mesh coordinates
and ids were unchanged, and all temporary render data were cleaned up. Human
crop judgment is pending. The human did not understand the isolated crop.
A contextual comparison is now prepared at
`workbench-loop-context/workbench-crop-explanation.png`: complete result on the
left, projected camera rectangle in cyan, matching enlarged region on the right.
`crop-location.json` stores the rectangle computed from the actual camera framing.
Ask only whether that enlargement is useful/readable next. Then
validate evenness warnings with intentional tight and unwanted uneven spacing,
without automatic repairs. On human returns with an active transform, first execute:

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

The modeler chose the cowboy hat for uniformity judgment through the existing
labeled cage/result views, and questioned the separate Workbench crop's value.
That crop remains optional, without a separate validation gate. Do not repeat
instructions to avoid Blender while its AI screen already blocks input.

The primary AI Blender now has `hat-legacy-review/hat-legacy.blend` open, PID
32932, access AI. `inspection-session.json` records the original test file to
restore afterward. The source `models/tasks/chapeu-cowboy/ai/C1/C1.blend` and its
sidecar are untouched. A real copy was migrated, normally saved and reopened:
88 unique ids, 71 faces, geometry, modifiers, labels, creases and empty group
set were preserved. All thirteen original fingerprints still match; twelve
copied sidecar files are intact apart from the expected semantic JSON rewrite.
Receipt: `hat-legacy-review/migration-result.json`. No raw C1 recorder logs were
inspected. The subsequent sync reports unchanged geometry and seven cage
neighbour pairs above the 4:1 area warning threshold; maximum ratio 5.954.
Opposite-edge ratio 2.439 is below 3:1. Evaluated maxima are 2.631 and 1.592,
with no warnings or degenerate faces. Migration was committed as f313e65.

The hat's existing cage/result sheet is prepared at
`hat-legacy-review/hat-legacy.bridge/Chapéu.uniformity-main-pair.png`.
It shows yaw 50/pitch 40, front and top, with faces f2/f14 and their six stable
vertex ids labeled. That is the largest area-ratio pair, 5.954:1. The face labels
were temporarily enabled only while rendering, then restored exactly; geometry
and ids were unchanged. Receipt: `hat-legacy-review/uniformity-review.json`.
The modeler judged this pair as apparently unwanted: "parece um problema de
uniformidade". That confirms the area warning's usefulness for this one case.
The intentional-spacing comparison remains pending. The next sheet is
`hat-legacy-review/hat-legacy.bridge/Chapéu.uniformity-crease-pair.png`, with
f36/f41 and six ids labeled at the crown crease. Its neighbour-area ratio is
2.430:1, below the current 4:1 warning threshold. Receipt:
`hat-legacy-review/uniformity-crease-pair.json`. Ask whether that local spacing
serves the intended crease or is also an unwanted irregularity. The modeler
could not identify the faces in that whole-model sheet and requested a close
or removal of irrelevant information.

An uncommitted readability correction now extends the existing `views()` with
`crop=True`, `context_labels=False`, and `isolate=True`. Isolation enables close
framing, removes unrelated base geometry from the cage drawing, and keeps the
actual Subdivision surface alongside it. The Blender geometry is untouched.
Twenty focused checks passed, including preservation and default-call regression.
Installed render.py/sync.py were updated and their pure Python modules reloaded;
the public bridge.views/bridge.sync bindings were refreshed without registering
classes again or restarting Blender.

The modeler rejected the isolated patch as worse and explicitly requested the
complete model, a square locating the enlargement, and the enlarged area.
Next show `hat-legacy-review/uniformity-context-close.png`: complete cage on the
left, measured blue square, matching close with surrounding geometry on the
right. It uses yaw 50/pitch 40 for both views. The square comes from the actual
full/crop Panel projections, not a guessed image location. f36 is outlined blue
and f41 orange. Receipt: `hat-legacy-review/uniformity-context-close.json`;
diagram builder: `hat-legacy-review/render_context_close.py`.
The earlier isolate rejection is preserved in `uniformity-crease-isolated.json`.
The contextual sheet at positive yaw was still looking from the opposite side
of the editable mesh. The modeler requested the front-left/mirror-side view.
The latest sheet is now `hat-legacy-review/uniformity-context-close-left-front.png`,
using yaw -50/pitch 40 for overview and close. Metadata/projection rectangle:
`uniformity-context-close-left-front.json`. The measured face centers have
negative X and Y, consistent with this front-left camera. Use this latest image
for the next human assessment, rather than the earlier positive-yaw sheets.
The modeler approved the contextual identification: "consegui identificar bem
o que você quer me mostrar. essa parte ficou ótima". The readability correction
is visually validated, with twenty focused checks. Approval is preserved in
`uniformity-context-close-left-front.json`; do not interpret it as threshold
approval for every region or automatically repair geometry.

The modeler asked to open the hat natively. `review(['Chapéu'])` opened a separate
human Blender, PID 28092, saved at `hat-legacy-review/hat-legacy.bridge/review.blend`.
The opened marker and process window were verified; geometry and all 88 ids
match the AI's copy. The primary MCP still answers AI PID 32932, access AI.
Receipt: `hat-legacy-review/native-inspection-open.json`. When the human finishes,
use `collect(close=True)` to save, synchronize, preserve an example and close
only the review. Do not call `resume_ai()` for this separate-window return.
Clarify the local uniformity judgment during the native inspection before
claiming the full evenness check passed.

1. Human judgment of evenness thresholds on the copied hat, distinguishing
   intentional spacing from unwanted unevenness through the existing views.
   Preserve Mirror Y and the dent; no hat modeling edits are requested.
2. Normal shutdown with native output captured, then final focused checks and
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
