"""Packaging readiness: build wheel/sdist and smoke-install."""

from __future__ import annotations

import subprocess
import sys
import tomllib
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _expected_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.slow
def test_build_twine_and_wheel_smoke(tmp_path: Path) -> None:
    """Ensure hatch produces installable artifacts (PB-090)."""
    expected = _expected_version()
    dist = tmp_path / "dist"
    dist.mkdir()

    build = _run([sys.executable, "-m", "build", "--outdir", str(dist)])
    assert build.returncode == 0, build.stderr + build.stdout

    wheels = list(dist.glob("*.whl"))
    sdists = list(dist.glob("*.tar.gz"))
    assert len(wheels) == 1, wheels
    assert len(sdists) == 1, sdists
    assert "dev_context_engine" in wheels[0].name or "dev-context-engine" in wheels[0].name
    assert expected in wheels[0].name

    check = _run([sys.executable, "-m", "twine", "check", *map(str, dist.iterdir())])
    assert check.returncode == 0, check.stderr + check.stdout
    assert "PASSED" in check.stdout

    smoke = tmp_path / "smoke"
    venv.create(smoke, with_pip=True)
    pip = smoke / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
    python = smoke / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    dce = smoke / ("Scripts" if sys.platform == "win32" else "bin") / "dce"

    install = _run([str(pip), "install", str(wheels[0])])
    assert install.returncode == 0, install.stderr + install.stdout

    version = _run([str(dce), "--version"])
    assert version.returncode == 0, version.stderr + version.stdout
    assert expected in version.stdout or expected in version.stderr

    import_check = _run([str(python), "-c", "import dce; print(dce.__version__)"])
    assert import_check.returncode == 0, import_check.stderr
    assert import_check.stdout.strip() == expected
