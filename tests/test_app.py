import os

from app import create_app
from config import Config, TestConfig
from routes.main import _audio_quality, _video_format
from utils import list_files, resolve_within, unique_name


def test_pages_render(client):
    for path in ("/", "/downloads", "/trimmed_videos"):
        assert client.get(path).status_code == 200


def test_home_has_csrf_meta(client):
    assert b'name="csrf-token"' in client.get("/").data


def test_upload_get_redirects_home(client):
    response = client.get("/upload")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_delete_traversal_reaches_view_and_is_refused(client, app):
    # Backslash-encoded traversal: the <path> converter passes it to the view,
    # where resolve_within (safe_join) rejects it with 400.
    response = client.post("/delete_file/..%5C..%5C..%5Csecret.txt")
    assert response.status_code in (400, 404)
    body = response.get_json()
    assert body is None or body.get("success") is False


def test_delete_real_file_succeeds(client, app):
    folder = app.config["DOWNLOAD_FOLDER"]
    target = os.path.join(folder, "clip.mp4")
    open(target, "w").close()

    response = client.post("/delete_file/clip.mp4")
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert not os.path.exists(target)


def test_delete_missing_file_returns_404(client):
    response = client.post("/delete_file/nope.mp4")
    assert response.status_code == 404


def test_bulk_delete_removes_selected_files(client, app):
    folder = app.config["DOWNLOAD_FOLDER"]
    for name in ("a.mp4", "b.mp3", "c.txt"):
        open(os.path.join(folder, name), "w").close()

    response = client.post("/delete_files", json={"filenames": ["a.mp4", "b.mp3"]})
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["deleted"] == 2
    assert body["failed"] == 0
    assert not os.path.exists(os.path.join(folder, "a.mp4"))
    assert not os.path.exists(os.path.join(folder, "b.mp3"))
    assert os.path.exists(os.path.join(folder, "c.txt"))


