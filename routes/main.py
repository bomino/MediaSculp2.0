import json
import os
import re
import shutil
import threading
import time
import uuid
from datetime import datetime

import yt_dlp
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from werkzeug.utils import secure_filename

import db
from utils import list_files, resolve_within, unique_name

main_bp = Blueprint("main", __name__)

AUDIO_CODEC = {"mp3": "mp3", "wav": "wav", "ogg": "vorbis"}

_jobs = {}
_jobs_lock = threading.Lock()
_MAX_JOBS = 50
_job_seq = 0
_semaphore = None
_semaphore_lock = threading.Lock()


def _get_semaphore(limit):
    global _semaphore
    with _semaphore_lock:
        if _semaphore is None:
            _semaphore = threading.BoundedSemaphore(max(1, limit))
    return _semaphore


def trim_video(input_file_path, output_file_path, start_time, duration):
    end_time = start_time + duration
    ffmpeg_extract_subclip(
        input_file_path, start_time, end_time, targetname=output_file_path
    )


def _allowed_upload(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_VIDEO_EXTENSIONS"]


def _video_format(quality):
    height = None
    if quality:
        match = re.match(r"(\d+)p?$", quality)
        if match:
            height = int(match.group(1))
    if height:
        return (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height<={height}][ext=mp4]/best[height<={height}]/best"
        )
    return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"


def _audio_quality(quality):
    if quality and quality.isdigit():
        return quality
    if quality == "best":
        return "0"
    return "192"


def _parse_limit(raw):
    if not raw:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


EXTRA_OPTIONS = ("subtitles", "thumbnail", "metadata", "sponsorblock", "chapters")


def _parse_extras(form):
    return {name for name in EXTRA_OPTIONS if form.get("opt_" + name)}


def _build_ydl_opts(download_folder, ffmpeg_location, format_choice, quality, playlist_wanted, limit=None, extras=None):
    extras = extras or set()
    opts = {
        "outtmpl": os.path.join(download_folder, "%(title)s.%(ext)s"),
        "noplaylist": not (playlist_wanted or limit),
        "download_archive": os.path.join(download_folder, ".download_archive.txt"),
        "socket_timeout": 30,
        "retries": 3,
        "ignoreerrors": "only_download",
    }
    if limit:
        opts["playlist_items"] = f"1:{limit}"
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location

    postprocessors = []
    if format_choice == "mp4":
        opts["format"] = _video_format(quality)
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "bestaudio/best"
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": AUDIO_CODEC.get(format_choice, "mp3"),
                "preferredquality": _audio_quality(quality),
            }
        )

    if "subtitles" in extras:
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        # Just English — a wildcard pulls dozens of auto-translated tracks and
        # trips YouTube's rate limiter, which can abort the whole download.
        opts["subtitleslangs"] = ["en"]
        if format_choice == "mp4":
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})
    if "thumbnail" in extras:
        opts["writethumbnail"] = True
        postprocessors.append({"key": "EmbedThumbnail"})
    if "sponsorblock" in extras:
        # Fetch sponsor segments (after_filter so it runs before extraction) and
        # strip them. A network hiccup or a video with no segments is a no-op.
        postprocessors.append(
            {"key": "SponsorBlock", "categories": ["sponsor"], "when": "after_filter"}
        )
        postprocessors.append(
            {"key": "ModifyChapters", "remove_sponsor_segments": ["sponsor"]}
        )
    if "metadata" in extras or "chapters" in extras:
        # One FFmpegMetadata pass carries both tags and embedded chapter markers.
        postprocessors.append(
            {
                "key": "FFmpegMetadata",
                "add_metadata": "metadata" in extras,
                "add_chapters": "chapters" in extras,
            }
        )

    opts["postprocessors"] = postprocessors
    return opts


def _update_job(job_id, **changes):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None:
            job.update(changes)


