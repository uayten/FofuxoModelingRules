# Human checks

Check the interaction after installing LLM Modeling Bridge 0.2.1. Use a copy
of a saved file. These checks do not approve the cowboy hat or the modeling method.

## Contents

- [Review recorder](#review-recorder)
- [Remaining validation](#remaining-validation)
- [Same window](#same-window)
- [Regions and renders](#regions-and-renders)
- [Open modeling work](#open-modeling-work)

## Review recorder

Open a review through `review()`. Make a small Edit Mode move, an edge slide
and a loop cut. Undo and redo once. In Sculpt, make separate Grab and Smooth
strokes, including temporary Smooth with Shift over Grab. Tell the agent when
finished; manual saving is optional.

The preferred workflow is `collect(close=True)`: save the human review,
synchronize its changes, preserve the example and close that Blender. For
the next edit, call `review()` again to launch a fresh human Blender with the
latest prepared model. Same-window handover remains a separate explicit test.
Keep the AI's own Blender running and controlling the MCP during this cycle.

Perform the operations at your normal pace, without artificial pauses. Include
two consecutive moves in opposite directions: both operations and their separate
deltas must be saved, even when their final displacement cancels. The recorder
uses dependency-graph and input events; Sculpt strokes end at their input/modal
boundary, rather than after an idle interval. Check the log before saving or
collecting to confirm that completed operations are already on disk.

Expected: operators, undo/redo and movements are in the compact summary;
the logs remain available; key modifiers and mouse press/release are in the
input log. Surface hits carry a stable id and point; a Grab drag on the model
may yield a provisional replay candidate. Compare its displacement and radius
with the actual stroke before accepting it. Missing hits are reported without
inventing coordinates. The correction is preserved in `human/review-.../`.

Missing or combined operations are defects. Exact brush replay is not claimed
by this version; that limitation does not permit dropping completed operations.

### Current validation

On 2026-10-02, the event recorder passed 15 focused checks, including immediate
mode/selection capture, separate opposite moves without waits, topology ids,
stroke-boundary callbacks, undo/redo callbacks and cleanup. Eight activation
checks also passed. The stroke and undo/redo boundary tests exercise callbacks;
at that point real modal input still required the separate checks recorded below.
The native shutdown diagnostic from the earlier full suite remains unexplained.
Opening the isolated test file also printed context errors from
`amp_transformator` (`selected_objects`) and `vertex_skin_weights_tool`
(`active_object`). These are environment observations, not an established
explanation of the native shutdown diagnostic.

The first real event-recorder review produced 99 operator records before
collection: four translates, five loop cuts, two edge slides and seven undos.
No parse errors or combined operator boundaries were reported. Both edge slides
used their clamped endpoints (1 and -1) and removed loops; their topology
changes were recorded. Redo still requires a deliberate human check.

This review is not approved: the input log has 27 middle-button presses and
no corresponding releases, and a drag spans the Sculpt/Edit Mode boundary.
Loop cuts after deletion also reused some retired vertex ids. Shift-modified
Sculpt gestures were labeled with the selected Grab brush. The modeler confirmed
that Smooth was invoked with Shift, without selecting its icon, establishing
the effective-brush labeling defect. Preserve these logs as evidence.

The follow-up interaction added 11 undos and 11 redos. Both sequences (three
steps, then eight) retained matching stable ids and inverse movement deltas
within the log's precision. Real Sculpt undo/redo recording passed this check.

The follow-up patch passed 26 focused checks. It gives the pass-through input
observer modal priority, closes strokes on release without graph-based guesses,
records effective temporary Smooth separately from selected Grab, and prevents
retired-id reuse while allowing historical ids to return through undo/redo.
Priority input snapshots do not repair or modify native modal mesh data.
Raw releases survive a failed surface sample, and incomplete drags cannot
produce replay candidates. Temporary Smooth settings are unavailable unless
shared unified settings or an observed native Smooth brush establish them.
The real follow-up passed: one Grab and two Shift-Smooth strokes were recorded,
with selected Grab retained and temporary Smooth observed at strength 0.7.
Six left-button presses/releases and two middle-button presses/releases paired;
all four sampled drags ended at release. No combined operator boundaries or
parse errors were reported. Native topology ids after the patch still need
the region/loop-cut interaction; its focused regression passed.

Collection with `close=False` saved and synchronized the review while leaving
its window open. That experiment passed, but the modeler prefers collecting
and closing, then opening a fresh review for each new edit. All 53 received
ids were unique; the Subdivision and Mirror
settings were unchanged. Summed recorded stroke deltas matched the received
mesh within 0.033 mm per component, accounting for the recorder's movement
filter and rounding. Before/after files, deltas and both logs were preserved
under `models/tests/bridge-0.2.1/2026-10-02/human/`.

Smooth replay commands remain provisional. The Grab candidate belongs to an
earlier surface drag rather than the stroke that deformed the mesh; reject it.
The actual Grab stroke had one surface point, insufficient for a drag replay.
This does not approve exact replay or promote a modeling technique.
The prior review was saved and archived, then closed with process exit code 0.
Its launcher does not capture native diagnostic output, so that exit code does
not establish the absence or cause of the earlier shutdown diagnostic.

The real region check passed after restarting the review. The five selected
`TestRegion` ids each moved by approximately (18.28, -1.61, 4.68) local mm.
One loop cut added 27 unique ids (109–135), growing the cage from 53 to 80
vertices without removing or reusing an existing id. Collection saved and
closed the human Blender; process exit code was 0. All five original region
members retained weight 1; six interpolated members were added (one at weight
1, five at 0.5). The group name, membership and mesh-text label survived absorb.

Both cropped Workbench and cage-overlay views were generated at 768 pixels,
focusing the 11 region members. Temporary objects and camera data were removed;
only `TestMesh` remained. The images have a transparent background. The modeler
rejected this Workbench overlay for cage inspection: topology must be shown as
the labeled base cage beside the Subdivision result, as in `views()` sheets.
A replacement sheet was generated at yaw -50 / pitch 40, top and front, with
the region's 11 ids and its name labeled. Subdivision was temporarily enabled
for the comparison; the original modifier visibility was restored afterward.
Human judgment of the replacement sheet remains pending.

On this deliberately deformed test mesh, maximum neighbouring-face area ratio
is 8.742 and opposite-edge spacing ratio is 23.784, above the initial 4:1 and
3:1 warning thresholds. The mirrored result doubles the flagged-pair counts
without changing those maxima. There are no degenerate faces. The modeler
still needs to judge whether these warnings help distinguish intentional
spacing from unwanted unevenness; they do not require automatic repair.

The replacement mesh review saved and closed by the modeler was absorbed
successfully. It preserved 276 operators, including 46 transforms, all carrying
selected ids and vertex movements. The received object has 36 vertices and
26 faces, with Mirror and Subdivision active. Recognizing its capital-M shape
is not approval of the extension's remaining validation.

This review exposed a summary defect: an existing empty TestRegion caused
unattributed movement samples to be reported as zero. The log retained all
121 samples. Attribution now uses the union of actual region memberships;
five pure regressions passed for absent, empty, partial, complete and overlapping
regions, and the real log now reports 121. No human editing needs repeating
for that summary correction.

The real Edit Mode topology undo/redo check failed. A cut created eight ids
255–262; a selection undo reloaded ids 247–254 on the same 44-vertex geometry,
the next undo returned to 36 vertices, and redo brought back 247–254 instead
of the originally recorded ids. Unique ids alone did not pass this check.
The failed review and logs were preserved before applying a fix.

The follow-up retains bounded identity snapshots of recorded geometry and
connectivity, restores known ids after native undo/redo, and does not invent
an identity snapshot for unrecorded geometry. It also prevents a repeated read
from retiring ids just allocated before the next recorder snapshot. Seven
focused identity checks passed, including reordered and coincident vertices;
26 event checks, 8 activation checks and 5 summary checks still passed. A real
editor repeat of the cut/undo/redo sequence remains required.

The repeat included selections, mode switches and edge dissolution. It exposed
missing object snapshots on some history callbacks and an unmatched restored
geometry state; final collected ids differed from the last history receipt.
The repeat was not approved. A native background reproduction then revealed
invalid BMVert references caused by losing the BMesh owner between reading
geometry and restoring ids. Restoration now keeps that owner alive and uses
the active view layer when the handler context has no object. Fourteen focused
checks passed, including actual native undo/redo, selection undo and edge
dissolve undo/redo. Real interactive confirmation is still pending.

The final real repeat passed. After dissolving two existing loops, the new cut
created ids 281–288 and grew the cage from 28 to 36 vertices. Undo removed
exactly those ids; redo restored the same set. All three undo and both redo
receipts identified TestMesh, reported successful identity restoration and
contained no snapshot errors. The collected mesh's unique ids matched the
last recorded state exactly. Selection, edge-slide and dissolve operations
were retained separately, with no combined boundaries or parse errors.
Collection saved, synchronized and closed the review; exit code was 0.

For cage readability, the modeler identified the new cut as one loop. The
path 281–283–288–287–286–282–284–285 was marked through `mark_loop`: seven
base edges, completed by the X/Y Mirror copies. The replacement cage sheet
shows one red `loop1` label instead of eight individual cut-vertex labels.
The modeler approved the labeled cage/subdivision presentation and this loop
display as-is. The cage-display validation is complete.

## Remaining validation

- Edit Mode topology undo/redo is now validated, including exact restored ids
  and agreement between the recorder and collected mesh; no repeat is needed.
- The labeled cage/result sheet, manual loop display and contextual close are
  approved. Initial evenness warnings passed the compared hat cases: f2/f14 was
  judged apparently unwanted, while unflagged f36/f41 was accepted before its
  minor centering adjustment. This is scoped to those examples. The modeler
  questioned the separate Workbench crop's value; it remains an optional tool,
  without a separate required visual gate or a claimed artistic approval.
- Same-window Edit Mode and Sculpt passed the refusal, saved prompt return,
  synchronization and immutable-example checks. Return during a still-active
  native transform also passed the real Edit Mode repeat. Separate object addition
  and removal passed the same-window saved handover and immutable-example check.
- Real legacy-copy migration, sidecar preservation and normal save/reopen passed
  with the copied cowboy hat; no repeat is needed.
- Observe normal shutdown with native diagnostic output captured. Prior
  process exit code 0 without console capture did not settle the original
  access-violation diagnostic; do not infer its cause from the activation fix.
- Once these checks pass, update the roadmap, package the extension and
  verify that the installed sources and generated ZIP include the validated
  fixes. Run focused checks; a full-suite rerun needs a concrete reason.

## Same window

The first handover reached human access with the normal layout restored and
MCP still running. While the modeler had an unfinished modal translate active
in Edit Mode, `edit("TestMesh", "mesh translate all w=1mm")` refused with
InstanceError. Mesh coordinates, selection, saved-file hash and active object
were unchanged by the attempt; the native translate remained active. The next
human prompt returned control through `resume_ai(save=True)`, without a button
click. At that point the translate had already ended, so no cancellation was
necessary. The AI screen returned, the file was saved, nine moved vertices
were synchronized and the correction example was preserved. All original ids
survived, including six vertices removed/restored by the human's undo.

The Sculpt handover also passed. The extension refused its edit without changing
the mesh, and the next prompt saved and restored AI access. The example contains
two Grab strokes and four temporary Shift/Smooth strokes, with radii 248–294 px
and observed strengths 0.4 and 0.7 respectively. Seven left-button and five
middle-button presses/releases paired; all eight sampled drags ended on release.
Thirteen vertices moved. Comparing the saved before/after objects preserved all
36 ids, topology, every inspected modifier setting, region memberships and loop
annotations. Summed stroke movements matched the received mesh within 0.006432 mm
per component. The archived after-object matched the live mesh, and temporary
data were removed. Replay suggestions remain provisional.

The background MCP tool timed out after 120 seconds, including after restarting
the AI Blender. Direct background startup probes completed, so the cause remains
unknown. With the modeler's authorization, comparison used the existing
`catalog.borrowed_objects` and `catalog.snapshot_delta` APIs through the
interactive MCP, without replacing the scene. Evidence is in
`models/tests/bridge-0.2.1/2026-10-02/modal-recorder-test.same-window-sculpt-return.json`.
The AI restart preserved ids, coordinates, faces and modifiers; its previous
process exited with code 0 without native output capture. That does not settle
the earlier access-violation diagnostic.

The first saved return during a still-active native transform failed: Object
Mode could not be entered while transforming. An attempted event-simulation
fix was rejected because Blender then ignored real mouse/keyboard input; that
attempt was removed. Its mocked checks did not validate human interaction.

The Windows correction uses paired right-button messages addressed only to
the current process's unique Blender window, checks the native Cancel binding,
and blocks further editing while awaiting cancellation. It never moves the
cursor, changes focus or enables event simulation. Fourteen isolated native
Object Mode checks, eight failure checks, eight activation checks and 26 recorder
checks passed before the real human repeat.

The real Edit Mode repeat passed on 2026-10-02. One confirmed move of nine vertices
was followed by an unfinished translate; the next chat prompt cancelled only
that live translate, saved and restored AI ownership. The log contains one
completed translate, separate cancellation request/completion receipts and paired
right-button input marked `during_return`, without an invented replay drag.
The final native transform handler is gone. The saved result matches the first
move within 0.000010 mm per component; all 36 ids, 26 faces, modifier settings,
regions and seven marked loop edges survived. The archived after-file matches
the live object, and borrowed comparison data were removed. Evidence:
`models/tests/bridge-0.2.1/2026-10-02/modal-recorder-test.native-cancel-return.json`.

The same-window object check also passed on 2026-10-02. The human deleted
`BridgeRemoveFixture` through the Outliner, added a cube and named it
`BridgeAddedFixture`. Saved prompt return preserved the addition and removal
in the before/after example and reported both object statuses. The recorder
retained Outliner deletion and cube addition. TestMesh geometry, all 36 ids,
topology, labels, matrix, modifier settings and region memberships were unchanged.
The archived added cube matched the live geometry and transform. Sync assigned
eight unique stable ids to the added object; a subsequent save persisted them.
Borrowed comparison objects were cleaned up. Evidence:
`models/tests/bridge-0.2.1/2026-10-02/modal-recorder-test.same-window-objects-return.json`.

Ask the agent for `human_access()`. Confirm that the black screen disappears,
the usual Blender layout returns and editing works. While you hold the window,
an extension edit must refuse without touching the file. The already observed
Edit Mode refusal remains valid; future refusal probes must run before the
next human prompt, because that prompt returns ownership immediately.
Tell the agent when finished. Its first state-changing MCP action must be
`resume_ai(save=True)`, restoring AI control and saving, followed by sync and
example checks. No sidebar-button click is part of the normal test flow.
Repeat after switching between Edit Mode and Sculpt. Keep the AI process open.

## Regions and renders

The first hat uniformity judgment identified the largest neighbouring-area
pair, f2/f14 at 5.954:1, as apparently unwanted: the modeler said
"parece um problema de uniformidade". The 4:1 warning points to a relevant
region in this example. This is a partial judgment; a tighter crease-region
pair, f36/f41 at 2.430:1, still needs its intentional-versus-unwanted verdict.
The original hat and inspection-copy geometry were not changed.

The modeler could not identify f36/f41 in the whole-model sheet and requested a
close or removal of irrelevant information. The existing `views()` API now has
`crop=True`, `context_labels=False` and `isolate=True`. Twenty focused checks
passed for camera framing, aligned cage/result panels, relevant face labels,
isolated base edges/vertices, unchanged geometry/annotations, invalid input and
backward-compatible default calls. The isolated hat sheet was visually rejected
as worse; removing context did not make the region understandable. The modeler
requested a complete model, a square showing the enlarged area, and the close.
That comparison is now prepared in `hat-legacy-review/uniformity-context-close.png`,
using the same native camera for the complete cage and close, with a rectangle
derived from their actual projections. Human legibility approval and local
uniformity judgment remained pending at that stage.
The modeler then corrected the viewing direction: the editable mesh is at the
front-left, while positive yaw was showing the opposite mirrored side. The latest
context/close sheet uses yaw -50/pitch 40, with matching full-view/crop projections;
the chosen face centers have negative X/Y. Human review now uses
`hat-legacy-review/uniformity-context-close-left-front.png`.
The modeler then approved identification and the contextual presentation:
"consegui identificar bem o que você quer me mostrar. essa parte ficou ótima".
The close-view readability correction is visually validated, alongside its
twenty focused checks. The modeler requested a native Blender inspection;
review PID 28092 opened with the same geometry and ids as the AI copy.
Native inspection then passed. The modeler stated the region was already
correct and only moved it slightly for centering. Collection saved, synchronized,
preserved the example and closed the review. Four vertices moved; all 88 ids,
71 faces, modifier settings, matrix, labels and groups were preserved. Two edge
slides, two undos and two redos were retained separately; their summed movements
matched the received mesh within 0.008710 mm per component. The archived after
object matched the live copy. This validates the initial warning's distinction
on the compared cases, without claiming universal thresholds or approving
automatic geometry repairs. Evidence: `hat-legacy-review/native-inspection-return.json`.

The real legacy-copy check passed on 2026-10-02 using `C1.blend` and all twelve
files of its `.cage` sidecar copied into `hat-legacy-review/`. Opening with the
installed extension migrated the sidecar directory and four legacy id/label
attributes. All 88 unique ids, 71 faces, vertex coordinates, edges, matrix,
modifier order/settings, label values and crease values survived migration,
normal save and reopening. The source has no vertex groups; that empty group
set was preserved, rather than being claimed as a populated-region test.
All thirteen original file fingerprints were unchanged; copied sidecar files
were preserved byte-for-byte except the expected semantically equivalent
rewrite of `review.json`. Raw historical recorder logs were not inspected.
Evidence: `models/tests/bridge-0.2.1/2026-10-02/hat-legacy-review/migration-result.json`.

Name a vertex group through `name_region`; use it for a move and a loop cut.
Check that its membership and label still match the intended region, including
after a review is absorbed. Read the evenness warnings on a cage with both
deliberately tight and unintentionally uneven loops; judge whether the initial
thresholds are useful.

Request a single Workbench view of that region, then a cage overlay. Check
that the crop and wire thickness are readable and that the file has no
temporary camera or objects. Legacy files should retain their ids, labels,
modifiers and geometry after migration and normal save/reopen.

## Open modeling work

Approve the cowboy hat's side dent before its temporary Mirror Y is applied.
Then continue thickness, band, buckle, tail and materials by reviewed stages.
Judge cage and result, the final hat and the method. Supply real session usage
for its cost report; historical C1 usage cannot be reconstructed from the new counters.

Choose the second concept and provide its reference. Supply the skirt-ruffle
example if it is still unavailable. Technique promotion and reuse require the
modeler's reason and a measured replay, not only a recorded gesture.