def test_bulk_delete_rejects_traversal_names(client, app):
    folder = app.config["DOWNLOAD_FOLDER"]
    open(os.path.join(folder, "real.mp4"), "w").close()

    response = client.post(
        "/delete_files", json={"filenames": ["real.mp4", "..\\..\\secret.txt"]}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["deleted"] == 1
    assert body["failed"] == 1
    assert body["success"] is False
    assert not os.path.exists(os.path.join(folder, "real.mp4"))


def test_bulk_delete_empty_returns_400(client):
    assert client.post("/delete_files", json={"filenames": []}).status_code == 400
    assert client.post("/delete_files", json={}).status_code == 400


def test_bulk_delete_trimmed_videos(client, app):
    folder = app.config["TRIMMED_FOLDER"]
    open(os.path.join(folder, "clip_trimmed.mp4"), "w").close()

    response = client.post(
        "/delete_trimmed_videos", json={"filenames": ["clip_trimmed.mp4"]}
    )
    assert response.status_code == 200
    assert response.get_json()["deleted"] == 1
    assert not os.path.exists(os.path.join(folder, "clip_trimmed.mp4"))


def test_bulk_delete_csrf_enforced(tmp_path):
    class Cfg(Config):
        WTF_CSRF_ENABLED = True
        SECRET_KEY = "unit-test"
        DOWNLOAD_FOLDER = str(tmp_path / "d")
        TRIMMED_FOLDER = str(tmp_path / "t")
        DATABASE = str(tmp_path / "db.sqlite")

    client = create_app(Cfg).test_client()
    response = client.post("/delete_files", json={"filenames": ["x.mp4"]})
    assert response.status_code in (400, 403)


def test_download_traversal_returns_404(client):
    assert client.get("/download_file/..%5C..%5Csecret.txt").status_code == 404


def test_csrf_enforced_when_enabled(tmp_path):
    class Cfg(Config):
        WTF_CSRF_ENABLED = True
        SECRET_KEY = "unit-test"
        DOWNLOAD_FOLDER = str(tmp_path / "d")
        TRIMMED_FOLDER = str(tmp_path / "t")
        DATABASE = str(tmp_path / "db.sqlite")

    client = create_app(Cfg).test_client()
    response = client.post("/delete_file/whatever.mp4")
    assert response.status_code in (400, 403)


def test_resolve_within_blocks_traversal():
    base = os.path.abspath("base")
    assert resolve_within(base, "..\\x") is None
    assert resolve_within(base, "../x") is None
    assert resolve_within(base, "C:\\Windows\\win.ini") is None
    assert resolve_within(base, "") is None
    assert resolve_within(base, "clip.mp4") is not None


def test_unique_name(tmp_path):
    directory = str(tmp_path)
    assert unique_name(directory, "a.mp4") == "a.mp4"
    open(os.path.join(directory, "a.mp4"), "w").close()
    assert unique_name(directory, "a.mp4") == "a_1.mp4"


def test_list_files_filters_hidden_dirs_and_extensions(tmp_path):
    directory = str(tmp_path)
    for name in ("v.mp4", "a.mp3", ".hidden", "note.txt"):
        open(os.path.join(directory, name), "w").close()
    os.mkdir(os.path.join(directory, "sub"))

    videos = list_files(directory, {"mp4", "mov", "avi", "mkv"})
    assert videos == ["v.mp4"]

    everything = list_files(directory)
    assert ".hidden" not in everything
    assert "sub" not in everything
    assert "note.txt" in everything


def test_video_format_binds_filters_correctly():
    assert _video_format("best") == (
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    )
    assert "height<=720" in _video_format("720p")
    assert "height" not in _video_format(None)


def test_audio_quality_mapping():
    assert _audio_quality("320") == "320"
    assert _audio_quality("best") == "0"
    assert _audio_quality("high") == "192"
    assert _audio_quality(None) == "192"


def test_parse_limit():
    from routes.main import _parse_limit

    assert _parse_limit("3") == 3
    assert _parse_limit("") is None
    assert _parse_limit(None) is None
    assert _parse_limit("0") is None
    assert _parse_limit("-2") is None
    assert _parse_limit("abc") is None


def test_build_ydl_opts_limit_and_playlist():
    from routes.main import _build_ydl_opts

    limited = _build_ydl_opts("/d", None, "mp3", "192", playlist_wanted=False, limit=3)
    assert limited["playlist_items"] == "1:3"
    assert limited["noplaylist"] is False

    plain = _build_ydl_opts("/d", None, "mp3", "192", playlist_wanted=False, limit=None)
    assert plain["noplaylist"] is True
    assert "playlist_items" not in plain

    whole = _build_ydl_opts("/d", None, "mp4", "720p", playlist_wanted=True, limit=None)
    assert whole["noplaylist"] is False
    assert whole["merge_output_format"] == "mp4"


def test_cancel_download(client, monkeypatch):
    import routes.main as main

    monkeypatch.setattr(main, "_run_download", lambda *a, **k: None)
    response = client.post(
        "/", data={"action": "Download Playlist", "url": "https://example.com/v"}
    )
    job_id = response.headers["Location"].split("job=")[1].split("&")[0]

    cancel = client.post("/cancel_download/" + job_id)
    assert cancel.status_code == 200
    assert cancel.get_json()["success"] is True

    status = client.get("/download_status/" + job_id).get_json()
    assert status["cancel"] is True
    assert client.post("/cancel_download/does-not-exist").status_code == 404


def test_list_files_skips_partial_downloads(tmp_path):
    directory = str(tmp_path)
    for name in ("done.mp3", "half.webm.part", "frag.ytdl"):
        open(os.path.join(directory, name), "w").close()
    files = list_files(directory)
    assert "done.mp3" in files
    assert "half.webm.part" not in files
    assert "frag.ytdl" not in files


def test_download_without_url_flashes_and_redirects(client):
    response = client.post(
        "/", data={"action": "Download Playlist", "url": ""}, follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Please enter a video URL." in response.data


def test_download_starts_background_job_and_redirects(client, monkeypatch):
    import routes.main as main

    monkeypatch.setattr(main, "_run_download", lambda *a, **k: None)
    response = client.post(
        "/", data={"action": "Download Playlist", "url": "https://example.com/v"}
    )
    assert response.status_code == 302
    assert "job=" in response.headers["Location"]


def test_download_status_endpoint(client, monkeypatch):
    import routes.main as main

    monkeypatch.setattr(main, "_run_download", lambda *a, **k: None)
    response = client.post(
        "/", data={"action": "Download Playlist", "url": "https://example.com/v"}
    )
    job_id = response.headers["Location"].split("job=")[1].split("&")[0]
    status = client.get("/download_status/" + job_id)
    assert status.status_code == 200
    assert status.get_json()["id"] == job_id
    assert client.get("/download_status/does-not-exist").status_code == 404


def test_downloads_status_lists_jobs(client, monkeypatch):
    import routes.main as main

    monkeypatch.setattr(main, "_run_download", lambda *a, **k: None)
    post = client.post(
        "/", data={"action": "Download Playlist", "url": "https://example.com/v"}
    )
    job_id = post.headers["Location"].split("job=")[1].split("&")[0]

    data = client.get("/downloads_status").get_json()
    assert "jobs" in data
    ids = [j["id"] for j in data["jobs"]]
    assert job_id in ids
    job = [j for j in data["jobs"] if j["id"] == job_id][0]
    assert "seq" in job
    assert job["status"] in ("queued", "running")


def test_disk_guard_blocks_download_when_space_low(tmp_path):
    class Cfg(TestConfig):
        DOWNLOAD_FOLDER = str(tmp_path / "d")
        TRIMMED_FOLDER = str(tmp_path / "t")
        DATABASE = str(tmp_path / "db.sqlite")
        MIN_FREE_BYTES = 10 ** 18  # larger than any real disk

    client = create_app(Cfg).test_client()
    response = client.post(
        "/",
        data={"action": "Download Playlist", "url": "https://example.com/v"},
        follow_redirects=True,
    )
    assert b"Not enough free disk space" in response.data


def test_db_records_and_mark_interrupted(tmp_path):
    import db

    path = str(tmp_path / "h.db")
    db.init_db(path)
    db.insert_download(path, "a", "u1", "mp3", "t1")
    db.insert_download(path, "b", "u2", "mp4", "t2")
    db.finish_download(path, "a", "done", "Title A", None, "a.mp3", 10, None, "t3")

    assert len(db.list_downloads(path)) == 2
    assert db.get_download(path, "a")["status"] == "done"

    db.mark_interrupted(path)
    assert db.get_download(path, "b")["status"] == "interrupted"
    assert db.get_download(path, "a")["status"] == "done"  # terminal rows untouched

    assert len(db.list_downloads(path, "Title A")) == 1
    assert len(db.list_downloads(path, "u2")) == 1


def test_history_page_lists_recorded_downloads(client, app):
    import db

    path = app.config["DATABASE"]
    db.insert_download(path, "job1", "https://example.com/v", "mp3", "2026-07-04T10:00")
    db.finish_download(
        path, "job1", "done", "My Song", None, "My Song.mp3", 12345, None, "2026-07-04T10:01"
    )

    html = client.get("/history").data
    assert b"My Song" in html
    assert b"DONE" in html


def test_redownload_starts_job(client, app, monkeypatch):
    import db
    import routes.main as main

    monkeypatch.setattr(main, "_run_download", lambda *a, **k: None)
    path = app.config["DATABASE"]
    db.insert_download(path, "jobX", "https://example.com/v", "mp3", "2026-07-04T10:00")
    db.finish_download(path, "jobX", "done", "T", None, None, None, None, "2026-07-04T10:01")

    response = client.post("/redownload/jobX")
    assert response.status_code == 302
    assert "job=" in response.headers["Location"]
    assert client.post("/redownload/does-not-exist").status_code == 302


def test_build_ydl_opts_extras():
    from routes.main import _build_ydl_opts

    opts = _build_ydl_opts("/d", None, "mp3", "192", False, None, {"subtitles", "thumbnail", "metadata"})
    assert opts["writesubtitles"] is True
    assert opts["writethumbnail"] is True
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegExtractAudio" in keys
    assert "EmbedThumbnail" in keys
    assert "FFmpegMetadata" in keys

    plain = _build_ydl_opts("/d", None, "mp3", "192", False, None, set())
    assert "writesubtitles" not in plain
    assert [pp["key"] for pp in plain["postprocessors"]] == ["FFmpegExtractAudio"]


def test_build_ydl_opts_sponsorblock_and_chapters():
    from routes.main import _build_ydl_opts

    opts = _build_ydl_opts("/d", None, "mp4", "720p", False, None, {"sponsorblock", "chapters"})
    pps = {pp["key"]: pp for pp in opts["postprocessors"]}
    assert "SponsorBlock" in pps
    assert "ModifyChapters" in pps
    assert pps["ModifyChapters"]["remove_sponsor_segments"] == ["sponsor"]
    assert pps["FFmpegMetadata"]["add_chapters"] is True
    assert pps["FFmpegMetadata"]["add_metadata"] is False


def test_downloads_stream_first_frame(app):
    import json

    from routes.main import downloads_stream

    with app.test_request_context("/downloads_stream"):
        response = downloads_stream()
        assert response.mimetype == "text/event-stream"
        first = next(iter(response.response))
        assert first.startswith("data:")
        payload = json.loads(first[len("data:"):].strip())
        assert "jobs" in payload


def test_list_files_detailed(tmp_path):
    from utils import list_files_detailed

    (tmp_path / "b.mp4").write_bytes(b"xxxxx")
    (tmp_path / "a.mp3").write_bytes(b"xx")
    (tmp_path / ".hidden").write_bytes(b"z")
    (tmp_path / "clip.part").write_bytes(b"z")

    rows = list_files_detailed(str(tmp_path))
    names = [r["name"] for r in rows]
    assert names == ["a.mp3", "b.mp4"]
    sizes = {r["name"]: r["size"] for r in rows}
    assert sizes["a.mp3"] == 2
    assert sizes["b.mp4"] == 5
    assert all(isinstance(r["mtime"], float) for r in rows)


def test_parse_extras_includes_new_options():
    from werkzeug.datastructures import MultiDict

    from routes.main import _parse_extras

    form = MultiDict([("opt_sponsorblock", "on"), ("opt_chapters", "on")])
    assert _parse_extras(form) == {"sponsorblock", "chapters"}


def test_parse_extras():
    from werkzeug.datastructures import MultiDict

    from routes.main import _parse_extras

    form = MultiDict([("opt_subtitles", "on"), ("opt_metadata", "on")])
    assert _parse_extras(form) == {"subtitles", "metadata"}
    assert _parse_extras(MultiDict()) == set()


def test_multi_url_creates_multiple_jobs(client, monkeypatch):
    import routes.main as main

    monkeypatch.setattr(main, "_run_download", lambda *a, **k: None)
    before = len(client.get("/downloads_status").get_json()["jobs"])
    client.post(
        "/",
        data={
            "action": "Download Playlist",
            "url": "https://a.example/1\nhttps://a.example/2\nhttps://a.example/3",
        },
    )
    after = client.get("/downloads_status").get_json()["jobs"]
    assert len(after) >= before + 3


def test_trim_missing_fields_flashes(client):
    response = client.post(
        "/", data={"action": "Trim Video"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Please provide a video" in response.data


def test_trim_unknown_video_reports_not_found(client):
    response = client.post(
        "/",
        data={
            "action": "Trim Video",
            "video_file": "does-not-exist.mp4",
            "start_time": "0",
            "duration": "5",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Selected video was not found." in response.data


def test_upload_without_file_flashes(client):
    response = client.post("/upload", data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b"No file selected." in response.data


def test_downloads_list_uses_safe_delete_markup(client, app):
    folder = app.config["DOWNLOAD_FOLDER"]
    open(os.path.join(folder, "clip.mp4"), "w").close()
    html = client.get("/downloads").data
    assert b'class="btn btn-sm btn-danger js-delete"' in html
    assert b'data-filename="clip.mp4"' in html
    # the old injection-prone inline handler must be gone
    assert b"showDeleteConfirm('" not in html
    assert b"file-manager.js" in html


def test_uploaded_file_query_param_is_escaped_in_js(client):
    payload = "</script><img src=x onerror=alert(1)>"
    response = client.get("/", query_string={"uploaded_file": payload, "show_trim": "1"})
    assert response.status_code == 200
    # tojson escapes the HTML metacharacters, so the raw breakout markup never appears.
    assert b"<img src=x onerror" not in response.data
    assert b"</script><img" not in response.data
