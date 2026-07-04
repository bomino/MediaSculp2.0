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
- **FFmpeg auto-resolution**: `config._resolve_ffmpeg()` uses `FFMPEG_LOCATION`, else `PATH`, else the bundled `imageio-ffmpeg` binary — so downloads work without a separate ffmpeg install.

### Background downloads (progress + cancel + limit)
- **Async jobs**: `routes/main.py` runs `yt-dlp` in a daemon thread with an in-memory registry (`_jobs`, guarded by `_jobs_lock`). `POST /` returns immediately and redirects to `/?job=<id>`; the page polls `GET /download_status/<id>`. Jobs are single-process and in-memory (lost on restart, but `download_archive` lets a re-run resume).
- **Real progress**: yt-dlp `progress_hooks` update percent + "Downloading N/total: title"; the frontend renders it (no more fake progress bar).
- **Cancel**: `POST /cancel_download/<id>` (CSRF) sets a per-job flag; the progress hook raises `yt_dlp.utils.DownloadCancelled` to abort. Status becomes `cancelled`.
- **Playlist limit**: an optional "first N items" field maps to yt-dlp `playlist_items='1:N'`.
- **Active downloads panel**: `static/downloads-panel.js` (loaded in `base.html`, so it shows on every page) polls `GET /downloads_status` and renders each running/queued job with progress + cancel. `_start_download` checks free space (`MIN_FREE_BYTES`) before starting; `app._ytdlp_startup` prints the yt-dlp version at startup (optional `AUTO_UPDATE_YTDLP` self-update).

### UI redesign (compact, light + dark)
- **Design system**: `static/styles.css` is fully token-driven (CSS custom properties). Light + dark themes via `data-theme` on `<html>`, set before paint by a no-flash script in `base.html`, defaulting to `prefers-color-scheme` with a persisted toggle button in the navbar.
- **Look**: single desaturated **emerald** accent; **Geist** (UI) + **JetBrains Mono** (numbers) from Google Fonts; segmented tabs; restrained borders/shadows; focus-visible rings; `prefers-reduced-motion` support.
- **Trimmed chrome**: removed the fake enterprise footer (newsletter/link-farm/social), marketing stat row, and lorem Terms/Privacy/Contact modals; slim honest footer. Copy is plain and sentence-case.
- **Themed components**: the custom delete modal and other previously inline-styled bits are now token-based classes so dark mode works. Keep Bootstrap grid/JS + jQuery + Font Awesome (no framework migration).

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
CI runs the suite on every push/PR via `.github/workflows/ci.yml`.

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
   - Application factory `create_app` in `app.py`; CSRF (`Flask-WTF`) and error handlers registered there
   - Configuration in `config.py` (`Config` / `TestConfig`), all env-driven
   - Shared helpers in `utils.py` (`resolve_within`, `unique_name`, `list_files`)
   - Flask Blueprints for modular routes:
     - `routes/main.py`: download (background jobs), trim, upload, `/download_status`, `/cancel_download`
     - `routes/downloads.py`: file listing, download, delete endpoints

2. **Media Processing Pipeline**
   - **Downloading**: `yt-dlp` runs in a background daemon thread; the request returns immediately and the page polls job status (see the "Background downloads" section above)
   - **Video Trimming**: `moviepy` with an FFmpeg backend (synchronous — a single quick local operation)
   - **File Storage**: Two directories, created at startup by `create_app`:
     - `downloads/`: Downloaded media files
     - `trimmed_videos/`: Trimmed clips

3. **External Dependencies**
   - **FFmpeg**: Resolved by `config._resolve_ffmpeg()` — `FFMPEG_LOCATION`, else `PATH`, else the bundled `imageio-ffmpeg` binary. A separate install is optional.
   - **yt-dlp**: Download functionality (keep current — stale pins break against YouTube)
   - **moviepy**: Video trimming (uses the bundled `imageio-ffmpeg` binary)

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
6. **Download jobs**: in-memory and single-process; a job is lost if the server restarts, but a re-run resumes via `download_archive`. The dev server runs with `threaded=True` so status polls are served while a download runs.
7. **Theming**: light/dark via `data-theme` on `<html>`; all colors are tokens in `styles.css`; the navbar toggle persists the choice in `localStorage` and the initial theme is set before paint.