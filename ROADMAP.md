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
2. **A one-page junction checklist and a scoped report.** The modeler found
   the leaf-by-leaf modeling too slow and too costly in tokens (each leaf took
   20 to 80 minutes from start to the modeler's correction, see the task's
   `report.md`). Distill D-080 to D-093 and `EDITING.md` into one page an
   agent reads instead of them (recipe: fork or side branch, `lift_crotch`, a
   stem loop each side, base rows level with the stem's, `crease_border`,
   closing checks). Scope `topology_report` to the new leaf's ids and the
   stem band near it (`Plane.001.txt` is 38 KB and grows per leaf). Use both
   on the next leaf of item 1 and note its minutes of correction and session
   cost. **Done when** the modeler judges the next leaf no worse for it.
3. **`connect_leaf`: one call for the fixed part of a junction.** A bridge
   call such as `connect_leaf(stem, leaf, recipe)` doing the join, the
   junction rules and the crease, so the model only picks the recipe and
   checks one image. Built from item 2's checklist, tested like any bridge
   call, then used on a leaf of item 1. **Done when** the modeler approves
   the call on a leaf.
4. **[research] Jev for the recipe choice.** The modeler describes Jev as a
   typed-decision model by TypeSafe AI ("System 1": context in, typed answer
   out). Answer: does it exist, how is it called (API, cost, local or not),
   and can it pick a leaf's recipe (fork or side branch) as a typed answer
   from item 2's scoped report. **Done when** the answer is in DECISIONS with
   its source, and the modeler decides whether it enters item 3.
   Found (2026-10-21, web search, vendor-reported): Jev exists, launched
   September 2026; input state plus typed questions (Choice, Score, yes/no)
   in, answers with per-option probabilities out; access by early-access
   waitlist; reported price $0.042 per million input tokens, output free.
   Sources: nexos.ai/blog/what-is-jev, siliconangle.com 2026-09-16, vktr.com.
   Left: get access, then try a Choice question on the reports of the leaves
   already done (their recipes are known) before a new one.
5. **A Sonnet executor for the leaves** (not a priority). A Sonnet subagent
   gets the checklist and the leaf, runs the bridge calls and `views()`, and
   returns only counts and the image path; the main model checks the image
   and opens the review. Haiku is not a candidate: picking ids from the
   geometry is its weak spot. **Done when** a leaf done this way costs less
   for the same correction time, by the modeler's judgment.
6. **Review what is left to prune** (not a priority, by the modeler). Each
   needs the modeler's word before it goes:
   - `extension/fofuxo_cage/`: the compatibility import and launcher for
     scripts written before the rename; `tests/test_roadmap.py` and the
     cowboy hat's plans still call `fofuxo_cage`.
   - The older tasks `models/tasks/chapeu-cowboy`, `chifre`, `laco` and
     `oculos-ferreiro`: still useful, or history only.
   - `AGENTS.md` and `.agents/skills/`: copies of the modeler's global rules
     and skills for another agent.

   **Done when** the modeler has decided each one.

## Order

| Step | What | Why first |
|---|---|---|
| 1 | Item 2: junction checklist and scoped report | makes every remaining leaf cheaper |
| 2 | Item 1: next leaf (`Plane.023`) with item 2 | the modeler's chosen work; tests item 2 |
| 3 | Item 4: research Jev | its answer decides part of item 3 |
| 4 | Item 3: `connect_leaf` | needs item 2's checklist; leaves of item 1 to test on |
| 5 | Item 1: the other leaves | the modeler's chosen work |
| 6 | Item 5: Sonnet executor | not a priority, by the modeler |
| 7 | Item 6: review what is left to prune | not a priority, by the modeler |

