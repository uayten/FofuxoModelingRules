"""Compatibility launcher; the implementation lives in fofuxo-bridge."""

from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent.parent / "fofuxo-bridge" / "launcher.py"), run_name="__main__")
