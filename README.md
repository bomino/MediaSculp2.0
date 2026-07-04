# MediaSculp 2.0

![MediaSculp Logo](static/QidayaLogo-small.png)

MediaSculp 2.0 is a local Flask web app for downloading media and trimming clips. It downloads audio or video from the many sites [yt-dlp](https://github.com/yt-dlp/yt-dlp) supports (YouTube, TikTok, and more), and cuts clips with [MoviePy](https://zulko.github.io/moviepy/)/FFmpeg. It's meant to run on your own machine at `http://127.0.0.1:5000`.

It ships with a compact interface that has both light and dark themes.

## Features

- **Download audio or video** from any site yt-dlp supports, with a format picker (MP3, WAV, OGG, MP4) and quality/bitrate selection.
- **Extras & batch** — optionally embed a thumbnail/cover art, save metadata tags, fetch subtitles, embed chapter markers, and skip sponsor segments ([SponsorBlock](https://sponsor.ajay.app/)); paste several links (one per line) to download them all at once. Your last options are remembered.
- **Playlists** — download a whole playlist, or cap it to the first N items.
- **Background downloads** — downloads run in the background and appear in an **Active downloads** panel (on every page) with live per-job progress (streamed over Server-Sent Events, with polling as a fallback) and a **Cancel** button, so a long playlist never freezes the page. Multiple downloads run in parallel up to a configurable limit; the rest queue. For **playlists**, downloaded video IDs are recorded (yt-dlp `download_archive`) so re-runs resume rather than re-download; single videos aren't archive-gated, so you can grab the same video in another format (e.g. MP3 after MP4).
- **Trim clips** — pick a downloaded video, scrub the built-in preview and set the start/end from the playhead, then cut. A fast keyframe copy by default, or tick **Precise cut** to re-encode for a frame-accurate clip.
- **Upload** local video files to trim them.
- **Manage files** — preview, download, and delete files; instant search (Ctrl+K), sort by name/size/date, filter by type, and real file sizes with at-a-glance counts.
- **Download history** — every download is recorded to a small SQLite database, so a **History** page lets you search, re-download, review past downloads even across restarts, and **delete** individual entries or **clear all** (records only — your files aren't touched).
- **Light + dark theme** — follows your OS setting, with a toggle in the top bar.

## Requirements

- **Python 3.10 or newer**
- **FFmpeg** — used for audio extraction and merging. It's resolved automatically from your `PATH`, and falls back to the FFmpeg binary bundled with `imageio-ffmpeg` (a dependency), so a separate install is optional. Set `FFMPEG_LOCATION` to point at a specific binary if you prefer.
- **A JavaScript runtime — Node ≥22 or Deno** *(recommended)*. yt-dlp uses it to solve YouTube's challenges and mint PO tokens; without one, many videos return only storyboards (no audio/video). It's auto-detected on `PATH` (override with `YTDLP_JS_RUNTIME`).
- A modern web browser (Chrome, Firefox, Safari, Edge)

## Quick start

1. **Clone:**
   ```bash
   git clone https://github.com/bomino/MediaSculp2.0.git
   cd MediaSculp2.0
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt          # runtime
   pip install -r requirements-dev.txt      # runtime + pytest (for tests)
   ```

4. **Run it:**
   ```bash
   python app.py
   ```
   The `downloads/` and `trimmed_videos/` folders are created automatically. Open `http://127.0.0.1:5000`.

## Configuration

Copy `.env.example` to `.env` and adjust. Everything is optional with safe defaults.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | random per run | Signs session/flash cookies. Set a fixed value so sessions survive a restart. |
| `FLASK_DEBUG` | `0` | Enables the Werkzeug debugger. **Never enable when exposed** — it allows remote code execution. |
| `DOWNLOAD_FOLDER` | `./downloads` | Where downloads are stored. |
| `TRIMMED_FOLDER` | `./trimmed_videos` | Where trimmed clips are stored. |
| `DATABASE` | `./mediasculp.db` | SQLite file backing the download history. |
| `FFMPEG_LOCATION` | auto | Path to an ffmpeg binary; blank = PATH, then the bundled binary. |
| `MAX_UPLOAD_BYTES` | `524288000` (500 MB) | Maximum upload size. |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | How many downloads run at once; extras queue. |
| `MIN_FREE_BYTES` | `209715200` (200 MB) | Refuse to start a download below this free space (0 disables). |
| `AUTO_UPDATE_YTDLP` | `0` | If `1`, update yt-dlp at startup (restart to load). |
| `YTDLP_NIGHTLY` | packaged: `1`, dev: `0` | Track yt-dlp's nightly channel — ships YouTube fixes days ahead of stable. |
| `YTDLP_JS_RUNTIME` | auto | JS runtime for yt-dlp's PO-token solver (`node`/`deno` or a path); blank = auto-detect (bundled Deno, then PATH). |
| `AUTH_PASSWORD` | _(unset)_ | If set, gate the whole app behind a single-password login. Blank = no auth. |
| `COOKIES_FROM_BROWSER` | _(unset)_ | Read YouTube cookies from this browser (`firefox`/`chrome`/`edge`/…) to pass "not a bot" checks. |
| `COOKIES_FILE` | auto | Path to an exported `cookies.txt`. Unset = auto-detect a drop-in `cookies.txt` beside the app / in the data folder. |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Bind address and port. Read by `python app.py` directly (not `config.py`). |

`SECRET_KEY`, `FLASK_DEBUG`, the folder paths, `FFMPEG_LOCATION`, and `MAX_UPLOAD_BYTES` are read by `config.py` at startup; `HOST`/`PORT` are read by the `python app.py` / `serve.py` entrypoints.

## Run with Docker

```bash
docker compose up --build
```

Open `http://127.0.0.1:5000`. Downloads and trimmed clips are written to `./downloads` and `./trimmed_videos` on the host (mounted as volumes), and ffmpeg is bundled in the image. Set a fixed `SECRET_KEY` in `docker-compose.yml` so sessions survive a restart.

## Production server

`python app.py` runs the Flask **dev server** — fine locally, not for exposure. For a production-style run, use the bundled [waitress](https://github.com/Pylons/waitress) server:

```bash
python serve.py        # HOST/PORT via env; defaults to 127.0.0.1:5000
```

Run a **single instance only** — the download-job registry and concurrency limit are in-memory, so multiple workers or replicas would not share them.

## Run as a desktop app

To run it in a native window instead of a browser tab (waitress runs in the background and the UI opens in a desktop window):

```bash
pip install -r requirements-desktop.txt
python desktop.py
```

This adds [pywebview](https://pywebview.flowrl.com/), which uses the platform's built-in web view (WebView2 on Windows, WebKitGTK on Linux, WebKit on macOS). Set `HOST`/`PORT` to change the bind address (a free port is chosen automatically if `PORT` is unset).

### Build a double-click app (no Python needed)

To hand a non-technical person a single icon they can double-click — no terminal, no Python — build a standalone bundle with [PyInstaller](https://pyinstaller.org/):

```bash
pip install -r requirements-build.txt
python build_desktop.py
```

This produces `dist/MediaSculp/` containing `MediaSculp.exe` (Windows). ffmpeg, yt-dlp, and a JS runtime are bundled, so nothing else needs installing. Notes:

- **Per-OS build.** Build on the OS you want to ship for — a Windows `.exe` won't run on macOS/Linux. The GitHub Actions workflow `build-desktop.yml` builds the Windows bundle on a tag push (`v*`) or manual run and uploads it as an artifact.
- **Bundled JS runtime.** The CI build downloads **Deno** into `runtimes/` and bundles it, so the packaged app can solve YouTube's challenges without the user installing Node. For a local build, drop a `deno` (or `deno.exe`) into `runtimes/` before running `build_desktop.py` — otherwise it falls back to a `node`/`deno` on the machine's `PATH`.
- **User data** (downloads, clips, history, log) lives in a `MediaSculp` folder in the user's home directory, not next to the read-only bundle. A drop-in `cookies.txt` there is auto-detected.
- **yt-dlp stays current.** A frozen copy can't be `pip`-upgraded, so on launch the app quietly downloads the latest yt-dlp (nightly, by default for the packaged app) into a user-writable folder that shadows the bundled copy on the next start — this keeps it working as YouTube changes.

## Usage

### Download
1. Open the **Download** tab.
2. Paste one or more links (one per line to queue several) — use the **Paste** button or drop a link onto the box — and pick a format (MP3/WAV/OGG or MP4) and quality.
3. Optionally tick **Extras** — subtitles, embed thumbnail/cover art, save metadata tags, embed chapter markers, skip sponsor segments. Your choices are remembered next time.
4. For a playlist URL, optionally set a **Playlist limit** to grab only the first N items.
4. Click **Start Download**. A progress bar shows real progress (e.g. "Downloading 3/19"); use **Cancel** to stop. Finished files appear on the **Downloads** page.

> **Download fails on a YouTube video?** The app now translates the common causes into guidance in the progress panel:
> - *"Sign in to confirm you're not a bot"* → give it your YouTube cookies. Easiest: export a `cookies.txt` and **drop it beside the app / in the data folder** — it's auto-detected. Or set `COOKIES_FROM_BROWSER` (e.g. `firefox`). On Windows, Chrome/Edge lock their cookie DB while running, so Firefox tends to work best. Cookies expire — re-export from a private window (sign in, export, close the window) if it stops working.
> - *Only storyboards / "Requested format is not available"* → the streams are PO-token/SABR-gated. Make sure a **JS runtime** (Node ≥22 or Deno) is installed and set **`YTDLP_NIGHTLY=1`** — nightly yt-dlp plus a JS runtime is what unlocks these.

### Trim
1. Open the **Trim** tab and pick a downloaded video — it loads into a preview player.
2. Play to the point you want and click **Set start from playhead** / **Set end from playhead**, or type a start time and duration in seconds (decimals allowed, e.g. `5.5`).
3. Optionally tick **Precise cut** to re-encode for a frame-accurate clip (slower, always MP4); leave it off for a fast keyframe-aligned copy.
4. Click **Trim Video**; find the clip on the **Trimmed** page.

### Upload
Open the **Upload** tab to upload a local video (MP4/MOV/AVI/MKV, up to 500 MB), then switch to **Trim**.

### Manage
The **Downloads** and **Trimmed** pages let you preview, download, and delete files, with instant search (Ctrl+K), sorting (name/size/date), and a type filter.

## Project structure

```
MediaSculp2.0/
├── app.py                    # App factory (create_app), CSRF, error handlers, dev entry
├── serve.py                  # Production entrypoint (waitress)
├── desktop.py                # Desktop-app entrypoint (waitress + pywebview)
├── build_desktop.py          # Builds the standalone bundle (PyInstaller)
├── MediaSculp.spec           # PyInstaller spec (data files, hidden imports)
├── ytdlp_updater.py          # Keeps a frozen build's yt-dlp current
├── config.py                 # Env-driven configuration (Config / TestConfig)
├── utils.py                  # safe path resolution, unique naming, file listing
├── db.py                     # SQLite download history (stdlib sqlite3)
├── routes/
│   ├── main.py               # Download (background jobs), trim, upload, status/cancel
│   ├── downloads.py          # File listing, download, delete endpoints
│   └── auth.py               # Optional single-password login/logout
├── templates/
│   ├── base.html             # Layout, navbar + theme toggle, slim footer
│   ├── index.html            # Home: download / trim / upload tabs
│   ├── downloads.html        # Downloads manager
│   ├── trimmed_videos.html   # Trimmed videos manager
│   ├── history.html          # Download history
│   └── login.html            # Login page (when AUTH_PASSWORD is set)
├── static/
│   ├── styles.css            # Token-based light/dark design system
│   ├── file-manager.js       # Shared delete/search/stats logic (FileManager)
│   ├── downloads-panel.js    # Active-downloads panel (all pages)
│   └── QidayaLogo-small.png  # Logo
├── icons/                    # App icon PNGs (72–512 px)
├── tests/                    # pytest suite (Flask test client)
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Runtime + pytest
├── requirements-desktop.txt  # Runtime + pywebview (desktop app)
├── requirements-build.txt    # Desktop deps + PyInstaller (standalone build)
├── Dockerfile                # Container image (waitress + ffmpeg)
├── docker-compose.yml        # One-command Docker run
├── .env.example              # Configuration template
├── downloads/                # Downloaded files (git-ignored)
├── trimmed_videos/           # Trimmed clips (git-ignored)
├── CLAUDE.md                 # Guidance for AI assistants
└── README.md                 # This file
```

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Home (download / trim / upload) |
| POST | `/` | Start a download job or run a trim |
| GET | `/download_status/<job_id>` | JSON status/progress of a download job |
| GET | `/downloads_status` | JSON status of all active/recent jobs |
| GET | `/downloads_stream` | Server-Sent Events stream of job status |
| POST | `/cancel_download/<job_id>` | Cancel a running download |
| GET | `/history` | Download history (searchable) |
| POST | `/redownload/<id>` | Re-download a history entry |
| POST | `/history/delete/<id>` | Delete one history entry (record only) |
| POST | `/history/delete_all` | Clear all history (records only) |
| GET/POST | `/login` | Login page / submit (only when `AUTH_PASSWORD` is set) |
| GET | `/logout` | Clear the login session |
| GET/POST | `/upload` | GET redirects home; POST uploads a file |
| GET | `/downloads` | Downloads manager |
| GET | `/trimmed_videos` | Trimmed manager |
| GET | `/download_file/<filename>` | Download a file |
| GET | `/download_trimmed/<filename>` | Download a trimmed clip |
| POST | `/delete_file/<filename>` | Delete a downloaded file |
| POST | `/delete_trimmed_video/<filename>` | Delete a trimmed clip |

Every POST route is CSRF-protected (Flask-WTF); browser requests must include the token.

## Design

A compact "tool" interface with light and dark themes driven by CSS custom properties (`data-theme` on `<html>`, following `prefers-color-scheme` with a persisted toggle). Single emerald accent, [Geist](https://vercel.com/font) for UI and JetBrains Mono for numbers. Built on Bootstrap 5 (grid, tabs, modals) with Font Awesome icons and a small amount of vanilla JS.

## Tech stack

- **Backend:** Flask, Flask-WTF (CSRF), yt-dlp (downloading), MoviePy + FFmpeg (trimming)
- **Frontend:** Bootstrap 5, Font Awesome 6, jQuery, custom CSS + vanilla JS

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The suite uses Flask's test client and does not hit the network (download jobs are stubbed), covering routing, CSRF enforcement, path-traversal rejection, upload/trim validation, and the format/quality helpers. GitHub Actions (`.github/workflows/ci.yml`) runs it on every push and pull request.

## Security notes

This is a single-user app intended for `127.0.0.1`. Keep `FLASK_DEBUG` off and don't expose it to a network without protecting it — the file-management endpoints act on the local filesystem. If you do expose it (e.g. on a LAN), set `AUTH_PASSWORD` to gate the whole app behind a login, and set a fixed `SECRET_KEY` so the session persists. CSRF protection is enabled and user-supplied paths are confined with `werkzeug.utils.safe_join`.

## Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push and open a Pull Request

## License

Licensed under the MIT License — see [LICENSE](LICENSE).

## Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — media downloading
- [MoviePy](https://zulko.github.io/moviepy/) — video processing
- [Flask](https://flask.palletsprojects.com/) — web framework
- [Bootstrap](https://getbootstrap.com/) — UI framework
- [Font Awesome](https://fontawesome.com/) — icons
- [Qidaya](https://qidaya.com) — branding

## Support

- Issues: [GitHub Issues](https://github.com/bomino/MediaSculp2.0/issues)

---

**MediaSculp 2.0** — download and trim media, locally.
