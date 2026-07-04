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

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_BYTES", 500 * 1024 * 1024))

    # How many downloads may run at once; the rest are queued.
    MAX_CONCURRENT_DOWNLOADS = int(os.environ.get("MAX_CONCURRENT_DOWNLOADS", 3))

    # Refuse to start a download when free space on the download folder is below
    # this (bytes). Default 200 MB; set 0 to disable the check.
    MIN_FREE_BYTES = int(os.environ.get("MIN_FREE_BYTES", 200 * 1024 * 1024))

    # When true, attempt `pip install -U yt-dlp` at startup (needs a restart to load).
    AUTO_UPDATE_YTDLP = _env_bool("AUTO_UPDATE_YTDLP", False)

    # Optional single-password gate. When set, every page requires logging in
    # first — useful before exposing the app beyond localhost. Empty = no auth.
    AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD") or None

    # Optional YouTube auth to satisfy "confirm you're not a bot" checks.
    # COOKIES_FROM_BROWSER reads cookies from a logged-in browser
    # (firefox/chrome/edge/brave/opera/vivaldi/chromium); COOKIES_FILE points at
    # an exported cookies.txt. Either, both, or neither.
    COOKIES_FROM_BROWSER = os.environ.get("COOKIES_FROM_BROWSER") or None
    COOKIES_FILE = os.environ.get("COOKIES_FILE") or None

    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}
    ALLOWED_AUDIO_FORMATS = {"mp3", "wav", "ogg"}


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
