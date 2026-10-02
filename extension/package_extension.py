"""Build an installable Blender extension archive from the canonical source folder."""

from pathlib import Path
import tomllib
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
source = root / "fofuxo-bridge"
manifest = tomllib.loads((source / "blender_manifest.toml").read_text("utf-8"))
destination = root / "dist" / f"{manifest['id']}-{manifest['version']}.zip"
destination.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for path in sorted(source.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and "tests" not in path.relative_to(source).parts and path.suffix != ".pyc":
            archive.write(path, path.relative_to(source).as_posix())
print(destination)
