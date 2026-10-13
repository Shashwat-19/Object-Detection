from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from tracker import TrackingError, UnreadableVideoError, process_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
OUTPUT_DIR = BASE_DIR / "static" / "outputs"
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    """Health check endpoint for Render."""
    return {"status": "ok"}, 200


@app.get("/debug")
def debug():
    """Diagnostic endpoint — shows environment info for troubleshooting."""
    import shutil
    import subprocess
    import sys

    import cv2

    info = {
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "base_dir": str(BASE_DIR),
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "output_dir_exists": OUTPUT_DIR.exists(),
    }

    # Check model files
    for name in ["yolov8n.pt", "yolov8m.pt"]:
        path = BASE_DIR / name
        info[f"model_{name}"] = {
            "exists": path.exists(),
            "size_mb": round(path.stat().st_size / 1024 / 1024, 1) if path.exists() else None,
        }

    # Memory info
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total_mb": round(mem.total / 1024 / 1024),
            "available_mb": round(mem.available / 1024 / 1024),
            "used_percent": mem.percent,
        }
    except Exception as e:
        info["memory_error"] = str(e)

    # Disk info
    try:
        disk = shutil.disk_usage(str(BASE_DIR))
        info["disk"] = {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 1),
        }
    except Exception as e:
        info["disk_error"] = str(e)

    # OpenCV info
    info["opencv_version"] = cv2.__version__
    info["opencv_ffmpeg"] = bool(cv2.getBuildInformation().find("FFMPEG") >= 0 and "YES" in cv2.getBuildInformation().split("FFMPEG")[1][:20])

    # Check ffmpeg binary
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        info["ffmpeg_binary"] = result.stdout.split("\n")[0] if result.returncode == 0 else "not found"
    except Exception:
        info["ffmpeg_binary"] = "not found"

    # PyTorch info
    try:
        import torch
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
    except Exception as e:
        info["torch_error"] = str(e)

    # Ultralytics info
    try:
        import ultralytics
        info["ultralytics_version"] = ultralytics.__version__
    except Exception as e:
        info["ultralytics_error"] = str(e)

    return info, 200


def _has_video_signature(header: bytes, suffix: str) -> bool:
    """Check the first bytes of a file against the container its extension names."""
    if suffix in {".mp4", ".mov"}:
        return header[4:8] == b"ftyp"
    if suffix == ".avi":
        return header[0:4] == b"RIFF" and header[8:12] == b"AVI "
    if suffix in {".mkv", ".webm"}:
        return header[0:4] == b"\x1a\x45\xdf\xa3"  # EBML header
    return False


@app.post("/upload")
def upload():
    file = request.files.get("video")
    if file is None or file.filename == "":
        return _error_response("Select a video before running tracking.", 400)

    if not allowed_file(file.filename):
        return _error_response("Unsupported format. Upload MP4, AVI, MOV, MKV, or WebM.", 400)

    suffix = Path(file.filename).suffix.lower()

    # The declared Content-Type is checked only to reject obvious mismatches
    # such as text/html. The file contents are the real test.
    declared_type = (file.mimetype or "").lower()
    if declared_type and not (declared_type.startswith("video/") or declared_type == "application/octet-stream"):
        return _error_response("Unsupported format. Upload MP4, AVI, MOV, MKV, or WebM.", 400)

    header = file.stream.read(16)
    file.stream.seek(0)
    if not _has_video_signature(header, suffix):
        return _error_response(
            "The file is not a supported video. Its contents do not match the file extension.", 400
        )

    # Build the stored name from a sanitized stem, so a name that sanitizes to
    # nothing (for example "%%%.mp4") still ends with the video extension.
    stem = secure_filename(Path(file.filename).stem) or "video"
    upload_name = f"{stem}_{uuid.uuid4().hex[:10]}{suffix}"
    upload_path = UPLOAD_DIR / upload_name

    try:
        logger.info("Saving uploaded file: %s", upload_name)
        file.save(upload_path)
        file_size_mb = upload_path.stat().st_size / (1024 * 1024)
        logger.info("File saved (%.1f MB). Starting processing...", file_size_mb)

        output_path = Path(process_video(upload_path))
        logger.info("Processing complete: %s", output_path.name)
    except UnreadableVideoError:
        return _error_response("The video could not be read. Upload a different file.", 400)
    except TrackingError:
        ref = _new_reference()
        logger.exception("Tracking failed (reference %s)", ref)
        return _error_response(f"Processing failed. Reference: {ref}", 500)
    except Exception:
        ref = _new_reference()
        logger.exception("Unexpected error during upload (reference %s)", ref)
        return _error_response(f"Processing failed. Reference: {ref}", 500)
    finally:
        # process_video deletes its input. This also covers failures before it runs.
        upload_path.unlink(missing_ok=True)

    return redirect(url_for("result", file=output_path.name))


def _wants_json() -> bool:
    """True when the client asked for JSON: XHR requests or Accept: application/json."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", "")


def _new_reference() -> str:
    """Short ID that ties a client-facing error to its log entry."""
    return uuid.uuid4().hex[:8]


def _error_response(message: str, status_code: int):
    """Return error as JSON for API clients, or the upload page with an alert for browsers."""
    if _wants_json():
        return {"error": message}, status_code
    return render_template("index.html", error=message), status_code


@app.get("/result/")
def result():
    filename = request.args.get("file")
    if not filename:
        abort(404)

    output_path = OUTPUT_DIR / secure_filename(filename)
    if not output_path.exists():
        abort(404)

    return render_template(
        "result.html",
        video_url=url_for("static", filename=f"outputs/{output_path.name}"),
        download_url=url_for("download", filename=output_path.name),
        filename=output_path.name,
    )


@app.get("/download/")
def download():
    filename = request.args.get("filename") or request.args.get("file")
    if not filename:
        abort(404)

    safe_name = secure_filename(filename)
    output_path = OUTPUT_DIR / safe_name
    if not output_path.exists():
        abort(404)

    return send_from_directory(OUTPUT_DIR, safe_name, as_attachment=True)


@app.errorhandler(HTTPException)
def handle_http_error(error: HTTPException):
    """Return {"error": ...} to API clients. Browsers keep the default page or the upload alert."""
    if error.code == 413:
        message = "File is too large. Maximum upload size is 100 MB."
    else:
        message = error.description

    if _wants_json():
        return {"error": message}, error.code
    if request.endpoint == "upload" and error.code in (400, 413):
        return render_template("index.html", error=message), error.code
    return error


@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception):
    if isinstance(error, HTTPException):
        return handle_http_error(error)
    ref = _new_reference()
    logger.exception("Unhandled error (reference %s)", ref)
    message = f"Internal server error. Reference: {ref}"
    if _wants_json():
        return {"error": message}, 500
    return message, 500, {"Content-Type": "text/plain; charset=utf-8"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)

