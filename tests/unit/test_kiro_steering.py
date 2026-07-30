"""Unit tests for Kiro steering text (PB-108)."""

from __future__ import annotations

from dce.interfaces.kiro_steering import STEERING_MARKDOWN, steering_payload
from dce.interfaces.web import service


def test_steering_mentions_primary_tool() -> None:
    text = STEERING_MARKDOWN
    assert "build_context" in text
    assert "workspace_status" in text
    assert "NÃO usar" in text or "Não invoque" in text

    payload = steering_payload()
    assert payload["ok"] is True
    assert "build_context" in payload["steering_markdown"]
    assert service.steering_payload()["steering_markdown"] == payload["steering_markdown"]
