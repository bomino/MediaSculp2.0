"""Run MediaSculp as a desktop app: waitress in a background thread wrapped in a
native pywebview window. For the browser version use `python app.py` or
`python serve.py`.

Set MEDIASCULP_SERVER_ONLY=1 to serve without opening a window (used for
headless testing of a packaged build).
"""

import os
import sys


def _redirect_streams():
    """A windowed (no-console) frozen build has no stdout/stderr; sending
    print()/logging there would crash it. Point them at a log file when
    packaged, or os.devnull otherwise."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    target = open(os.devnull, "w")
    if getattr(sys, "frozen", False):
        try:
            log_dir = os.path.join(
                os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "MediaSculp"
            )
            os.makedirs(log_dir, exist_ok=True)
            target = open(os.path.join(log_dir, "mediasculp.log"), "a", buffering=1)
        except OSError:
            pass
    if sys.stdout is None:
        sys.stdout = target
    if sys.stderr is None:
        sys.stderr = target


_redirect_streams()

import socket
import threading
import time

from waitress import serve

from app import app


def _run_server(host, port):
    serve(app, host=host, port=port, threads=8)


def _free_port(host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return probe.getsockname()[1]


def _wait_until_ready(host, port, timeout=20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port_env = os.environ.get("PORT")
    port = int(port_env) if port_env else _free_port(host)

    if os.environ.get("MEDIASCULP_SERVER_ONLY"):
        print(f" * MediaSculp serving on http://{host}:{port}")
        _run_server(host, port)
        return

    try:
        import webview
    except ImportError:
        raise SystemExit(
            "pywebview is not installed. Install the desktop extra:\n"
            "    pip install -r requirements-desktop.txt\n"
            "Or run the browser version instead:\n"
            "    python serve.py"
        )

    thread = threading.Thread(target=_run_server, args=(host, port), daemon=True)
    thread.start()

    if not _wait_until_ready(host, port):
        raise SystemExit(f"Server did not start on http://{host}:{port}")

    webview.create_window("MediaSculp", f"http://{host}:{port}", width=1200, height=820)
    webview.start()


if __name__ == "__main__":
    main()
