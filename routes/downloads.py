import os

from flask import Blueprint, current_app, jsonify, render_template, request, send_from_directory

from utils import list_files, resolve_within

downloads_bp = Blueprint("downloads", __name__)


def _download_folder():
    return current_app.config["DOWNLOAD_FOLDER"]


def _trimmed_folder():
    return current_app.config["TRIMMED_FOLDER"]


def _delete_within(folder, filename):
    target = resolve_within(folder, filename)
    if target is None:
        return jsonify({"success": False, "error": "Invalid filename"}), 400
    try:
        os.remove(target)
    except FileNotFoundError:
        return jsonify({"success": False, "error": "File not found"}), 404
    except OSError:
        current_app.logger.exception("Failed to delete %s", target)
        return jsonify({"success": False, "error": "Could not delete file"}), 500
    return jsonify({"success": True, "message": "Deleted"}), 200


def _delete_many(folder):
    data = request.get_json(silent=True) or {}
    names = data.get("filenames")
    if not isinstance(names, list) or not names:
        return jsonify({"success": False, "error": "No files specified"}), 400

    deleted = 0
    failed = 0
    for name in names:
        target = resolve_within(folder, name) if isinstance(name, str) else None
        if target is None:
            failed += 1
            continue
        try:
            os.remove(target)
            deleted += 1
        except FileNotFoundError:
            failed += 1
        except OSError:
            current_app.logger.exception("Failed to delete %s", target)
            failed += 1
    return jsonify({"success": failed == 0, "deleted": deleted, "failed": failed}), 200


@downloads_bp.route("/downloads", methods=["GET"])
def list_downloads():
    return render_template("downloads.html", files=list_files(_download_folder()))


@downloads_bp.route("/download_file/<path:filename>")
def download_file(filename):
    return send_from_directory(_download_folder(), filename, as_attachment=True)


@downloads_bp.route("/delete_file/<path:filename>", methods=["POST"])
def delete_file(filename):
    return _delete_within(_download_folder(), filename)


@downloads_bp.route("/delete_files", methods=["POST"])
def delete_files():
    return _delete_many(_download_folder())


@downloads_bp.route("/download_trimmed/<path:filename>")
def download_trimmed(filename):
    return send_from_directory(_trimmed_folder(), filename, as_attachment=True)


@downloads_bp.route("/trimmed_videos", methods=["GET"])
def trimmed_videos():
    return render_template("trimmed_videos.html", files=list_files(_trimmed_folder()))


@downloads_bp.route("/delete_trimmed_video/<path:filename>", methods=["POST"])
def delete_trimmed_video(filename):
    return _delete_within(_trimmed_folder(), filename)


@downloads_bp.route("/delete_trimmed_videos", methods=["POST"])
def delete_trimmed_videos_bulk():
    return _delete_many(_trimmed_folder())
