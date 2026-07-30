"""Unit tests for local setup UI service layer."""

from __future__ import annotations

from pathlib import Path

from dce.interfaces.web import service


def test_resolve_and_init_index_build(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert service.workspace_exists(root) is False
    init = service.init_payload(root, name="ui-demo")
    assert init["ok"] is True
    assert service.workspace_exists(root) is True

    seed = service.seed_sample_doc(root)
    assert seed["ok"] is True
    assert Path(seed["path"]).is_file()

    indexed = service.index_payload(root)
    assert indexed["ok"] is True
    assert indexed["total_upserted"] >= 1

    status = service.status_payload(root)
    assert status["ok"] is True
    assert status["initialized"] is True
    assert status["status"]["document_count"] >= 1

    built = service.build_payload(root, "ORA-12541")
    assert built["ok"] is True
    assert built["document_count"] >= 1

    mcp = service.mcp_config_payload(root, dce_command=r"C:\Tools\dce\dce.exe")
    assert mcp["ok"] is True
    assert "mcpServers" in mcp["config"]
    assert mcp["config"]["mcpServers"]["dce"]["command"].endswith("dce.exe")


def test_status_without_init(tmp_path: Path) -> None:
    status = service.status_payload(tmp_path / "missing")
    assert status["ok"] is False
    assert status["initialized"] is False
