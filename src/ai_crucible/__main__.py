"""``python -m ai_crucible`` and the PyInstaller binary entry point (npm-launcher target)."""

from ai_crucible.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
