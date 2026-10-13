"""Fix: each uploaded video starts with a fresh tracker.

With persist=True, Ultralytics keeps tracker state after a video ends, so the
next upload in the same process started with the previous video's IDs.
"""


def _process_twice(tracker, tmp_path):
    for name in ("first.mp4", "second.mp4"):
        source = tmp_path / name
        source.write_bytes(b"not really a video")
        try:
            tracker.service.process_video(source)
        except tracker.TrackingError:
            pass  # the fake model writes no output file


def test_track_is_called_without_persistence(fake_yolo, tracker, tmp_path):
    _process_twice(tracker, tmp_path)

    assert fake_yolo.track_calls, "track() was never called"
    for call in fake_yolo.track_calls:
        assert call["persist"] is False


def test_every_video_is_tracked_with_the_same_settings(fake_yolo, tracker, tmp_path):
    _process_twice(tracker, tmp_path)

    settings = [
        {k: v for k, v in call.items() if k not in {"source", "project", "name"}}
        for call in fake_yolo.track_calls
    ]
    assert len(settings) == 2
    assert settings[0] == settings[1]
