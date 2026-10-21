"""Run Python inside the open Blender through its MCP socket.

The Blender Lab MCP addon listens on a local TCP port and executes Python in
Blender's own thread. This is the same channel the ``blender_mcp`` client uses;
talking to it directly keeps the bridge reachable from a shell or an agent
session that has no MCP tool of its own.

Usage::

    python tools/blender_exec.py -c "import bpy; result = {'file': bpy.data.filepath}"
    python tools/blender_exec.py script.py
    python tools/blender_exec.py -                 # code from stdin

The code must leave a JSON-serializable dict in ``result``. That is the
addon's contract: it returns ``{"status": "ok", "result": ...}`` or
``{"status": "error", "message": ...}``.

Exit codes: 0 when the request ran, 1 when it failed, 2 when no Blender
answered.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876
DEFAULT_TIMEOUT = 120.0
MAX_BYTES = 64 * 1024 * 1024


def run(code: str, host: str, port: int, timeout: float) -> dict:
    """Send one ``execute`` request and return the decoded response."""
    request = json.dumps({"type": "execute", "code": code, "strict_json": False})
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall((request + "\0").encode("utf-8"))
        chunks = bytearray()
        while b"\0" not in chunks:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.extend(chunk)
            if len(chunks) > MAX_BYTES:
                raise RuntimeError("response exceeded {:d} bytes".format(MAX_BYTES))
    raw = bytes(chunks).split(b"\0", 1)[0]
    if not raw:
        raise RuntimeError("the Blender server closed the connection without a response")
    return json.loads(raw.decode("utf-8", "replace"))


def read_code(args: argparse.Namespace) -> str:
    if args.code:
        return args.code
    if args.path is None or args.path == "-":
        data = sys.stdin.read()
        if not data.strip():
            raise SystemExit("no code: pass -c, a file path, or stdin")
        return data
    try:
        with open(args.path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise SystemExit("cannot read {:s}: {:s}".format(args.path, str(exc)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", help="file with the code; '-' or empty reads stdin")
    parser.add_argument("-c", "--code", help="code to run, instead of a file")
    parser.add_argument("--host", default=os.environ.get("BLENDER_MCP_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("BLENDER_MCP_PORT", DEFAULT_PORT)))
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--compact", action="store_true", help="print the response on one line")
    args = parser.parse_args(argv)

    code = read_code(args)
    try:
        response = run(code, args.host, args.port, args.timeout)
    except (ConnectionRefusedError, socket.timeout, OSError) as exc:
        print(
            "no Blender answered on {host}:{port} ({error}). Start the AI instance with:\n"
            "  python extension/fofuxo-bridge/launcher.py <file.blend> --native-log <log>".format(
                host=args.host, port=args.port, error=exc
            ),
            file=sys.stderr,
        )
        return 2

    indent = None if args.compact else 2
    print(json.dumps(response, ensure_ascii=False, indent=indent))
    return 0 if response.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
