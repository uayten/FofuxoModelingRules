# The build plan

Written before any modeling call (SKILL, step 5), as `plan.md` next to the
`.blend`. It turns the reading into the exact work: which parts, which
modifiers in which order, which commands, what each command should give, how
it is checked and what it may cost. A round that follows a plan runs its
commands instead of finding them by trial, which is where the tokens go.

`fofuxo_cage.round_start(label, plan="<path>/plan.md")` refuses a plan that
misses a section or the budget; every sync then warns (`round_budget`) once a
count passes the budget, and `round_end` puts the plan beside what was done.

## The sections

Copy the skeleton below and fill every section. Numbers, not adjectives:
"a brim 120 mm across", not "a wide brim".

~~~markdown
# Plan: <part or object> (<run or round>)

## Read
- Scale: <mm per px of the concept>; the body against the concept: <the
  landmark compared, the gap in mm and what moves> (D-063).
- The part as drawn: <visible size in mm, turning points of the outline>.
- What the 3D needs (D-064): <base width × depth, how it tapers, what goes on
  behind a covering part>; the side and top views in numbers.

## Parts
| part | primitive, size (mm), vertices | at (mm) | on / parent | collection, material |

## Stack
Per part, in order: modifier, its settings, why (rule number).

## Commands
Numbered, in order, each the exact call or text line and what it should give
(counts, the ring it makes, the size it reaches). Group them in stages; each
stage ends with one check from Checks.
1. `start_part("<name>", "cylinder", size=(..), vertices=8, at=(..), on="<body>")`: 8 sides, caps of quads
2. `edit("<name>", "mesh loopcut_slide ring v0-v1 number_cuts=4")`: 6 rings, L1 at the base
3. `edit("<name>", "mesh resize L2 w=150% d=150% around=selection")`: the brim 120 mm across
...

## Checks
After which stage, which measure or render, and the number it must give
(with a tolerance). One render per stage at most: views of the stage's part
with the body around it; measures (`sections(name, "rings")`, `profile`,
sizes) are cheaper than renders.

## Budget
```budget
syncs 12
ops 30
renders 5
measures 8
minutes 15
```

## Risks
What may not work as planned, and the fallback.

## Changes
Filled while building: each step that left the plan, and why. A check that
fails twice in a row stops the build: write here what it showed, revise the
plan, then go on.
~~~

## Where the commands come from

- The ops: the README's op tables (`extension/fofuxo_cage/README.md`, "Mesh
  op"), or `fofuxo_cage.mesh_help()` for the whitelist with its parameters.
  Read only the rows the plan uses.
- Shaping a ring on a bent part: `mesh translate <L>`, `mesh rotate <L>
  angle= axis=`, `mesh resize <L> ... around=selection`.
- Modifiers: `add <TYPE>`, `set <Modifier> <property> <value>`.
- A command not in the whitelist is a gap: say so in Risks, do not script
  around it without writing why in Changes.
