"""WorkspaceStatusResult aligns with doctor --json."""

from __future__ import annotations

from pathlib import Path

from dce.infrastructure.storage.workspace import doctor_workspace, init_workspace
from dce.interfaces.mcp.schemas import WorkspaceStatusResult


def test_workspace_status_from_doctor_report(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    init_workspace(root)
    report = doctor_workspace(root)
    status = WorkspaceStatusResult.from_doctor_report(report)
    assert status.schema_version == "1"
    assert status.healthy is True
    assert status.mcp.primary_tool == "build_context"
    assert "workspace_status" in status.mcp.stable_tools
    assert status.document_count == 0
    assert status.counts_by_source == {}
    assert any(check.name == "documents" for check in status.checks)
