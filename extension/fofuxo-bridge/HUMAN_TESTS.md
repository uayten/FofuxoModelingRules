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
- The labeled cage/result sheet and manual loop display are approved. Judge
  the focused Workbench crop and evenness thresholds with intentional
  tight spacing and unwanted unevenness. The earlier distorted cage was
  not approved merely because its image was generated.
- Exercise same-window access in Edit Mode and Sculpt: normal layout,
  refused extension edit, Save and return to LLM, synchronized geometry and
  immutable correction example. Check added/removed objects during this
  handover, since replacing geometry inside TestMesh does not test new objects.
- Migrate a real legacy file copy with its sidecar; save and reopen, comparing
  geometry, modifier order/settings, stable ids, region labels and sidecar data.
- Observe normal shutdown with native diagnostic output captured. Prior
  process exit code 0 without console capture did not settle the original
  access-violation diagnostic; do not infer its cause from the activation fix.
- Once these checks pass, update the roadmap, package the extension and
  verify that the installed sources and generated ZIP include the validated
  fixes. Run focused checks; a full-suite rerun needs a concrete reason.

## Same window

Ask the agent for `human_access()`. Confirm that the black screen disappears,
the usual Blender layout returns and editing works. While you hold the window,
ask for a small extension edit: it must refuse without touching the file.
Use **LLM > Save and return to LLM**. Confirm that it saves, restores the screen
and lets the agent synchronize your changes. Repeat once after switching
between Edit Mode and Sculpt. Do not close a file with unsaved work.

## Regions and renders

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
