from dce.interfaces.mcp.server import normalize_tag_slug


def test_normalize_tag_slug() -> None:
    assert normalize_tag_slug("oracle") == "oracle"
    assert normalize_tag_slug("tag:oracle") == "oracle"
    assert normalize_tag_slug("  TAG:db  ") == "db"
    assert normalize_tag_slug("") == ""
