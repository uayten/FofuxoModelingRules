# Task: the window's arabesques (ROADMAP item 1)

Copy of the gold ornament carved on the gothic window of the shop's entrance
hall, moved out of the shop scene into a file of its own so the ornament can
be worked on without the rest of the level.

- **Source:** `C:\UnityProjects\MyDragonShop\Docs\Loja\Loja.blend`, scene
  collection `Hall de Entrada > Janela`. The source file was read only; it was
  not saved or modified.
- **Work file:** `arabescos.blend` (3.0 MB, compressed). Evaluated geometry is
  identical to the source for all 48 meshes (same vertex counts and
  world-space digests). Nothing was applied: Mirror, Subdivision, Array and
  Smooth by Angle are live, as in the source.
- **Units:** metric, unit scale 1. The window is 0.886 m wide and 2.064 m tall;
  the ornaments are 2–6 mm thick plates on its inner face.

## Collections in the file

| Collection | Objects | What |
|---|---|---|
| `Arabescos > Florão` | `Circle.003`, `Circle.005`, `Circle.006` | fleur-de-lis finial over the arch peak |
| `Arabescos > Videira do Arco` | `Plane.017`–`Plane.027`, `Plane.029`–`Plane.037` (20) | leaf vine running down the right side of the arch |
| `Arabescos > Faixa Inferior` | `Plane.040`, `Plane.043`–`Plane.052` (11) | scroll band under the window, from `Arabesco Base.png` |
| `Arabescos > Capitéis` | `Cube.064`, `Cube.065`, `Roundcube.002`, `Roundcube.003` | leaf capital cluster on the right column |
| `Referência da Janela > Estrutura` | `Plane.011`–`Plane.016`, `Plane.038`–`Plane.042` (10) | frame, glass, columns, sill — context only |
| `Referência da Janela > Controles` | `Mirror` (empty at the world origin) | mirror plane `Plane.013` depends on |
| `Referências > Imagens` | `Empty.009` | the `Arabesco Base.png` reference, packed |

Materials: `M_Ouro` (the ornament), `M_Mármore` and `M_Vitral` (frame and
glass). The `Arabesco Base.png` image is packed; no path outside the file is
needed.

## State left by the source scene

- The vine exists only on the right side of the arch; `Plane.028` does not
  exist in the source. The left side of the arch is bare.
- `Plane.038` (glass), `Plane.039`, `Plane.041`, `Plane.042` (marble), `Plane.040`
  (band) and `Plane.049`, `Plane.050` (bottom corner leaves) were hidden in
  render in the source (`hide_render = True`). In this copy they are visible,
  so nothing is missing by accident; hide them again if they are placeholders.
- The band mirrors around `Plane.048` (its centre mullion); the corner leaves
  and the band share that mirror object.

## Open

The modeler has not said yet what "work on the arabesques" means for this
file: redraw a form, finish the missing left side, build a new piece, or match
`Arabesco Base.png` more closely. The goal is set in the conversation before a
plan is written.
