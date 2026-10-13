"""Fix: JSON error responses with correct status codes, and no server paths.

Clients that ask for JSON (X-Requested-With: XMLHttpRequest, or
Accept: application/json) always get {"error": "..."} with the HTTP status
that matches the problem. Error messages never include absolute paths.
"""

import io

import pytest

import app as app_module
import tracker as tracker_module

JSON_HEADERS = {"Accept": "application/json"}
MP4_HEADER = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


def _assert_json_error(response, status):
    assert response.status_code == status
    assert response.mimetype == "application/json"
    body = response.get_json()
    assert set(body) == {"error"}
    assert isinstance(body["error"], str) and body["error"]
    assert str(app_module.BASE_DIR) not in body["error"], "error must not expose server paths"
    return body["error"]


def test_missing_result_returns_json_404(client):
    response = client.get("/result/", headers=JSON_HEADERS)
    _assert_json_error(response, 404)


def test_unknown_route_returns_json_404_for_api_clients(client):
    response = client.get("/does-not-exist", headers=JSON_HEADERS)
    _assert_json_error(response, 404)


def test_wrong_method_returns_json_405_for_api_clients(client):
    response = client.get("/upload", headers=JSON_HEADERS)
    _assert_json_error(response, 405)


def test_browser_404_keeps_the_default_html_page(client):
    response = client.get("/result/?file=missing.mp4")
    assert response.status_code == 404
    assert response.mimetype == "text/html"


def test_upload_too_large_returns_json_413(client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "MAX_CONTENT_LENGTH", 1024)
    response = client.post(
        "/upload",
        data={"video": (io.BytesIO(MP4_HEADER + b"x" * 4096), "big.mp4")},
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    message = _assert_json_error(response, 413)
    assert "too large" in message.lower()


def test_processing_failure_hides_internal_details(client, monkeypatch):
    def fail(path):
        raise tracker_module.TrackingError("Inference failed: secret internal detail")

    monkeypatch.setattr(app_module, "process_video", fail)
    response = client.post(
        "/upload",
        data={"video": (io.BytesIO(MP4_HEADER), "clip.mp4")},
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    message = _assert_json_error(response, 500)
    assert "secret internal detail" not in message
    assert "Reference:" in message


def test_unreadable_video_is_a_client_error(client, monkeypatch, fake_yolo):
    def unreadable(**kwargs):
        raise FileNotFoundError("Failed to open video /private/var/folders/x/clip.mp4")

    monkeypatch.setattr(fake_yolo, "track", lambda self, **kwargs: unreadable(**kwargs))
    response = client.post(
        "/upload",
        data={"video": (io.BytesIO(MP4_HEADER), "clip.mp4")},
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    message = _assert_json_error(response, 400)
    assert "/private/var" not in message
