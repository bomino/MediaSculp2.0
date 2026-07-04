"""Run MediaSculp as a desktop app: waitress in a background thread, wrapped in
a native pywebview window. Falls back with a clear message if pywebview is
missing. For the browser version use `python app.py` or `python serve.py`.
"""

import os
import socket
import threading
import time

from waitress import serve

from app import app


def _run_server(host, port):
    serve(app, host=host, port=port, threads=8)


def _wait_until_ready(host, port, timeout=15.0):
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
    port = int(os.environ.get("PORT", 5000))

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
