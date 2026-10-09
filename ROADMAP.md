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

1. **Finish the cowboy hat (C1) and judge the method** (D-065 to D-079).
   Read models/tasks/chapeu-cowboy/HANDOFF.md, the plan's Changes and only
   the decisions needed by the next stage. The historical recorder has a
   [compact receipt](models/tasks/chapeu-cowboy/ai/C1/recording-summary.json)
   and an [observed-method index](models/example/cowboy-hat/RECORDING.md).
   Left:
   - the band extracted from the crown's band row (`ring v12-v62`, 12 faces,
     previewed, not yet extracted), buckle, tail (Mirror X and Subdivision),
     materials;
   - cage and result checks (D-078), including the new evenness receipts;
   - resume the checkpointed round `C1 side dent review` (`round_resume`),
     round_end, ai/C1/report.md with supplied cost data, and the modeler's
     verdict on the hat and method.
   **Done when** the modeler judges the hat good and the method approved.
   The old in-memory C1 round cannot be reconstructed by the new counters;
   historical usage stays unknown unless actual session usage is available.

2. **A second concept, chosen by the modeler.** Build with the reviewed
   staged method. Read the session card, its reference and relevant technique
   blocks. Test whether D-066 to D-079 and recorded techniques transfer with
   less explanation. Before reuse, compare body/attachment, depth,
   proportions, topology and modifier assumptions (D-063, D-064).
   The proposed checklist is not evidence of successful transfer.
   **Done when** the modeler judges the result and measured replay;
   unresolved method questions go to DECISIONS.md.

3. **Complete the human example catalog.** E1's top hat now has
   models/example/chapeu/measures.json; the bow already has its measures.
   The skirt ruffles still have no source file in the catalog. Obtain it,
   then store their measures and example entry. New absorbed reviews preserve
   before/after files, deltas and receipts under human/; interview the modeler
   about each correction's why and validate useful replay before promotion
   to a technique. C1's earlier log has counts but no historical moved-id or
   region receipts, so exact movements cannot be recovered from its summary.
   Read models/example/CATALOG.md, models/FEEDBACK.md and the affected
   example's EXAMPLE.md and edit.json.

4. **Demonstrate cost reduction with real session usage.** Read the README's
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
| 1 | Item 4: begin receipts on the next reviewed stage | preserve measurements before claiming a saving |
| 2 | Item 1: finish the hat and judge the method | the open run still needs its verdict |
| 3 | Item 2: choose and build the second concept | tests transfer and technique reuse |
| 4 | Item 3: interview corrections and supply the ruffle file | depends on human provenance and missing data |
