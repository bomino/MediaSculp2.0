"""Keep yt-dlp current in a frozen (PyInstaller) build.

A frozen app can't be `pip install -U`'d, so a bundled yt-dlp would rot as
YouTube changes. Instead we let a user-writable "vendor" directory shadow the
bundled copy: `ensure_on_path()` puts it on `sys.path` before yt-dlp is
imported, and `update_ytdlp()` downloads the latest wheel into it. Updates take
effect on the next launch (yt-dlp is imported once at startup).
"""

import os
import sys


def vendor_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "MediaSculp", "vendor")


def ensure_on_path():
    """Prepend the vendor dir to sys.path when it holds a valid yt_dlp package.

    Must run before yt-dlp is first imported for the shadow to take effect.
    """
    vendor = vendor_dir()
    marker = os.path.join(vendor, "yt_dlp", "version.py")
    if os.path.isfile(marker) and vendor not in sys.path:
        sys.path.insert(0, vendor)


def _normalize(version):
    """yt-dlp reports dates as '2026.06.09' but PyPI normalizes to '2026.6.9';
    compare them numerically so an identical version isn't re-downloaded."""
    try:
        return tuple(int(part) for part in version.split("."))
    except (AttributeError, ValueError):
        return version


def update_ytdlp(current_version=None, timeout=120):
    """Fetch the latest yt-dlp wheel from PyPI into the vendor dir.

    Returns the new version string when a fresh copy is written, or None when
    already current or on any failure. Extraction is staged then swapped so a
    partial download never breaks the copy already in place.
    """
    import io
    import json
    import shutil
    import tempfile
    import urllib.request
    import zipfile

    try:
        with urllib.request.urlopen("https://pypi.org/pypi/yt-dlp/json", timeout=30) as resp:
            meta = json.load(resp)
        version = meta["info"]["version"]
        if current_version and _normalize(version) == _normalize(current_version):
            return None

        wheels = [
            u for u in meta["urls"]
            if u.get("packagetype") == "bdist_wheel" and u["filename"].endswith("py3-none-any.whl")
        ]
        if not wheels:
            return None

        with urllib.request.urlopen(wheels[0]["url"], timeout=timeout) as resp:
            blob = resp.read()

        vendor = vendor_dir()
        os.makedirs(vendor, exist_ok=True)
        staging = tempfile.mkdtemp(prefix="ytdlp-", dir=vendor)
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                archive.extractall(staging)
            staged_pkg = os.path.join(staging, "yt_dlp")
            if not os.path.isfile(os.path.join(staged_pkg, "version.py")):
                return None

            target_pkg = os.path.join(vendor, "yt_dlp")
            previous = target_pkg + ".old"
            if os.path.isdir(target_pkg):
                shutil.rmtree(previous, ignore_errors=True)
                os.replace(target_pkg, previous)
            os.replace(staged_pkg, target_pkg)
            shutil.rmtree(previous, ignore_errors=True)
            return version
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    except Exception:
        return None
