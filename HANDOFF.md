# Handoff

Updated: 2026-10-21

## State
- No modeling run has started. The modeler dropped the earlier work (bow tie,
  horns, cowboy hat, goggles); their files remain under `models/`, untouched.
- New work: the window's arabesques, copied out of
  `C:\UnityProjects\MyDragonShop\Docs\Loja\Loja.blend` into
  `models/tasks/arabesco-janela/arabescos.blend` (3.0 MB; every mesh's
  evaluated geometry verified identical to the source; reference images
  packed). The task's `prompt.md` lists what is in the file and what the
  source scene left hidden.
- Extension 0.2.1 is validated in real human reviews; the generated ZIP and
  the installed copy match the source. `main` holds the committed work up to
  `af94760`; the roadmap rewrite and this file are still uncommitted.

## Next step
Agree with the modeler what "working on the arabesques" means for this file
(finish the bare left side of the arch, redo the vine, match the `Arabesco
Base.png` band), then write the plan (`skill/fofuxo-modeling-rules/PLAN.md`),
review it, `round_start` and build stage by stage. The vine exists on the
right side of the arch only; `Plane.028` does not exist in the source.

## Open questions
- What the ornament work is: finish the missing left side, redo a form, or
  build something new for the window.

## Environment (2026-10-21)
- The agent session (DeepSeek Harness) has no Blender MCP tool. The addon's
  socket is reached with `python tools/blender_exec.py -c "<code>"` instead:
  same TCP protocol, code executed in Blender's thread. `result` must be a
  JSON-serializable dict.
- AI Blender started by the launcher on `arabescos.blend`; `llm_modeling_bridge`
  reports `role = ai`, `mcp_running = True`. One Blender per port: a second
  instance does not get 9876.
- `AGENTS.md` mirrors the global Claude memory; `.agents/skills/` holds the
  copied Claude skills (project-docs, roadmap, comment-replies, pull-requests,
  blender-pull-requests) and the session catalog picks them up without a
  restart. Claude Code plugins were not copied: they are not DSH packages.

## Notes for the next session
- Open the AI Blender with
  `python extension/fofuxo-bridge/launcher.py <file> --native-log <new log>`.
- The background MCP tool (`execute_blender_code_for_cli`) timed out before;
  use the interactive MCP.
- `mirror_object` references matter: `Plane.013` mirrors around the `Mirror`
  empty at the world origin, and the band mirrors around `Plane.048`. Keep both
  in the file.

## Read first
`ROADMAP.md` item 1, `models/tasks/arabesco-janela/prompt.md`,
`skill/fofuxo-modeling-rules/SESSION.md`, `extension/fofuxo-bridge/OPS.md`.
