"""Plot a complete cage view, its measured crop rectangle and matching close."""

import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
metadata_path = root / (sys.argv[1] if len(sys.argv) > 1 else "uniformity-context-close.json")
output_path = root / (sys.argv[2] if len(sys.argv) > 2 else "uniformity-context-close.png")
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
size, header = metadata["panel_size"], metadata["header"]
with Image.open(metadata["overview"]) as image:
    overview = image.crop((0, header, size, header + size)).convert("RGB")
with Image.open(metadata["detail"]) as image:
    detail = image.crop((0, header, size, header + size)).convert("RGB")
bounds = metadata["overview_bounds"]
box = (math.floor(bounds["left"]), math.floor(bounds["top"]),
       math.ceil(bounds["right"]), math.ceil(bounds["bottom"]))
overview = overview.crop(box)
figure = Image.new("RGB", (1640, 1040), "#f4f6fa")
drawing = ImageDraw.Draw(figure)
font_path = "C:/Windows/Fonts/segoeui.ttf"
header_font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 40)
title_font = ImageFont.truetype(font_path, 30)
body_font = ImageFont.truetype(font_path, 26)
drawing.text((40, 24), "Onde ficam f36 e f41 no chapéu", font=header_font, fill="#172b42")
drawing.text((40, 85), "O quadrado azul localiza a área ampliada à direita. As duas vistas têm o mesmo ângulo.",
             font=body_font, fill="#47586b")
positions = ((40, 180), (880, 180))
panel_size = 720
full_scale = min(panel_size / overview.width, panel_size / overview.height)
full_width, full_height = round(overview.width * full_scale), round(overview.height * full_scale)
offset_x = positions[0][0] + (panel_size - full_width) // 2
offset_y = positions[0][1] + (panel_size - full_height) // 2
drawing.rectangle((40, 180, 759, 899), fill="white")
figure.paste(overview.resize((full_width, full_height), Image.Resampling.LANCZOS), (offset_x, offset_y))
figure.paste(detail.resize((panel_size, panel_size), Image.Resampling.LANCZOS), positions[1])
drawing.text((40, 135), "1. Modelo completo — malha base", font=title_font, fill="#172b42")
drawing.text((880, 135), "2. A mesma área ampliada", font=title_font, fill="#172b42")
rectangle = metadata["rectangle"]
left = offset_x + (rectangle["x"] - box[0]) * full_scale
top = offset_y + (rectangle["y"] - box[1]) * full_scale
right = left + rectangle["width"] * full_scale
bottom = top + rectangle["height"] * full_scale
accent = "#007fc4"
drawing.line((right, top, 880, 180), fill=accent, width=2)
drawing.line((right, bottom, 880, 899), fill=accent, width=2)
drawing.rectangle((left, top, right, bottom), outline=accent, width=5)
drawing.rectangle((880, 180, 1599, 899), outline=accent, width=4)
detail_scale = panel_size / size
for face, color in (("36", "#2578c9"), ("41", "#dc7621")):
    polygon = [(880 + point[0] * detail_scale, 180 + point[1] * detail_scale)
               for point in metadata["face_polygons_detail"][face]]
    drawing.line(polygon + [polygon[0]], fill=color, width=4)
drawing.text((40, 934), "Localização no modelo inteiro", font=body_font, fill="#47586b")
drawing.text((880, 934), "f36: contorno azul   •   f41: contorno laranja", font=body_font, fill="#172b42")
figure.save(output_path)
