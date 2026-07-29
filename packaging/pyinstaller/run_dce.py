"""PyInstaller entrypoint for the portable ``dce`` binary."""

from __future__ import annotations

from dce.interfaces.cli.main import app

if __name__ == "__main__":
    app()
