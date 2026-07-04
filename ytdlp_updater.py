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
    """Compare versions numerically. yt-dlp reports dates as '2026.06.09' but
    PyPI normalizes to '2026.6.9', and nightlies add a '.dev0' suffix; take the
    leading numeric components so equivalent versions aren't re-downloaded."""
    parts = []
    for part in str(version).split("."):
        if part.isdigit():
            parts.append(int(part))
        else:
            break
    return tuple(parts) if parts else str(version)


def _latest_release(releases):
    """Return (version, files) for the most recently uploaded release, including
    pre-releases (nightlies), based on file upload timestamps."""
    best_version = None
    best_time = ""
    for version, files in releases.items():
        for entry in files:
            if entry.get("yanked"):
                continue
            uploaded = entry.get("upload_time_iso_8601") or entry.get("upload_time") or ""
            if uploaded > best_time:
                best_time = uploaded
                best_version = version
    return best_version, releases.get(best_version, [])


def update_ytdlp(current_version=None, timeout=120, nightly=False):
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

        releases = meta.get("releases", {})
        if nightly:
            version, files = _latest_release(releases)
        else:
            version = meta["info"]["version"]
            files = releases.get(version) or meta.get("urls", [])
        if not version:
            return None
        if current_version and _normalize(version) == _normalize(current_version):
            return None

        wheels = [
            entry for entry in files
            if entry.get("packagetype") == "bdist_wheel" and entry["filename"].endswith("py3-none-any.whl")
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
