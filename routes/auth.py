import hmac

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

auth_bp = Blueprint("auth", __name__)


def _safe_next(target):
    """Only allow same-site relative redirects, never protocol-relative URLs."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("main.index")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    password = current_app.config.get("AUTH_PASSWORD")
    if not password or session.get("authed"):
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        supplied = request.form.get("password", "")
        if hmac.compare_digest(supplied, password):
            session["authed"] = True
            session.permanent = True
            return redirect(_safe_next(request.args.get("next")))
        error = "Incorrect password."
    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.pop("authed", None)
    return redirect(url_for("auth.login"))
