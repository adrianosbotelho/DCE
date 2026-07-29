from dce.interfaces.mcp.server import normalize_technology_slug


def test_normalize_technology_slug() -> None:
    assert normalize_technology_slug("oracle") == "oracle"
    assert normalize_technology_slug("technology:oracle") == "oracle"
    assert normalize_technology_slug("  TECHNOLOGY:java  ") == "java"
    assert normalize_technology_slug("") == ""