def _create_job(format_choice):
    global _job_seq
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        finished = [j for j, v in _jobs.items() if v["status"] in ("done", "error", "cancelled")]
        while len(_jobs) >= _MAX_JOBS and finished:
            _jobs.pop(finished.pop(0), None)
        _job_seq += 1
        _jobs[job_id] = {
            "id": job_id,
            "seq": _job_seq,
            "status": "queued",
            "percent": 0,
            "total": None,
            "current_title": "",
            "message": "Queued…",
            "format": format_choice,
            "cancel": False,
        }
    return job_id


def _make_progress_hook(job_id):
    def hook(data):
        with _jobs_lock:
            job = _jobs.get(job_id)
            cancelled = job.get("cancel") if job else True
        if cancelled:
            raise yt_dlp.utils.DownloadCancelled()

        info = data.get("info_dict") or {}
        total = info.get("playlist_count") or info.get("n_entries")
        index = info.get("playlist_index")
        with _jobs_lock:
            job = _jobs.get(job_id)
            if job is None:
                return
            if total:
                job["total"] = total
            if info.get("title"):
                job["current_title"] = info["title"]
            if data.get("status") == "downloading":
                downloaded = data.get("downloaded_bytes") or 0
                size = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                fraction = (downloaded / size) if size else 0
                if job["total"] and index:
                    job["percent"] = round(((index - 1) + fraction) / job["total"] * 100)
                    job["message"] = (
                        f"Downloading {index}/{job['total']}: {job['current_title']}"
                    )
                else:
                    job["percent"] = round(fraction * 100)
                    job["message"] = f"Downloading: {job['current_title']}"
            elif data.get("status") == "finished":
                job["message"] = f"Converting: {job['current_title']}"

    return hook


def _make_pp_hook(job_id):
    def hook(data):
        info = data.get("info_dict") or {}
        path = info.get("filepath")
        if path:
            _update_job(job_id, final_file=path)

    return hook


def _record(db_path, job_id, status, error):
    with _jobs_lock:
        job = _jobs.get(job_id)
        title = job.get("current_title") if job else None
        items = job.get("total") if job else None
        final_file = job.get("final_file") if job else None
    file_name = None
    size = None
    if final_file and os.path.isfile(final_file):
        file_name = os.path.basename(final_file)
        try:
            size = os.path.getsize(final_file)
        except OSError:
            size = None
    try:
        db.finish_download(
            db_path, job_id, status, title or None, items, file_name, size, error,
            datetime.now().isoformat(),
        )
    except Exception:
        pass  # history is best-effort; never fail a download over it


def _run_download(job_id, download_folder, ffmpeg_location, url, format_choice, quality, playlist_wanted, limit, extras, max_concurrent, db_path, logger):
    semaphore = _get_semaphore(max_concurrent)
    semaphore.acquire()
    try:
        with _jobs_lock:
            job = _jobs.get(job_id)
            cancelled = job.get("cancel") if job else True
        if cancelled:
            _update_job(job_id, status="cancelled", message="Download cancelled.")
            _record(db_path, job_id, "cancelled", None)
            return
        _update_job(job_id, status="running", message="Starting…")

        opts = _build_ydl_opts(download_folder, ffmpeg_location, format_choice, quality, playlist_wanted, limit, extras)
        opts["progress_hooks"] = [_make_progress_hook(job_id)]
        opts["postprocessor_hooks"] = [_make_pp_hook(job_id)]
        opts["quiet"] = True
        opts["no_warnings"] = True
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except yt_dlp.utils.DownloadCancelled:
            _update_job(job_id, status="cancelled", message="Download cancelled.")
            _record(db_path, job_id, "cancelled", None)
            return
        except Exception:
            logger.exception("Download failed for %s", url)
            _update_job(
                job_id,
                status="error",
                message="Download failed. Check that the URL is valid and try again.",
            )
            _record(db_path, job_id, "error", "Download failed.")
            return

        with _jobs_lock:
            job = _jobs.get(job_id)
            if job is not None:
                job["status"] = "done"
                job["percent"] = 100
                count = job.get("total")
                suffix = f" {count} item(s)." if count else ""
                job["message"] = f"Download completed in {format_choice.upper()} format.{suffix}"
        _record(db_path, job_id, "done", None)
    finally:
        semaphore.release()


