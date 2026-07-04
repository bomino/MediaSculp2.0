import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import TestConfig


@pytest.fixture
def app(tmp_path):
    class Cfg(TestConfig):
        DOWNLOAD_FOLDER = str(tmp_path / "downloads")
        TRIMMED_FOLDER = str(tmp_path / "trimmed_videos")

    return create_app(Cfg)


@pytest.fixture
def client(app):
    return app.test_client()
