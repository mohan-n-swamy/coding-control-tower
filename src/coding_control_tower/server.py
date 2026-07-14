"""Local-only HTTP server for bundled dashboard resources."""

from __future__ import annotations

import contextlib
import mimetypes
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import Config
from .paths import snapshot_path, static_dir
from .scan import scan


class TowerHandler(BaseHTTPRequestHandler):
    server_version = "CodingControlTower/0.1"

    def do_GET(self) -> None:  # noqa: N802
        route = urllib.parse.urlparse(self.path).path
        if route == "/state.json":
            path = snapshot_path()
            if not path.exists():
                self.send_error(404, "Run coding-control-tower scan first")
                return
            self._send(path.read_bytes(), "application/json; charset=utf-8", no_store=True)
            return
        relative = "index.html" if route in ("", "/") else route.lstrip("/")
        if ".." in relative.split("/"):
            self.send_error(400, "Invalid path")
            return
        resource = static_dir().joinpath(*relative.split("/"))
        try:
            if not resource.is_file():
                self.send_error(404)
                return
            content_type = mimetypes.guess_type(relative)[0] or "application/octet-stream"
            self._send(resource.read_bytes(), content_type)
        except OSError:
            self.send_error(404)

    def _send(self, data: bytes, content_type: str, no_store: bool = False) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if no_store:
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, _format: str, *_args) -> None:
        return


def _refresh_loop(config: Config, stop: threading.Event) -> None:
    while not stop.wait(30):
        with contextlib.suppress(Exception):
            scan(config, refresh_github=False)


def serve(config: Config, open_browser: bool = True) -> None:
    scan(config, refresh_github=False)
    server = ThreadingHTTPServer(("127.0.0.1", config.port), TowerHandler)
    stop = threading.Event()
    worker = threading.Thread(target=_refresh_loop, args=(config, stop), daemon=True)
    worker.start()
    url = f"http://127.0.0.1:{config.port}/"
    if open_browser:
        threading.Timer(0.2, lambda: webbrowser.open(url)).start()
    print(f"Coding Control Tower: {url}")
    print("Local-only. Press Ctrl-C to stop.")
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=2)