def _launch_download(url, format_choice, quality, playlist_wanted, limit, extras):
    download_folder = current_app.config["DOWNLOAD_FOLDER"]
    ffmpeg_location = current_app.config.get("FFMPEG_LOCATION")
    max_concurrent = current_app.config["MAX_CONCURRENT_DOWNLOADS"]
    db_path = current_app.config["DATABASE"]
    logger = current_app.logger

    min_free = current_app.config.get("MIN_FREE_BYTES", 0)
    if min_free:
        try:
            free = shutil.disk_usage(download_folder).free
        except OSError:
            free = None
        if free is not None and free < min_free:
            flash("Not enough free disk space to start this download.", "danger")
            return None

    job_id = _create_job(format_choice)
    db.insert_download(db_path, job_id, url, format_choice, datetime.now().isoformat())
    thread = threading.Thread(
        target=_run_download,
        args=(
            job_id,
            download_folder,
            ffmpeg_location,
            url,
            format_choice,
            quality,
            playlist_wanted,
            limit,
            extras,
            max_concurrent,
            db_path,
            logger,
        ),
        daemon=True,
    )
    thread.start()
    return job_id


def _start_download():
    urls = (request.form.get("url") or "").split()
    if not urls:
        flash("Please enter a video URL.", "danger")
        return None
    format_choice = request.form.get("format", "mp3")
    quality = request.form.get("quality")
    playlist_wanted = bool(request.form.get("playlist"))
    limit = _parse_limit(request.form.get("limit"))
    extras = _parse_extras(request.form)
    first = None
    for url in urls:
        job_id = _launch_download(url, format_choice, quality, playlist_wanted, limit, extras)
        if job_id and first is None:
            first = job_id
    return first


def _handle_trim(download_folder, trimmed_folder):
    video_file = request.form.get("video_file")
    start_raw = request.form.get("start_time")
    duration_raw = request.form.get("duration")

    if not (video_file and start_raw and duration_raw):
        flash("Please provide a video, start time, and duration.", "danger")
        return
    try:
        start_time = float(start_raw)
        duration = float(duration_raw)
    except ValueError:
        flash("Start time and duration must be numbers.", "danger")
        return
    if start_time < 0 or duration <= 0:
        flash("Start time must be at least 0 and duration greater than 0.", "danger")
        return

    input_path = resolve_within(download_folder, video_file)
    if input_path is None or not os.path.isfile(input_path):
        flash("Selected video was not found.", "danger")
        return

    base, ext = os.path.splitext(os.path.basename(video_file))
    output_name = unique_name(trimmed_folder, f"{base}_trimmed{ext}")
    output_path = os.path.join(trimmed_folder, output_name)
    try:
        trim_video(input_path, output_path, start_time, duration)
    except Exception:
        current_app.logger.exception("Trim failed for %s", input_path)
        flash("Trimming failed. Please try again.", "danger")
        return
    flash(
        f'Video trimmed successfully. Find "{output_name}" on the Trimmed Videos page.',
        "success",
    )


