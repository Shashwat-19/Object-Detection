"""Fix: the upload and result pages show values measured from the video.

Before this fix, the summary cards, the hero panel, and the charts showed fixed
numbers (for example 128 tracked objects and 31 FPS) for every video.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import app as app_module
import tracker as tracker_module

MP4_HEADER = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


class _FakeIds:
    def __init__(self, values):
        self._values = list(values)

    def int(self):
        return self

    def tolist(self):
        return list(self._values)


class _FakeBoxes:
    def __init__(self, count, ids):
        self._count = count
        self.id = None if ids is None else _FakeIds(ids)

    def __len__(self):
        return self._count


def _fake_track(frames):
    """Return a track() replacement that yields one result per (count, ids) frame.

    It also writes the output video where tracker.process_video looks for it.
    """

    def track(self, **kwargs):
        out_dir = Path(kwargs["project"]) / kwargs["name"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / Path(kwargs["source"]).name).write_bytes(MP4_HEADER)
        return iter([SimpleNamespace(boxes=_FakeBoxes(count, ids)) for count, ids in frames])

    return track


FRAMES = [(2, [1, 2]), (3, [2, 3, 4]), (0, None)]  # 3 frames, 5 detections, IDs 1-4


@pytest.fixture
def processed(fake_yolo, monkeypatch, tmp_path):
    """Process a fake video and return (output name, stats dict). Cleans up after."""
    monkeypatch.setattr(fake_yolo, "track", _fake_track(FRAMES))
    source = tmp_path / "clip.mp4"
    source.write_bytes(MP4_HEADER)

    output = Path(tracker_module.service.process_video(source))
    stats = json.loads(output.with_suffix(".json").read_text())
    yield output.name, stats

    output.unlink(missing_ok=True)
    output.with_suffix(".json").unlink(missing_ok=True)


def test_stats_are_measured_from_the_tracking_results(processed):
    _, stats = processed

    assert stats["frames_processed"] == 3
    assert stats["total_detections"] == 5
    assert stats["unique_track_ids"] == 4
    assert stats["processing_seconds"] >= 0


def test_result_page_shows_the_measured_values(client, processed):
    name, _ = processed

    body = client.get("/result/", query_string={"file": name}).get_data(as_text=True)

    assert "<strong>4</strong>" in body  # unique track IDs
    assert "<strong>5</strong>" in body  # detections
    assert "<strong>3</strong>" in body  # frames processed


def test_result_page_has_no_fixed_placeholder_numbers(client, processed):
    name, _ = processed

    body = client.get("/result/", query_string={"file": name}).get_data(as_text=True)

    for placeholder in ("128", "214", "02:18", 'data-count-up="31"'):
        assert placeholder not in body, f"fixed value {placeholder!r} still in the result page"


def test_result_page_without_stats_shows_a_dash_not_a_number(client, tmp_path):
    name = "no_stats_here.mp4"
    (app_module.OUTPUT_DIR / name).write_bytes(MP4_HEADER)
    try:
        body = client.get("/result/", query_string={"file": name}).get_data(as_text=True)
    finally:
        (app_module.OUTPUT_DIR / name).unlink(missing_ok=True)

    assert "128" not in body
    assert "—" in body


def test_upload_page_has_no_fixed_percentages(client):
    body = client.get("/").get_data(as_text=True)

    for placeholder in ("92.4%", "96%", "31.8"):
        assert placeholder not in body
