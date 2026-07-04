import os
import secrets
import shutil
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# A frozen (packaged) app can't write next to its read-only bundle, so its
# downloads, clips and history default to a MediaSculp folder in the user's
# home directory instead. Environment overrides still win.
if getattr(sys, "frozen", False):
    DATA_ROOT = os.path.join(os.path.expanduser("~"), "MediaSculp")
else:
    DATA_ROOT = BASE_DIR


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_js_runtime():
    """Pick a JavaScript runtime for yt-dlp's challenge / PO-token solver.

    Newer yt-dlp needs Node >=22 or Deno to descramble YouTube's nsig and mint
    PO tokens; without one, extraction silently degrades to storyboard-only.
    yt-dlp defaults to deno, so a machine with only Node still fails unless the
    runtime is named explicitly. Honors YTDLP_JS_RUNTIME (a name like
    'node'/'deno' or a path to the binary), else prefers deno then node on PATH.
    Returns the runtime name, or None.
    """
    override = os.environ.get("YTDLP_JS_RUNTIME")
    if override:
        looks_like_path = os.sep in override or bool(os.altsep and os.altsep in override) or os.path.exists(override)
        if looks_like_path:
            directory = os.path.dirname(override)
            if directory:
                os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
            return os.path.splitext(os.path.basename(override))[0].lower() or None
        return override.lower()
    for name in ("deno", "node"):
        if shutil.which(name):
            return name
    return None


_COOKIE_FILENAMES = (
    "cookies.txt",
    "www.youtube.com_cookies.txt",
    "youtube.com_cookies.txt",
    "youtube_cookies.txt",
)


def _resolve_cookies():
    """Locate an exported cookies.txt for YouTube auth.

    Honors COOKIES_FILE, else auto-detects a drop-in cookies file in the data
    folder or next to the app — so any user, on any machine, can just drop a
    'cookies.txt' beside the app with no config editing. Returns a path or None.
    """
    override = os.environ.get("COOKIES_FILE")
    if override:
        return override
    for directory in dict.fromkeys((DATA_ROOT, BASE_DIR)):
        for name in _COOKIE_FILENAMES:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                return candidate
    return None


def _resolve_ffmpeg():
    """Locate ffmpeg for yt-dlp: explicit override, then PATH, then the
    imageio-ffmpeg bundled binary (already a dependency), else None."""
    override = os.environ.get("FFMPEG_LOCATION")
    if override:
        return override
    if shutil.which("ffmpeg"):
        return None  # on PATH; let yt-dlp resolve it
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("FLASK_DEBUG", False)

    DOWNLOAD_FOLDER = os.environ.get("DOWNLOAD_FOLDER") or os.path.join(DATA_ROOT, "downloads")
    TRIMMED_FOLDER = os.environ.get("TRIMMED_FOLDER") or os.path.join(DATA_ROOT, "trimmed_videos")

    # SQLite file backing the download history.
    DATABASE = os.environ.get("DATABASE") or os.path.join(DATA_ROOT, "mediasculp.db")

    # Path to the ffmpeg binary. Falls back to PATH, then the imageio-ffmpeg
    # bundled binary, so downloads work without a separate ffmpeg install.
    FFMPEG_LOCATION = _resolve_ffmpeg()

    # JS runtime name for yt-dlp's challenge / PO-token solver. Without one,
    # many YouTube videos return only storyboards (no audio/video).
    JS_RUNTIME = _resolve_js_runtime()

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_BYTES", 500 * 1024 * 1024))

    # How many downloads may run at once; the rest are queued.
    MAX_CONCURRENT_DOWNLOADS = int(os.environ.get("MAX_CONCURRENT_DOWNLOADS", 3))

    # Refuse to start a download when free space on the download folder is below
    # this (bytes). Default 200 MB; set 0 to disable the check.
    MIN_FREE_BYTES = int(os.environ.get("MIN_FREE_BYTES", 200 * 1024 * 1024))

    # When true, attempt `pip install -U yt-dlp` at startup (needs a restart to load).
    AUTO_UPDATE_YTDLP = _env_bool("AUTO_UPDATE_YTDLP", False)

    # Track yt-dlp's nightly channel instead of stable. Nightly ships YouTube
    # fixes days ahead of tagged releases — often the difference between a video
    # downloading and returning storyboards. Defaults on for the packaged app
    # (which can't be pip-upgraded ad hoc); off for a dev checkout.
    YTDLP_NIGHTLY = _env_bool("YTDLP_NIGHTLY", getattr(sys, "frozen", False))

    # Optional single-password gate. When set, every page requires logging in
    # first — useful before exposing the app beyond localhost. Empty = no auth.
    AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD") or None

    # Optional YouTube auth to satisfy "confirm you're not a bot" checks.
    # COOKIES_FROM_BROWSER reads cookies from a logged-in browser
    # (firefox/chrome/edge/brave/opera/vivaldi/chromium); COOKIES_FILE (or a
    # drop-in cookies.txt beside the app / in the data folder) points at an
    # exported cookies file. Either, both, or neither.
    COOKIES_FROM_BROWSER = os.environ.get("COOKIES_FROM_BROWSER") or None
    COOKIES_FILE = _resolve_cookies()

    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}
    ALLOWED_AUDIO_FORMATS = {"mp3", "wav", "ogg"}


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
