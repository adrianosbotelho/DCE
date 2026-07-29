from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_contributing_doc() -> None:
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "pytest" in text
    assert "cut_release.sh" in text
    assert "schema_version" in text