@main_bp.route("/download_status/<job_id>")
def download_status(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return jsonify({"error": "unknown job"}), 404
        return jsonify(dict(job))


def _jobs_snapshot():
    with _jobs_lock:
        jobs = [dict(job) for job in _jobs.values()]
    jobs.sort(key=lambda j: j.get("seq", 0))
    return jobs


@main_bp.route("/downloads_status")
def downloads_status():
    return jsonify({"jobs": _jobs_snapshot()})


@main_bp.route("/downloads_stream")
def downloads_stream():
    """Server-Sent Events feed of job status, so the panel updates without polling.

    Emits a frame whenever the snapshot changes, a heartbeat comment otherwise,
    and closes itself after a stretch of inactivity so a worker thread is not
    held open forever; the client falls back to polling once the stream ends.
    """
    poll_interval = 1.5
    max_idle_ticks = 20

    def stream():
        last_payload = None
        idle_ticks = 0
        while idle_ticks < max_idle_ticks:
            jobs = _jobs_snapshot()
            payload = json.dumps({"jobs": jobs})
            if payload != last_payload:
                last_payload = payload
                yield f"data: {payload}\n\n"
            else:
                yield ": ping\n\n"
            active = any(job.get("status") in ("running", "queued") for job in jobs)
            idle_ticks = 0 if active else idle_ticks + 1
            time.sleep(poll_interval)
        yield "event: idle\ndata: {}\n\n"

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@main_bp.route("/cancel_download/<job_id>", methods=["POST"])
def cancel_download(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return jsonify({"success": False, "error": "unknown job"}), 404
        if job["status"] in ("running", "queued"):
            job["cancel"] = True
            job["message"] = "Cancelling…"
        return jsonify({"success": True}), 200


@main_bp.route("/history")
def history():
    query = request.args.get("q")
    rows = db.list_downloads(current_app.config["DATABASE"], query)
    download_folder = current_app.config["DOWNLOAD_FOLDER"]
    for row in rows:
        row["exists"] = bool(row.get("file")) and os.path.isfile(
            os.path.join(download_folder, row["file"])
        )
    return render_template("history.html", rows=rows, query=query or "")


@main_bp.route("/redownload/<download_id>", methods=["POST"])
def redownload(download_id):
    row = db.get_download(current_app.config["DATABASE"], download_id)
    if not row:
        flash("That download was not found in history.", "danger")
        return redirect(url_for("main.history"))
    job_id = _launch_download(row["url"], row.get("format") or "mp3", None, False, None, set())
    if job_id:
        flash("Re-download started.", "success")
        return redirect(url_for("main.index", job=job_id))
    return redirect(url_for("main.history"))


@main_bp.route("/upload", methods=["GET", "POST"])
def upload_video():
    if request.method == "GET":
        return redirect(url_for("main.index"))

    download_folder = current_app.config["DOWNLOAD_FOLDER"]
    file = request.files.get("video")
    if file is None or file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("main.index"))

    filename = secure_filename(file.filename)
    if not filename or not _allowed_upload(filename):
        flash("Unsupported file type. Allowed: MP4, MOV, AVI, MKV.", "danger")
        return redirect(url_for("main.index"))

    filename = unique_name(download_folder, filename)
    file.save(os.path.join(download_folder, filename))
    flash(
        f'Video "{filename}" uploaded successfully. Open the Trim tab to edit it.',
        "success",
    )
    return redirect(url_for("main.index", uploaded_file=filename, show_trim="1"))


@main_bp.route("/", methods=["GET", "POST"])
def index():
    download_folder = current_app.config["DOWNLOAD_FOLDER"]
    trimmed_folder = current_app.config["TRIMMED_FOLDER"]

    if request.method == "POST":
        action = request.form.get("action")
        if action == "Download Playlist":
            job_id = _start_download()
            if job_id:
                return redirect(url_for("main.index", job=job_id))
            return redirect(url_for("main.index"))
        if action == "Trim Video":
            _handle_trim(download_folder, trimmed_folder)
        return redirect(url_for("main.index"))

    videos = list_files(download_folder, current_app.config["ALLOWED_VIDEO_EXTENSIONS"])
    return render_template(
        "index.html",
        videos=videos,
        current_year=datetime.now().year,
        uploaded_file=request.args.get("uploaded_file"),
        show_trim=request.args.get("show_trim"),
        job=request.args.get("job"),
    )
