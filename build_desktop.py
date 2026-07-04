"""Build the standalone MediaSculp desktop app with PyInstaller.

    pip install -r requirements-build.txt
    python build_desktop.py

Produces dist/MediaSculp/MediaSculp.exe (Windows). Build on the OS you want to
ship for — a Windows .exe won't run on macOS/Linux.
"""

import subprocess
import sys


def main():
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "MediaSculp.spec"],
        check=True,
    )
    print("\nBuilt: dist/MediaSculp/  (run dist/MediaSculp/MediaSculp.exe)")


if __name__ == "__main__":
    main()
