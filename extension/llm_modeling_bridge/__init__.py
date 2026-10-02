"""Repository import entry point for the extension's Blender package id."""

from pathlib import Path

_source = Path(__file__).resolve().parent.parent / "fofuxo-bridge"
__path__ = [str(_source)]
__file__ = str(_source / "__init__.py")
exec(compile(Path(__file__).read_text("utf-8"), __file__, "exec"), globals())
