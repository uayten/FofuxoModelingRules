# Learning from the modeler

How human knowledge enters this repository: interviews about examples, and
feedback on AI models. Every item is filtered before it becomes a rule.

## Contents

- [Interview on an example](#interview-on-an-example)
- [Feedback on an AI model](#feedback-on-an-ai-model)
- [The filter](#the-filter)
- [Where things go](#where-things-go)
- [Session brief (NEXT.md)](#session-brief-nextmd)

## Interview on an example

1. The modeler hands over the file and a free description.
2. The AI measures first (stack, counts, sizes, edge data, poles, transforms)
   and never asks what it can measure. It writes its deductions in the
   example's `EXAMPLE.md`, each with its evidence and status *pending*.
3. The AI asks one subject at a time: why each choice was made, and for each
   deduction, "was this on purpose?".
4. For every answer, the question that decides where it goes: **always, always
   for this kind of part, or only here?**
5. Answers are kept in the modeler's words (quoted) and filtered below.

## Feedback on an AI model

After each AI modeling session, feedback goes into the run's `feedback.md`.
Two sources:

- **What the modeler says or writes.**
- **What the modeler edits in Blender.** Fofuxo Cage shows which vertices
  moved and by how much (in permille of the frame). The AI proposes the reason
  ("the whole L1 rim went up 4% → the silhouette was low") and asks.

Each item records: the modeler's words, what the AI understood, the class, and
the destination.

## The filter

| Class | When | Goes to |
|---|---|---|
| Rule | the modeler states it as general practice | `DECISIONS.md` as Stated, then `SKILL.md` |
| Provisional | seen once; unknown whether it generalizes | `DECISIONS.md` as Provisional; becomes Stated on a second matching case |
| Specific | true for this model only | the example's `EXAMPLE.md` |
| Coincidence | an accident of the file (a name, a threshold) | Coincidences in `DECISIONS.md` |
| Tool | about how the AI sees or edits, not about modeling | Fofuxo Cage (`extension/fofuxo_cage/`) |
| Discarded | see below; the reason is recorded | stays in `feedback.md` only |

Questions that weigh an item:

- **General?** Does it hold outside this model? Ask; never assume.
- **Evidence?** Can it be seen or measured in the file?
- **Actionable?** "Make it cuter" does not enter until it becomes "which
  vertices, how much".
- **Conflict?** If it contradicts a D-xxx, it is not discarded: ask which one
  wins, and the new rule replaces the old one on record (as D-033 replaced the
  first draft).
- **Repeated?** A second matching case promotes Provisional to Stated.
- **Source?** An AI deduction never becomes a rule without the modeler's
  confirmation.

Discard when: still vague after asking; a taste of the moment the modeler does
not want as a rule; the AI misread; out of scope (rig, D-017).

## Where things go

- A rule change is always proposed to the modeler first, never made silently.
- `DECISIONS.md` keeps the why; `SKILL.md` keeps only the rule.
- The catalog status of an example moves forward (`CATALOG.md`) as it is
  measured, interviewed and validated.

## Session brief (NEXT.md)

At the end of each session on a run, the AI writes `ai/<run>/NEXT.md`, and
the next session reads it first, instead of the whole history (fewer tokens;
`ROADMAP.md`, Part 2, item 7). The modeler may edit it. Sections:

- **Open items**: the feedback items and questions still waiting, by number;
- **Read first**: the files (and sections) the next session needs, nothing
  more;
- **Measures to trust**: the numbers already taken (`measures.json`, the
  task's targets and their last result), so they are not measured again;
- **Do not touch**: files that are records (the modeler's edits, a finished
  round's `.blend`);
- **Start**: the file to open and the first call.

Each round's `report.md` ends with its cost: `fofuxo_cage.round_start(label)`
when the round begins, `round_end(tokens=...)` when it ends (the tokens from
the session's usage); the `report_line` goes in the report (ROADMAP, Part 2,
item 8).
