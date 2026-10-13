"""Fix: validate upload type and name, and keep invalid files off disk.

Before this fix, the upload check looked only at the file name. A text file
named clip.mp4 was saved and passed to the model, which failed with a 500.
"""

import io

import pytest

import app as app_module

MP4_HEADER = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64
AVI_HEADER = b"RIFF\x00\x00\x00\x00AVI LIST" + b"\x00" * 64
TEXT_BODY = b"this is plain text, not a video\n"


def _post(client, data, filename, content_type=None, extra_headers=None):
    part = (io.BytesIO(data), filename)
    if content_type:
        part = (io.BytesIO(data), filename, content_type)
    return client.post(
        "/upload",
        data={"video": part},
        content_type="multipart/form-data",
        headers=extra_headers or {},
    )


def _upload_files():
    return set(app_module.UPLOAD_DIR.iterdir())


@pytest.fixture
def stub_processing(monkeypatch):
    """Replace inference with a stub that records its input and writes an output."""
    seen = []

    def fake_process(path):
        seen.append(path)
        output = app_module.OUTPUT_DIR / "test_stub_output.mp4"
        output.write_bytes(MP4_HEADER)
        return str(output)

    monkeypatch.setattr(app_module, "process_video", fake_process)
    yield seen
    (app_module.OUTPUT_DIR / "test_stub_output.mp4").unlink(missing_ok=True)


def test_text_file_named_mp4_is_rejected_before_processing(client, stub_processing):
    before = _upload_files()

    response = _post(client, TEXT_BODY, "clip.mp4", extra_headers={"X-Requested-With": "XMLHttpRequest"})

    assert response.status_code == 400
    assert response.get_json()["error"].startswith("The file is not a supported video")
    assert stub_processing == []
    assert _upload_files() == before, "rejected upload must not stay on disk"


def test_mp4_extension_with_avi_signature_is_rejected(client, stub_processing):
    response = _post(client, AVI_HEADER, "clip.mp4", extra_headers={"X-Requested-With": "XMLHttpRequest"})

    assert response.status_code == 400
    assert stub_processing == []


def test_unsupported_extension_is_rejected(client, stub_processing):
    response = _post(client, MP4_HEADER, "photo.jpg", extra_headers={"X-Requested-With": "XMLHttpRequest"})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Unsupported format. Upload MP4, AVI, MOV, MKV, or WebM."


def test_declared_html_content_type_is_rejected(client, stub_processing):
    response = _post(client, MP4_HEADER, "clip.mp4", content_type="text/html",
                     extra_headers={"X-Requested-With": "XMLHttpRequest"})

    assert response.status_code == 400
    assert stub_processing == []


def test_valid_mp4_is_accepted_and_temporary_file_is_removed(client, stub_processing):
    response = _post(client, MP4_HEADER, "clip.mp4", content_type="video/mp4")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/result/?file=test_stub_output.mp4")
    assert len(stub_processing) == 1
    assert not stub_processing[0].exists(), "uploaded source must be deleted after processing"


def test_stored_name_is_sanitized_and_stays_inside_the_upload_folder(client, stub_processing):
    _post(client, MP4_HEADER, "../../evil name.mp4", content_type="video/mp4")

    stored = stub_processing[0]
    assert stored.parent == app_module.UPLOAD_DIR
    assert ".." not in stored.name and "/" not in stored.name
    assert stored.suffix == ".mp4"


def test_name_that_sanitizes_to_nothing_keeps_the_extension(client, stub_processing):
    _post(client, MP4_HEADER, "%%%.mp4", content_type="video/mp4")

    stored = stub_processing[0]
    assert stored.suffix == ".mp4", "the stored file must keep a video extension"
