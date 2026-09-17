"""
Real desktop entry point for 外贸数字员工.

Development:
    python run_desktop.py

Packaged builds use the same desktop.app.main().
"""

from desktop.app import main


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
