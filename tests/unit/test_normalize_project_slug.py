from dce.interfaces.mcp.server import normalize_project_slug


def test_normalize_project_slug() -> None:
    assert normalize_project_slug("payments") == "payments"
    assert normalize_project_slug("project:payments") == "payments"
    assert normalize_project_slug("  PROJECT:PAY  ") == "PAY"
    assert normalize_project_slug("") == ""
