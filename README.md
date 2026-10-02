# Fofuxo Modeling Rules

> [!TIP]
> Versão em português aqui → [README.pt-BR.md](README.pt-BR.md) (README em português)

Tools and modeling rules for building editable Blender models together with a text LLM.

- Edit meshes and modifiers through checked, one-line Blender operations.
- Name regions, measure shape and mesh spacing, and render a single view of the changed part.
- Record human corrections, keep before/after examples, and summarize operators and gestures.
- Track report and image volume, and resume a stage from a small handoff.

## Contents

- [Use](#use)
- [Development](#development)
- [Current status](#current-status)
- [References](#references)

## Use

The Blender extension is **LLM Modeling Bridge**. Its source is in
[`extension/fofuxo-bridge/`](extension/fofuxo-bridge/README.md), with the package id
`llm_modeling_bridge`. Build its installable archive with
`python extension/package_extension.py`, then install that archive in Blender.
The [extension README](extension/fofuxo-bridge/README.md) explains the APIs,
automatic legacy migration, and tests.

The modeling workflow is in [`skill/fofuxo-modeling-rules/SKILL.md`](skill/fofuxo-modeling-rules/SKILL.md).
Start with its [short session card](skill/fofuxo-modeling-rules/SESSION.md),
then read only the sections relevant to the current stage.

## Development

Read [`ROADMAP.md`](ROADMAP.md) before choosing work. Read only the files and
decisions named by the item. Tests use temporary copies; the original human
examples and open modeling runs are preserved.

Code, comments and public extension commits use English. Conversation with
the modeler uses Portuguese. Human judgments and interviews remain the source
of modeling rules: an untested replay candidate is not an approved technique.

## Current status

The tooling update is ready for the [human checks](extension/fofuxo-bridge/HUMAN_TESTS.md).
The [implementation report](IMPLEMENTATION.md) records delivered features,
test coverage and the unconfirmed native shutdown diagnostic from one test run.
The cowboy hat still awaits its stage reviews and final judgment. A second
concept and the skirt-ruffle reference file are also pending.
Character counts and image pixels are receipts, not billed token estimates.

## References

- [Portuguese project overview](README.pt-BR.md)
- [Modeling decisions](DECISIONS.md)
- [Human example catalog](models/example/CATALOG.md)
- [Techniques](models/TECHNIQUES.md)
- [How feedback becomes a rule](models/FEEDBACK.md)
