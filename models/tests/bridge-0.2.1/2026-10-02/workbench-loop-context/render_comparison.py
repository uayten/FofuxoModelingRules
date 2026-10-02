"""Plot the measured camera crop beside the complete Workbench result."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
rectangle = json.loads((root / "crop-location.json").read_text(encoding="utf-8"))["rectangle"]
figure = Image.new("RGB", (1600, 1040), "#f4f6fa")
drawing = ImageDraw.Draw(figure)
font_path = "C:/Windows/Fonts/segoeui.ttf"
header_font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 40)
title_font = ImageFont.truetype(font_path, 30)
body_font = ImageFont.truetype(font_path, 26)
drawing.text((40, 24), "O teste é o enquadramento da imagem", font=header_font, fill="#172b42")
drawing.text((40, 86), "O quadro azul localiza o recorte. A malha é a mesma nas duas imagens.",
             font=body_font, fill="#47586b")
size = 720
positions = ((40, 180), (840, 180))
sources = (root / "model.workbench.high.png", root.parent / "workbench-loop-review" / "model.workbench.high.png")
for position, source, title in zip(positions, sources,
                                   ("1. Modelo inteiro", "2. A área do quadro azul, ampliada")):
    with Image.open(source) as picture:
        figure.paste(picture.convert("RGB").resize((size, size), Image.Resampling.LANCZOS), position)
    drawing.text((position[0], 135), title, font=title_font, fill="#172b42")
scale = size / 768
left = positions[0][0] + rectangle["x"] * scale
top = positions[0][1] + rectangle["y"] * scale
drawing.rectangle((left, top, left + rectangle["width"] * scale, top + rectangle["height"] * scale),
                  outline="#28dcff", width=5)
drawing.rectangle((840, 180, 1559, 899), outline="#28dcff", width=5)
drawing.text((40, 930), "Avalie: a ampliação ajuda a inspecionar essa região ou corta contexto demais?",
             font=body_font, fill="#172b42")
figure.save(root / "workbench-crop-explanation.png")
