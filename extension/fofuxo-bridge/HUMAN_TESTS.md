# Human checks

Check the interaction after installing LLM Modeling Bridge 0.2.1. Use a copy
of a saved file. These checks do not approve the cowboy hat or the modeling method.

## Contents

- [Review recorder](#review-recorder)
- [Same window](#same-window)
- [Regions and renders](#regions-and-renders)
- [Open modeling work](#open-modeling-work)

## Review recorder

Open a review through `review()`. Make a small Edit Mode move, an edge slide
and a loop cut. Undo and redo once. In Sculpt, make separate Grab and Smooth
strokes. Save, then ask the agent to collect the review.

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
real modal Edit Mode and Grab/Smooth input remain pending human validation.
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
its window open. All 53 received ids were unique; the Subdivision and Mirror
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
