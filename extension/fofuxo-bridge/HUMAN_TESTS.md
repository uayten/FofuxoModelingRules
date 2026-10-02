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
