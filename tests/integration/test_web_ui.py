"""HTTP API smoke for local setup UI."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

from dce.interfaces.web.server import SetupUIState, make_handler


def _serve(tmp_path: Path) -> tuple[ThreadingHTTPServer, str]:
    state = SetupUIState(tmp_path, dce_command="dce")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, f"{host}:{port}"


def test_ui_http_wizard_flow(tmp_path: Path) -> None:
    server, authority = _serve(tmp_path / "ws")
    try:
        conn = HTTPConnection(authority, timeout=5)

        conn.request("GET", "/api/health")
        health = json.loads(conn.getresponse().read().decode())
        assert health["ok"] is True

        conn.request("GET", "/")
        home = conn.getresponse()
        assert home.status == 200
        assert b"Dev Context Engine" in home.read()

        workspace = str((tmp_path / "ws").resolve())
        body = json.dumps({"path": workspace, "name": "ui"}).encode()
        conn.request(
            "POST",
            "/api/init",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        init = json.loads(conn.getresponse().read().decode())
        assert init["ok"] is True

        body = json.dumps({"path": workspace}).encode()
        conn.request(
            "POST",
            "/api/seed-sample",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        assert json.loads(conn.getresponse().read().decode())["ok"] is True

        conn.request(
            "POST",
            "/api/index",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        indexed = json.loads(conn.getresponse().read().decode())
        assert indexed["ok"] is True
        assert indexed["total_upserted"] >= 1

        conn.request("GET", f"/api/status?path={workspace}")
        status = json.loads(conn.getresponse().read().decode())
        assert status["initialized"] is True
        assert status["status"]["document_count"] >= 1

        conn.request("GET", f"/api/mcp-config?path={workspace}&command=C:/Tools/dce/dce.exe")
        mcp = json.loads(conn.getresponse().read().decode())
        assert "mcpServers" in mcp["config"]

        conn.request("GET", "/api/steering")
        steering = json.loads(conn.getresponse().read().decode())
        assert steering["ok"] is True
        assert "build_context" in steering["steering_markdown"]

        build_body = json.dumps({"path": workspace, "text": "ORA-12541"}).encode()
        conn.request(
            "POST",
            "/api/build",
            body=build_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(build_body)),
            },
        )
        built = json.loads(conn.getresponse().read().decode())
        assert built["document_count"] >= 1
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
