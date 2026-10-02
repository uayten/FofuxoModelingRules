# Roadmap

> [!IMPORTANT]
> **This file is written to be read and acted on by AI agents.** Read the
> remaining work here, take the next available step from [Order](#order),
> and keep this file true. Implemented tools belong in the extension README;
> this file contains only work and judgments still pending.

What remains before a text LLM can build an editable Blender model from an
approved plan, learn from human corrections and demonstrate a lower session cost.

## Contents

- [How an agent uses this file](#how-an-agent-uses-this-file)
- [Principles](#principles)
- [To do](#to-do)
- [Order](#order)

## How an agent uses this file

1. Read this file, then only the files and decision sections named by the
   step. Do not read the whole repository or the whole DECISIONS.md.
2. Take the first available step in [Order](#order), unless the modeler asks
   for another. Say which one before starting. A required human judgment
   stays pending when the modeler is unavailable.
3. Modeling proceeds in the conversation, stage by stage, stopping after
   each form render for the modeler's correction. Keep the AI Blender open
   and use `review()` to open a separate human Blender with the latest saved
   model. When the modeler finishes, `collect(close=True)` saves, synchronizes
   and closes only the human review. Launch a fresh review for the next edit.
   Same-window handover is an explicit opt-in or its dedicated validation
   step. After handing the AI window to the human, the next human prompt is
   the return signal: the first state-changing MCP action must be
   `resume_ai(save=True)`, restoring exclusive AI access and saving the work
   before synchronization or editing. Do not require a sidebar-button click.
   This is agent orchestration; the Blender extension does not receive chat
   prompts directly. Show labeled cage/subdivision panels with `views()` for topology
   review; Workbench views show the result and do not replace the cage panels.
   A correction of method becomes a proposed decision with the modeler's
   words; do not
   promote an AI deduction or replay candidate without their confirmation.
4. Tools live in extension/fofuxo-bridge/; import llm_modeling_bridge.
   The [README](extension/fofuxo-bridge/README.md#session-tools) describes the
   APIs, [OPS.md](extension/fofuxo-bridge/OPS.md) is the short operator card,
   and [SESSION.md](skill/fofuxo-modeling-rules/SESSION.md) is the session card.
   Run the appropriate documented tests after changing the extension.
5. Only what is left goes here. Remove a finished item, renumber and update
   Order. A new need gets its scope and files to read. Use a small handoff
   instead of dragging tool-development history into modeling.
6. Code, comments, file names and public extension commits use English;
   talk with the modeler in Portuguese, with Blender terms in English.

## Principles

- **Wrap, don't rewrite.** Call Blender's tools for existing operations;
  new mesh algorithms are for what Blender lacks.
- **Keep what Blender lacks.** Stable ids, mesh text, validation, shape
  measures, targets and fitting remain the extension's job.
- **Every op is safe to try.** Check changes, preserve conflicts and explain
  results in numbers. An intentional tight loop is not automatically an error.
- **One line per edit.** Use existing operations, not a new session script.
  Summaries are the default; full receipts remain available on request.
- **Measure before promising.** Characters and pixels are useful receipts;
  they do not prove billed token savings or artistic success.

## To do

1. **Validate the tooling in a real human review.** Follow
   [HUMAN_TESTS.md](extension/fofuxo-bridge/HUMAN_TESTS.md). Read only the
   README's Session tools and the relevant test section. Check:
   - the recorder in Edit Mode and Sculpt (Grab and Smooth), with selected
     and moved ids, undo/redo and named regions;
   - pass-through key/button press and release, modifiers, surface hits,
     sampled drags and brush radius; compare provisional Grab commands
     against actual recorded vertex movements;
   - same-window editing, refusal of extension edits while the human holds
     it, saving and returning the window;
   - region membership through topology operators and absorb, cage labels,
     evenness thresholds, cropped Workbench views and cage overlay;
   - legacy save/reopen after metadata and sidecar migration.
   **Done when** the real review is judged usable and observed defects are
   fixed. Background checks cannot establish modal input or Sculpt fidelity.
   Verified: 26 focused recorder checks, 8 activation checks, real Grab and
   temporary Shift/Smooth, paired input releases, 11 Sculpt undo/redo inverse
   pairs, save/collect/close, modifier transfer and immutable examples. Region
   transfer kept all original ids and added 27 fresh ids. The replacement-M
   review retained 276 operators and movement snapshots for all 46 transforms.
   Its empty-region attribution summary defect was fixed with 5 pure checks;
   the real log now reports its 121 unattributed movement samples correctly.
   The identity-history correction passed 14 focused checks and the final real
   repeat: cut ids 281–288 survived undo/redo exactly, and the collected mesh
   agreed with the last recorded id set. No snapshot errors remained.
   Same-window Edit Mode and Sculpt passed extension-edit refusal, saved
   prompt return, synchronization and immutable examples. The Sculpt comparison
   retained 36 ids, topology, modifier settings, regions and loop annotations;
   six strokes matched the received mesh within 0.006432 mm per component.
   Real prompt return during an active Edit Mode translate also passed: the
   unfinished move was cancelled, the confirmed move was saved, all 36 ids,
   topology, modifiers, regions and seven loop marks survived, and the archived
   after-file matched the live object. The Windows cancellation uses targeted
   window messages with normal human input enabled; event simulation was rejected.
   Same-window object addition/removal also passed: the saved example retained
   the removed and added object statuses, the new cube's geometry and eight ids
   were saved, and TestMesh geometry, ids, labels, modifiers and regions were unchanged.
   After background MCP timeouts, the modeler authorized the existing catalog
   APIs through the interactive MCP for this comparison. The AI restart
   reconnected that MCP; the background timeout remains unexplained.
   **Remaining**, in order:
   - the labeled cage/result views and loop display are approved; focused
     Workbench crop and intentional-versus-unwanted spacing judgments for
     evenness warnings still need their separate verdict;
   - real legacy-copy migration with sidecar, normal save/reopen and unchanged
     geometry, modifiers, ids and labels;
   - normal shutdown with native diagnostics captured, then final focused
     checks and verification of the installed/generated extension package.
   Reject the unmatched Grab replay candidate; suggestions remain provisional.
   Also confirm the native shutdown diagnostic described in
   [IMPLEMENTATION.md](IMPLEMENTATION.md#verification) if it recurs. Its cause
   was not established by the passing assertions or the isolated catalog check.

2. **Finish the cowboy hat (C1) and judge the method** (D-065 to D-079).
   Read models/tasks/chapeu-cowboy/HANDOFF.md, the plan's Changes and only
   the decisions needed by the next stage. The historical recorder has a
   [compact receipt](models/tasks/chapeu-cowboy/ai/C1/recording-summary.json)
   and an [observed-method index](models/example/cowboy-hat/RECORDING.md).
   Left:
   - the modeler's approval of the side dent, then applying temporary Mirror Y;
   - thickness (Solidify after Subdivision), the band extracted from the
     crown's band row, buckle, tail (Mirror X and Subdivision), materials;
   - cage and result checks (D-078), including the new evenness receipts;
   - round_end, ai/C1/report.md with supplied cost data, and the modeler's
     verdict on the hat and method.
   **Done when** the modeler judges the hat good and the method approved.
   The old in-memory C1 round cannot be reconstructed by the new counters;
   historical usage stays unknown unless actual session usage is available.

3. **A second concept, chosen by the modeler.** Build with the reviewed
   staged method. Read the session card, its reference and relevant technique
   blocks. Test whether D-066 to D-079 and recorded techniques transfer with
   less explanation. Before reuse, compare body/attachment, depth,
   proportions, topology and modifier assumptions (D-063, D-064).
   The proposed checklist is not evidence of successful transfer.
   **Done when** the modeler judges the result and measured replay;
   unresolved method questions go to DECISIONS.md.

4. **Complete the human example catalog.** E1's top hat now has
   models/example/chapeu/measures.json; the bow already has its measures.
   The skirt ruffles still have no source file in the catalog. Obtain it,
   then store their measures and example entry. New absorbed reviews preserve
   before/after files, deltas and receipts under human/; interview the modeler
   about each correction's why and validate useful replay before promotion
   to a technique. C1's earlier log has counts but no historical moved-id or
   region receipts, so exact movements cannot be recovered from its summary.
   Read models/example/CATALOG.md, models/FEEDBACK.md and the affected
   example's EXAMPLE.md and edit.json.

5. **Demonstrate cost reduction with real session usage.** Read the README's
   Cost per round and Session tools. On the next reviewed stage, collect
   report characters, image pixels, external read receipts, agent text and
   actual supplied session tokens. Compare an equivalent stage against the
   old method: fewer calls alone do not establish savings. The target remains
   the T2 horns' reported 180–220k tokens per horn, not a promise.
   Remaining limits:
   - external reads and agent text need explicit receipts; the extension does
     not intercept unrelated agent tools or actual MCP output;
   - exact image billing and total session usage need provider/model telemetry;
     no supported source for those values is exposed to the extension, and
     they must not be guessed from pixels;
   - an end-to-end replay and second concept must show whether the technique
     library helps rather than repeating the T2 failures.
   **Done when** a reviewed model has attributable usage and a useful
   comparison, with unavailable values stated as unavailable.

## Order

| Step | What | Why first |
|---|---|---|
| 1 | Item 1: install the update and run human checks | the next stages rely on recording and handover |
| 2 | Item 5: begin receipts on the next reviewed stage | preserve measurements before claiming a saving |
| 3 | Item 2: finish the hat and judge the method | the open run still needs its verdict |
| 4 | Item 3: choose and build the second concept | tests transfer and technique reuse |
| 5 | Item 4: interview corrections and supply the ruffle file | depends on human provenance and missing data |
