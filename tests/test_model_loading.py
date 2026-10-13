"""Fix: load the model once at startup, not on the first or every request."""

from pathlib import Path


def test_model_is_loaded_when_the_service_is_created(fake_yolo, tracker):
    # The module-level service is created on import. Its model must already exist.
    assert fake_yolo.instances == 1
    assert tracker.service._model is not None


def test_requests_do_not_reload_the_model(fake_yolo, tracker, tmp_path):
    loads_before = fake_yolo.instances
    source = tmp_path / "clip.mp4"

    for _ in range(3):
        source.write_bytes(b"not really a video")  # process_video deletes its input
        try:
            tracker.service.process_video(source)
        except tracker.TrackingError:
            pass  # the fake model produces no frames, so no output is written

    assert fake_yolo.instances == loads_before


def test_model_property_returns_the_loaded_instance(tracker):
    assert tracker.service.model is tracker.service._model


def test_missing_weights_do_not_stop_startup(tracker):
    # Ultralytics downloads the named weights on first load, so the service
    # must not raise when the file is absent.
    missing = Path(tracker.BASE_DIR) / "does-not-exist-yolo.pt"
    assert not missing.exists()
    service = tracker.TrackingService(model_name=missing.name)
    assert service.model_path.name in {missing.name, "yolov8n.pt"}
