"""Localhost setup UI (stdlib HTTP) for non-CLI operators."""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from dce import __version__
from dce.domain.errors import WorkspaceError
from dce.interfaces.web import service


def _static_dir() -> Path:
    import sys

    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and isinstance(meipass, str):
        return Path(meipass) / "dce" / "interfaces" / "web" / "static"
    return Path(__file__).resolve().parent / "static"


def _json_bytes(payload: dict[str, Any], *, status: int = 200) -> tuple[int, bytes, str]:
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    return status, body, "application/json; charset=utf-8"


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    raw = handler.rfile.read(length) if length else b"{}"
    if not raw:
        return {}
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        msg = "JSON body must be an object"
        raise ValueError(msg)
    return data


def _html_page() -> bytes:
    return (_static_dir() / "index.html").read_bytes()


class SetupUIState:
    """Mutable wizard state shared by handler instances."""

    def __init__(self, workspace: Path, *, dce_command: str) -> None:
        self.workspace = workspace.resolve()
        self.dce_command = dce_command


def make_handler(state: SetupUIState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html"}:
                try:
                    self._send(200, _html_page(), "text/html; charset=utf-8")
                except OSError as exc:
                    status, body, ctype = _json_bytes(
                        {"ok": False, "error": f"UI assets missing: {exc}"},
                        status=500,
                    )
                    self._send(status, body, ctype)
                return
            if parsed.path == "/api/health":
                status, body, ctype = _json_bytes(
                    {
                        "ok": True,
                        "dce_version": __version__,
                        "workspace_path": str(state.workspace),
                        "bind": "127.0.0.1",
                    }
                )
                self._send(status, body, ctype)
                return
            if parsed.path == "/api/status":
                qs = parse_qs(parsed.query)
                raw_path = (qs.get("path") or [""])[0] or None
                path = service.resolve_workspace_path(
                    raw_path,
                    default=state.workspace,
                )
                state.workspace = path
                status, body, ctype = _json_bytes(service.status_payload(path))
                self._send(status, body, ctype)
                return
            if parsed.path == "/api/mcp-config":
                qs = parse_qs(parsed.query)
                raw_path = (qs.get("path") or [""])[0] or None
                path = service.resolve_workspace_path(
                    raw_path,
                    default=state.workspace,
                )
                command = (qs.get("command") or [state.dce_command])[0] or state.dce_command
                status, body, ctype = _json_bytes(
                    service.mcp_config_payload(path, dce_command=command)
                )
                self._send(status, body, ctype)
                return
            status, body, ctype = _json_bytes({"ok": False, "error": "Not found"}, status=404)
            self._send(status, body, ctype)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = _read_json(self)
            except (json.JSONDecodeError, ValueError) as exc:
                status, body, ctype = _json_bytes({"ok": False, "error": str(exc)}, status=400)
                self._send(status, body, ctype)
                return

            path = service.resolve_workspace_path(
                str(payload.get("path") or ""),
                default=state.workspace,
            )
            state.workspace = path

            try:
                if parsed.path == "/api/init":
                    name = payload.get("name")
                    force = bool(payload.get("force", False))
                    result = service.init_payload(
                        path,
                        name=str(name) if name else None,
                        force=force,
                    )
                    status, body, ctype = _json_bytes(result)
                    self._send(status, body, ctype)
                    return
                if parsed.path == "/api/seed-sample":
                    status, body, ctype = _json_bytes(service.seed_sample_doc(path))
                    self._send(status, body, ctype)
                    return
                if parsed.path == "/api/index":
                    source = payload.get("source")
                    result = service.index_payload(
                        path,
                        source=str(source) if source else None,
                    )
                    code = 200 if result.get("ok") else 400
                    status, body, ctype = _json_bytes(result, status=code)
                    self._send(status, body, ctype)
                    return
                if parsed.path == "/api/build":
                    text = str(payload.get("text") or "").strip() or "ORA-12541"
                    result = service.build_payload(path, text)
                    status, body, ctype = _json_bytes(result)
                    self._send(status, body, ctype)
                    return
                if parsed.path == "/api/set-workspace":
                    status, body, ctype = _json_bytes(
                        {
                            "ok": True,
                            "workspace_path": str(path),
                            "initialized": service.workspace_exists(path),
                        }
                    )
                    self._send(status, body, ctype)
                    return
            except WorkspaceError as exc:
                status, body, ctype = _json_bytes({"ok": False, "error": exc.message}, status=400)
                self._send(status, body, ctype)
                return
            except OSError as exc:
                status, body, ctype = _json_bytes({"ok": False, "error": str(exc)}, status=500)
                self._send(status, body, ctype)
                return

            status, body, ctype = _json_bytes({"ok": False, "error": "Not found"}, status=404)
            self._send(status, body, ctype)

    return Handler


def run_setup_ui(
    workspace: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    dce_command: str = "dce",
) -> None:
    """Serve the setup wizard (blocking)."""
    if host not in {"127.0.0.1", "localhost", "::1"}:
        msg = "Setup UI only binds to localhost for safety"
        raise ValueError(msg)

    state = SetupUIState(workspace, dce_command=dce_command)
    handler = make_handler(state)
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"dce ui {__version__} — open {url}", flush=True)
    print(f"workspace: {state.workspace}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        server.server_close()
