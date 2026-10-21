# Roadmap

> [!IMPORTANT]
> **This file is written to be read and acted on by AI agents.** Read the
> remaining work here, take the next available step from [Order](#order),
> and keep this file true. Implemented tools belong in the extension README;
> this file contains only work and judgments still pending.

The aim: a text LLM can build an editable Blender model from an approved
plan, learn from human corrections and demonstrate a lower session cost.

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
   stays pending when the modeler is unavailable. When Order is empty there
   is no pending work: ask the modeler for the next goal, write it here with
   its scope and the files to read, then start.
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

1. **The window's arabesques** (`models/tasks/arabesco-janela/`). The modeler
   picked the gold ornament carved on the gothic window of the shop's entrance
   hall as the next work. The copy is
   `models/tasks/arabesco-janela/arabescos.blend`: the fleur-de-lis finial, the
   arch vine, the bottom band and the right capital leaves, with the window
   frame kept as a reference collection and the band's `Arabesco Base.png`
   packed. The stem `Plane.001` carries ten leaves, all connected (1 island,
   0 non-manifold): `Plane.020` by the modeler's hand, `Plane.019`, `.021`,
   `.022`, the three-lobe curl `.027`/`.029`/`.030` and the acanthus leaf
   `.026`/`.024`/`.025` at the stem's bend by the AI and corrected by the
   modeler (D-081 to D-092). 9 leaves of `Videira do Arco` are still separate
   objects (`Plane.023`, `.031` to `.037`, `.018`), all growing from the
   stem's lower part, `Plane.017`, now joined into `Plane.001` (its elbow and
   lower end are hidden in the scene, D-093). Each next leaf follows the recipes and closing checks in
   `extension/fofuxo-bridge/EDITING.md`, then a review; turn each correction
   into a rule or a call. Read that task's `prompt.md` and `report.md` first.
   **Done when** the modeler judges the arabesques good.

## Order

| Step | What | Why first |
|---|---|---|
| 1 | Item 1: continue the vine, leaf by leaf | the modeler's chosen work |

