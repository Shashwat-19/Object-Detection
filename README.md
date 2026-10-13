# TrackVision AI

Multi-object tracking for uploaded videos, using YOLOv8 and ByteTrack in a Flask web app.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](runtime.txt)

![Example tracking output](trajectory_frame.jpg)

*Example frame from the tracking workflow. Upload a video to produce your own annotated MP4.*

## Features

- Detects 80 COCO object classes with YOLOv8n and assigns persistent track IDs with ByteTrack.
- Accepts MP4, AVI, MOV, MKV, and WebM uploads up to 100 MB, and checks each file's contents before it is processed.
- Returns an annotated MP4 with a label, confidence score, and track ID on each object.
- Shows measured values for each video: unique track IDs, detections, frames processed, and processing time.
- Provides a JSON API with a health check, an OpenAPI 3.0 spec, and consistent JSON errors.
- Runs on CPU, loads the model once at startup, and downloads the weights on first start.

## Quick start

```bash
git clone https://github.com/Shashwat-19/Object-Detection.git && cd Object-Detection
python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
export PORT=8000 && gunicorn app:app --bind 127.0.0.1:$PORT --timeout 600 --workers 1 --worker-class gthread --threads 4
```

The first start downloads the model weights, `yolov8n.pt` (about 6.5 MB), into the project folder. Wait for `Model loaded successfully` in the log, then open <http://127.0.0.1:8000>.

On macOS, the pinned `+cpu` PyTorch builds are not available. Follow step 3 in the [quickstart](docs/quickstart.md) instead.

## Example API call

Upload the sample clip. The server redirects to the result page, and the `file` parameter names the output:

```bash
curl -s -o /dev/null -D - -F video=@samples/sample.mp4 http://127.0.0.1:8000/upload
```

```http
HTTP/1.1 302 FOUND
Content-Type: text/html; charset=utf-8
Location: /result/?file=track_sample_8a78d9517b_29dc62e9a8.mp4
```

Fetch the measured values for that video:

```bash
curl -s http://127.0.0.1:8000/static/outputs/track_sample_8a78d9517b_29dc62e9a8.json
```

```json
{"frames_processed": 40, "total_detections": 133, "unique_track_ids": 15, "processing_seconds": 0.57}
```

Errors return JSON when the request asks for it (`X-Requested-With: XMLHttpRequest` or `Accept: application/json`):

```json
{"error":"The file is not a supported video. Its contents do not match the file extension."}
```

## Documentation

- [Quickstart](docs/quickstart.md): from a fresh clone to a tracked video.
- [API reference](docs/api-reference.md): every route, with examples and status codes.
- [Technical report](docs/technical-report.md): architecture, model settings, measured performance, and known limitations.
- [OpenAPI spec](docs/openapi.yaml): the machine-readable contract.

## Tech stack

| Area | Tools |
| --- | --- |
| Detection and tracking | Ultralytics YOLOv8 (8.4.49), ByteTrack |
| Web app | Flask 3.1, Gunicorn 23 |
| Computer vision | OpenCV, NumPy |
| Runtime | PyTorch 2.11 (CPU), Python 3.11 |
| Front end | Bootstrap 5.3, Bootstrap Icons, vanilla JavaScript |
| Tests | pytest |

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The tests use a fake model, so they do not download weights or run inference.

## License

Released under the [MIT License](LICENSE).

## Author

**Shashwat** · [github.com/Shashwat-19](https://github.com/Shashwat-19)
