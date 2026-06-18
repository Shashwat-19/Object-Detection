from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from tracker import TrackingError, process_video

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


@app.post("/upload")
def upload():
    file = request.files.get("video")
    if file is None or file.filename == "":
        return render_template("index.html", error="Select a video before running tracking."), 400

    if not allowed_file(file.filename):
        return (
            render_template(
                "index.html",
                error="Unsupported format. Upload MP4, AVI, MOV, MKV, or WebM.",
            ),
            400,
        )

    original_name = secure_filename(file.filename)
    upload_name = f"{Path(original_name).stem}_{uuid.uuid4().hex[:10]}{Path(original_name).suffix.lower()}"
    upload_path = UPLOAD_DIR / upload_name

    try:
        logger.info("Saving uploaded file: %s", upload_name)
        file.save(upload_path)
        file_size_mb = upload_path.stat().st_size / (1024 * 1024)
        logger.info("File saved (%.1f MB). Starting processing...", file_size_mb)

        output_path = Path(process_video(upload_path))
        logger.info("Processing complete: %s", output_path.name)
    except TrackingError as exc:
        logger.error("TrackingError: %s", exc)
        return render_template("index.html", error=str(exc)), 500
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        return render_template("index.html", error=f"Processing failed: {exc}"), 500

    return redirect(url_for("result", file=output_path.name))


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


@app.errorhandler(413)
def request_entity_too_large(_error):
    return render_template("index.html", error="File is too large. Maximum upload size is 100 MB."), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
