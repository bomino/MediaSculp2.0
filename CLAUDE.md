# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MediaSculp 2.0 is a Flask-based web application for downloading and processing media from YouTube and TikTok. It provides functionality for downloading videos/audio in various formats and trimming video files.

## Recent Updates (July 2026)

### Security & correctness hardening
- **Path traversal fixed**: delete and trim now resolve user-supplied names with `werkzeug.utils.safe_join` (`utils.resolve_within`), rejecting `..`, backslashes, and absolute paths.
- **CSRF protection**: `Flask-WTF` `CSRFProtect` guards every POST; forms carry `csrf_token()` and the delete `fetch()` calls send `X-CSRFToken` (read from the `<meta name="csrf-token">` in `base.html`).
- **No unsafe HTML**: templates no longer use `|safe` on user-influenced values; user messages go through `flash()` (Post/Redirect/Get) and are auto-escaped.
- **Config abstraction**: `config.py` centralizes `SECRET_KEY`, `DEBUG`, folders, `FFMPEG_LOCATION`, and `MAX_CONTENT_LENGTH`, all env-driven (see `.env.example`). `app.py` is an application factory (`create_app`).
- **Media fixes**: MP4 format selector corrected (was capped at 720p), audio no longer force-downsampled to 16 kHz, OGG maps to the `vorbis` codec, quality/playlist controls are wired, and duplicate downloads use yt-dlp's `download_archive`.

### Fixed Delete Modal Freezing Issue (December 2024)
- **Problem**: Bootstrap modals were causing the entire app to freeze when deleting files
- **Solution**: Custom modal solution without Bootstrap JavaScript (now shared in `static/file-manager.js`)
- **Key Learning**: KISS (Keep It Simple, Stupid) - Complex Bootstrap modal management was replaced with simple HTML/CSS/JavaScript

## Development Commands

### Running the Application
```bash
python app.py  # Serves http://127.0.0.1:5000 (debug OFF unless FLASK_DEBUG=1)
```

### Installing Dependencies
```bash
pip install -r requirements.txt        # runtime
pip install -r requirements-dev.txt    # runtime + pytest
```

### Running Tests
```bash
pytest
```

### Configuration
Copy `.env.example` to `.env` and adjust. `config.py` reads these at startup;
`SECRET_KEY`, `FLASK_DEBUG`, `DOWNLOAD_FOLDER`, `TRIMMED_FOLDER`, `FFMPEG_LOCATION`,
and `MAX_UPLOAD_BYTES` are all optional with safe defaults.

### Virtual Environment
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

## Architecture Overview

### Core Components

1. **Flask Application Structure**
   - Uses Flask Blueprints for modular route organization
   - Main app entry point: `app.py`
   - Routes split into:
     - `routes/main.py`: Core functionality (downloading, trimming)
     - `routes/downloads.py`: File management endpoints

2. **Media Processing Pipeline**
   - **Downloading**: Uses `yt-dlp` library for YouTube/playlist downloads
   - **Video Trimming**: Uses `moviepy` with FFmpeg backend
   - **File Storage**: Two main directories:
     - `downloads/`: Stores downloaded media files
     - `trimmed_videos/`: Stores processed/trimmed videos

3. **External Dependencies**
   - **FFmpeg**: Required system dependency. Resolved from `PATH` by default; override with the `FFMPEG_LOCATION` env var. (moviepy trimming uses the bundled `imageio-ffmpeg` binary.)
   - **yt-dlp**: YouTube download functionality (keep current — stale pins break)
   - **moviepy**: Video editing operations

### Key Technical Details

- **Supported Video Formats**: MP4, MOV, AVI, MKV
- **Supported Audio Formats**: MP3, WAV, OGG
- **File Upload Security**: Uses `werkzeug.utils.secure_filename` for sanitization
- **Blueprint Registration**: Modular route handling via Flask Blueprints
- **Template Engine**: Jinja2 with base template inheritance
- **Frontend**: Bootstrap-based responsive UI

### Important File Paths

- FFmpeg is resolved from `PATH` (or `FFMPEG_LOCATION`); no hardcoded path
- Media files stored in project-relative directories (created automatically by `create_app`)
- No database: the app is stateless and stores only files on disk

## Custom Modal Implementation

The delete functionality uses a custom modal instead of Bootstrap's modal JavaScript to avoid freezing issues. The shared logic lives in `static/file-manager.js` (exposed as the `FileManager` global) and is used by both `downloads.html` and `trimmed_videos.html`:

```javascript
// Custom modal markup (no Bootstrap JS) lives in the templates:
<div id="customDeleteModal" style="display: none; ...">...</div>

// Delete buttons carry the filename in a data attribute (no inline HTML injection):
<button class="js-delete" data-filename="{{ file }}">...</button>

// Each page wires the shared handler with its endpoint:
FileManager.init({ deletePrefix: '/delete_file/', itemNoun: 'file' });
```

**Important**: Never use Bootstrap's `new bootstrap.Modal()` for delete confirmations as it can cause the app to freeze. Delete requests must send the `X-CSRFToken` header.

## Key Considerations

1. **FFmpeg**: Resolved from `PATH`, overridable via `FFMPEG_LOCATION` — cross-platform
2. **File Validation**: Extension-based validation on the sanitized filename; paths confined via `resolve_within`
3. **Error Handling**: Exceptions are logged server-side; users see generic flash messages (no internals leaked)
4. **Duplicate Prevention**: yt-dlp `download_archive` (`.download_archive.txt`) records downloaded video IDs
5. **CSRF/Secrets/Debug**: CSRF on all POSTs; `SECRET_KEY` and `DEBUG` come from the environment