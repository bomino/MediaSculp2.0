import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect

import db
from config import Config

csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["DOWNLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["TRIMMED_FOLDER"], exist_ok=True)

    db.init_db(app.config["DATABASE"])
    db.mark_interrupted(app.config["DATABASE"])

    csrf.init_app(app)

    from routes.main import main_bp
    from routes.downloads import downloads_bp
    from routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(downloads_bp)
    app.register_blueprint(auth_bp)

    register_auth(app)
    register_error_handlers(app)
    register_template_filters(app)
    if not app.config.get("TESTING"):
        _ytdlp_startup(app)
    return app


def register_auth(app):
    auth_enabled = bool(app.config.get("AUTH_PASSWORD"))

    @app.context_processor
    def inject_auth():
        return {"auth_enabled": auth_enabled}

    if not auth_enabled:
        return

    open_endpoints = {"auth.login", "static"}

    @app.before_request
    def require_login():
        if session.get("authed") or request.endpoint in open_endpoints:
            return None
        return redirect(url_for("auth.login", next=request.full_path if request.query_string else request.path))


def register_template_filters(app):
    import datetime

    @app.template_filter("datetimeformat")
    def datetimeformat(timestamp):
        try:
            return datetime.datetime.fromtimestamp(timestamp).strftime("%b %d, %Y %H:%M")
        except (TypeError, ValueError, OSError):
            return ""


def _ytdlp_startup(app):
    try:
        import yt_dlp

        print(f" * yt-dlp {yt_dlp.version.__version__}")
    except Exception:
        return
    if app.config.get("AUTO_UPDATE_YTDLP"):
        import subprocess
        import sys

        try:
            print(" * AUTO_UPDATE_YTDLP set — running pip install -U yt-dlp")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "--quiet", "yt-dlp"],
                check=False,
                timeout=180,
            )
            print(" * yt-dlp update attempted; restart to load the new version.")
        except Exception:
            app.logger.exception("yt-dlp auto-update failed")


def register_error_handlers(app):
    @app.errorhandler(413)
    def too_large(error):
        limit_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        flash(f"Upload rejected: file exceeds the {limit_mb} MB limit.", "danger")
        return redirect(url_for("main.index")), 413

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith(("/delete_", "/download_")):
            return {"success": False, "error": "Not found"}, 404
        return render_template("base.html"), 404


app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config["DEBUG"],
        threaded=True,
    )
