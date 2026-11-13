"""Local playground for the Python interfacial SVG builder and TS renderer.

Run from the repository root:
    PYTHONPATH=packages/python/src python examples/standalone/interfacial_svg_playground/server.py
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

EXAMPLE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = EXAMPLE_ROOT.parents[2]
PYTHON_SOURCE = REPOSITORY_ROOT / "packages" / "python" / "src"
if str(PYTHON_SOURCE) not in sys.path:
    sys.path.insert(0, str(PYTHON_SOURCE))

from lmmp_charts.models import Wettability  # noqa: E402
from lmmp_charts.rendering.svg import InterfacialBuilder  # noqa: E402

CONFIG_PATH = REPOSITORY_ROOT / "examples" / "interface_config.json"
TYPESCRIPT_DIST = REPOSITORY_ROOT / "packages" / "typescript" / "dist"
MAX_BODY_BYTES = 64 * 1024


def generate_svg_document(config: dict[str, Any]) -> dict[str, Any]:
    """Validate domain input and build the versioned parametric SVG document."""
    model = Wettability.from_dict(config)
    return InterfacialBuilder().build(model).to_dict()


def reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON numeric constant: {value}")


class PlaygroundHandler(BaseHTTPRequestHandler):
    """Same-origin API and static assets for local evaluation."""

    server_version = "LMMPChartsSvgPlayground/0.1"

    def _respond(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._respond(status, data, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        assets = {
            "/": (EXAMPLE_ROOT / "index.html", "text/html; charset=utf-8"),
            "/index.html": (EXAMPLE_ROOT / "index.html", "text/html; charset=utf-8"),
        }
        if path == "/api/example":
            self._respond(200, CONFIG_PATH.read_bytes(), "application/json; charset=utf-8")
            return
        if path.startswith("/typescript/"):
            relative = unquote(path.removeprefix("/typescript/"))
            file_path = (TYPESCRIPT_DIST / relative).resolve()
            try:
                file_path.relative_to(TYPESCRIPT_DIST.resolve())
            except ValueError:
                self._json(404, {"error": "Resource not found."})
                return
            if file_path.suffix != ".js" or not file_path.is_file():
                self._json(404, {"error": "Resource not found."})
                return
            self._respond(200, file_path.read_bytes(), "application/javascript; charset=utf-8")
            return
        asset = assets.get(path)
        if asset is None:
            self._json(404, {"error": "Resource not found."})
            return
        file_path, content_type = asset
        self._respond(200, file_path.read_bytes(), content_type)

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/api/svg":
            self._json(404, {"error": "Resource not found."})
            return
        if "application/json" not in self.headers.get("Content-Type", ""):
            self._json(415, {"error": "Content-Type must be application/json."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "Invalid Content-Length."})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._json(413, {"error": "Payload must be between 1 and 65536 bytes."})
            return
        try:
            config = json.loads(
                self.rfile.read(length).decode("utf-8"),
                parse_constant=reject_nonfinite_constant,
            )
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self._json(400, {"error": "Invalid JSON body."})
            return
        try:
            document = generate_svg_document(config)
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            self._json(422, {"error": str(exc)})
            return
        self._json(200, document)


def main() -> None:
    parser = argparse.ArgumentParser(description="LMMP Charts: standalone SVG playground")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if not (1 <= args.port <= 65535):
        parser.error("port must be between 1 and 65535")
    with ThreadingHTTPServer(("127.0.0.1", args.port), PlaygroundHandler) as server:
        print(f"LMMP Charts SVG playground: http://127.0.0.1:{args.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
