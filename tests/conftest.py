"""Shared test setup.

The tracker creates its YOLO model when it is imported. These tests should not
load real weights or run inference, so a fake YOLO class replaces the real one
before the application modules are imported.
"""

import sys
from pathlib import Path

import pytest
import ultralytics

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


class FakeYOLO:
    """Stands in for ultralytics.YOLO. Records construction and track() calls."""

    instances = 0
    track_calls: list[dict] = []

    def __init__(self, path, *args, **kwargs):
        FakeYOLO.instances += 1
        self.path = str(path)
        self.names = {0: "person"}

    def track(self, **kwargs):
        FakeYOLO.track_calls.append(kwargs)
        return iter([])


ultralytics.YOLO = FakeYOLO

import app as app_module  # noqa: E402  (must come after the patch above)
import tracker as tracker_module  # noqa: E402


@pytest.fixture
def fake_yolo():
    FakeYOLO.track_calls.clear()
    return FakeYOLO


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def tracker():
    return tracker_module
