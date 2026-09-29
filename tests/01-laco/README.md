# T1: bow tie, with and without the skill

- **Date:** 2026-09-29
- **Model:** Sonnet 5.5 (subagent), one run per side.
- **Skill version:** commit `d2eb7cc`, without `fofuxo_lib` or the auditor.
- **Task:** model the red bow tie from the concept (`EUA-Frente.png`, packed in
  `start.blend`), about 13.5 cm wide.
- **Judging:** blind, labeled X and Y.

| Label | File | Run |
|---|---|---|
| X | `sem-regras.blend` | without the skill |
| Y | `com-regras.blend` | with `SKILL.md` |

## Measured

| | X (without) | Y (with) |
|---|---|---|
| Objects | 1 (`BowTie`, 3 shells) | 2 (`Laço`, `Laço Nó`, parented) |
| Stack | none | Mirror XYZ → Subdivision 2/2 |
| Cage | 168 vertices, 162 faces | 7 vertices, 3 faces per object |
| Evaluated faces | 162 | 768 |
| Triangles / n-gons / loose | 0 / 0 / 0 | 0 / 0 / 0 |
| Size (evaluated vertices) | 13.5 × 3.3 × 7.0 cm | 13.5 × 2.7 × 7.1 cm |
| Placement | on the chest, as in the concept | on the floor (Z = 0) |
| Names | English | Portuguese |

## Verdict

X was judged better: its shape matches the concept, and it has fewer visible
vertices. Y followed the structure (names, parent, live stack) but lost the
shape: its sparse cage plus Subdivision 2 made a "bone".

## Lessons, turned into rules

- D-032: shape comes first.
- D-033: the cage carries the silhouette, Subdivision only smooths.
- D-034: a symmetric baked mesh gets cut and mirrored.
- D-035: placement rule (provisional).
- "Look" step: compare over the concept in front ortho, and measure with code.

**Correction (found in run A3):** the first measurements used `obj.dimensions`,
which with GPU Subdivision measures the cage. Y's self-report (13.5 × 7.1 cm)
was right; the check was wrong (D-044).

## Run A2: revised skill (D-032 to D-035)

- **File:** `com-regras-v2.blend`, Sonnet 5.5, same prompt as run A.
- **Result:** `Laço` (29 cage vertices per 1/8) and `Laço Nó`, Mirror XYZ →
  Subdivision 1, on the chest. Size 13.5 × 3.3 × 7.3 cm, matching its report.
  `com-regras-v2.blend` now holds the modeler's manual edit; the original A2 is
  in `com-regras-v2.blend1`. 1024 evaluated faces. Silhouette overlap with the concept: 94.6%, as
  the model measured it.
- **Verdict:** good to edit, close to the modeler's modifier choices. Still out
  of shape, mainly after Subdivision: it misses the outer dents and the folds
  at the knot, and the wings do not narrow behind the knot.
- **Lessons:** D-036 (shading shows forms), D-037 (imagine hidden forms),
  D-038 (concept size wins), D-039 (tight loops), D-040 (silhouette check),
  D-041 (other views, round cross-sections), D-042 (validate objects alone,
  then together).
- **Manual edit test:** the modeler edited A2 by hand and got close to the bow
  shape in very few steps, "very, very, very superior" to editing a mesh
  without modifiers. The top view was still a square bone, where E1 converges
  to the center (a figure eight). The inner shading (folds) is expected to stay
  hard for models.

## Run A3: Opus 5.5, build + self-critique (D-036 to D-043)

- **Files:** `com-regras-v3-antes.blend` (first version), `com-regras-v3.blend`
  (after one self-critique pass). Screenshots `A3-antes-*` / `A3-depois-*`.
- **Result:** `Laço` (71 cage vertices per 1/8) and `Laço Nó` (37), Mirror XYZ
  → Subdivision 1, on the chest. 12.35 × 2.9 × 6.53 cm, sized to the concept
  (12.4 × 6.5). Silhouette overlap 93.8%. Outer dent, X behind the knot and the
  figure eight from the top are present; the horizontal fold is weak; the
  radial gathering at the knot is missing.
- **Density:** 2656 evaluated faces, against 768 in E1 and 1024 in A2.
- **Self-critique causes it found:**
  - EXECUTION: loops too far apart to hold the fold (D-039 existed, not
    applied); wings hiding the knot's sides; flipped face order making a
    false crease.
  - PERCEPTION: missed the radial gathering where the wing enters the knot.
  - RULE: `obj.dimensions` measures the cage under GPU Subdivision (became
    D-044); Mirror merge can weld rows placed very close to the mirror plane.
- **Its recommendations, ranked:** a side or 3/4 concept view; `octant_cage`
  and `fit_rim` helpers; measure from evaluated vertices; audit open edges and
  occlusion between parts; concrete numbers for "tight loops"; compare model
  and concept side by side at the same scale.
- **Cost:** about 14 minutes and 187k tokens.

## Caveats

- n = 1 per side.
- `SKILL.md` described the E1 bow (1/8 mirror, `Laço Nó`), so Y's structure was
  partly copied.
