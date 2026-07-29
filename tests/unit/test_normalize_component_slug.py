from dce.interfaces.mcp.server import normalize_component_slug


def test_normalize_component_slug() -> None:
    assert normalize_component_slug("listener") == "listener"
    assert normalize_component_slug("component:listener") == "listener"
    assert normalize_component_slug("  COMPONENT:db  ") == "db"
    assert normalize_component_slug("") == ""
