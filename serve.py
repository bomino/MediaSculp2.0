import os

from waitress import serve

from app import app

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    # Single process, multiple threads: the in-memory download-job registry and
    # the concurrency semaphore must be shared, so do NOT run multiple workers.
    print(f" * MediaSculp (waitress) on http://{host}:{port}")
    serve(app, host=host, port=port, threads=8)
