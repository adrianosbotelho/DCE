# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for portable Windows dce.exe (onefile).
# Build on Windows only (CI windows-latest or local PowerShell script).

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

SPECDIR = Path(SPECPATH).resolve()
ROOT = SPECDIR.parents[1]
SRC = ROOT / "src"

datas = [(str(SRC / "dce" / "interfaces" / "web" / "static"), "dce/interfaces/web/static")]
binaries = []
hiddenimports = [
    "dce",
    "dce.interfaces.cli.main",
    "dce.interfaces.mcp.server",
    "dce.interfaces.web.server",
    "dce.interfaces.web.service",
    "typer",
    "rich",
    "yaml",
    "pydantic",
    "mcp",
]

for pkg in ("mcp", "pydantic", "typer", "rich", "httpx", "anyio", "jsonschema"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        hiddenimports += collect_submodules(pkg)

a = Analysis(
    [str(SPECDIR / "run_dce.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="dce",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
