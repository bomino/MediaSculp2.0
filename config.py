import os
import secrets
import shutil

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


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

    DOWNLOAD_FOLDER = os.environ.get("DOWNLOAD_FOLDER") or os.path.join(BASE_DIR, "downloads")
    TRIMMED_FOLDER = os.environ.get("TRIMMED_FOLDER") or os.path.join(BASE_DIR, "trimmed_videos")

    # Path to the ffmpeg binary. Falls back to PATH, then the imageio-ffmpeg
    # bundled binary, so downloads work without a separate ffmpeg install.
    FFMPEG_LOCATION = _resolve_ffmpeg()

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_BYTES", 500 * 1024 * 1024))

    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}
    ALLOWED_AUDIO_FORMATS = {"mp3", "wav", "ogg"}


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
