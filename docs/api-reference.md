# API reference

This reference covers every HTTP route in `app.py`, plus the static file route that Flask adds. The machine-readable version is in [`openapi.yaml`](openapi.yaml).

The examples use the base URL `http://127.0.0.1:8000`, which is the address the [quickstart](quickstart.md) uses. Each response example comes from a real request in `evidence/curl/`. Absolute paths in those examples are shown as `/path/to/Object-Detection`.

The application programming interface (API) has no authentication. Anyone who can reach the server can call every route. The [technical report](technical-report.md#security-considerations) describes the protections that are in place.

## Error format

Requests that ask for JSON get JSON errors. A request asks for JSON when it sends either of these headers:

- `X-Requested-With: XMLHttpRequest`
- `Accept: application/json`

Error bodies have one field:

```json
{"error":"Unsupported format. Upload MP4, AVI, MOV, MKV, or WebM."}
```

Browser requests without these headers get HTML. Upload errors show the upload page with an alert. Other errors show the default page for the status.

## Routes at a glance

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Show the upload page. |
| `GET` | `/health` | Return a health check. |
| `GET` | `/debug` | Return environment details. Off unless `ENABLE_DEBUG_ENDPOINT` is set. |
| `POST` | `/upload` | Upload a video and track objects in it. |
| `GET` | `/result/` | Show the result page for a processed video. |
| `GET` | `/download/` | Download a processed video. |
| `GET` | `/static/{path}` | Serve files in `static/`, including processed videos. |

## GET /

Shows the upload page. This is an HTML page for people, not an API response.

### Parameters

None.

### Request examples

curl:

```bash
curl -i http://127.0.0.1:8000/
```

Python `requests`:

```python
import requests

response = requests.get("http://127.0.0.1:8000/", timeout=10)
print(response.status_code)
print(response.headers["Content-Type"])
```

### Response

Status `200 OK` with `Content-Type: text/html; charset=utf-8`. The body is the upload page. It begins like this (abbreviated):

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>TrackVision AI | Occlusion-Aware Multi-Object Tracking</title>
```

### Status codes

| Code | Meaning |
| --- | --- |
| `200` | The page is returned. |

## GET /health

Returns a health check. Use it to confirm that the server responds.

The server runs four threads, and one video is tracked at a time. `/health` answers while a video is processing. Before the fix, it waited for the upload to finish (see `evidence/results/health-during-upload.txt`).

### Parameters

None.

### Request examples

curl:

```bash
curl -i http://127.0.0.1:8000/health
```

Python `requests`:

```python
import requests

response = requests.get("http://127.0.0.1:8000/health", timeout=10)
print(response.status_code, response.json())
```

### Response

Status `200 OK`, `Content-Type: application/json`.

```json
{"status":"ok"}
```

| Field | Type | Description |
| --- | --- | --- |
| `status` | string | Always `"ok"` when the server responds. |

### Status codes

| Code | Meaning |
| --- | --- |
| `200` | The server is running. |

## GET /debug

Returns environment details for troubleshooting: paths, memory and disk use, and library versions.

The route is off by default and returns `404`. To turn it on, set `ENABLE_DEBUG_ENDPOINT=1` before you start the server. Do not enable it on a public server, because the response shows host details.

### Parameters

None.

### Request examples

curl (after you set `ENABLE_DEBUG_ENDPOINT=1` and restart the server):

```bash
curl -s http://127.0.0.1:8000/debug
```

Python `requests`:

```python
import requests

info = requests.get("http://127.0.0.1:8000/debug", timeout=30)
if info.status_code == 404:
    print("Set ENABLE_DEBUG_ENDPOINT=1 and restart the server.")
else:
    print(info.json()["torch_version"], info.json()["ultralytics_version"])
```

### Response

When the route is off, the status is `404 Not Found` with Flask's HTML page.

When it is on, the status is `200 OK` with `Content-Type: application/json`. The example below is from one run. Values change with the machine and the time.

```json
{"base_dir":"/path/to/Object-Detection","cuda_available":false,"cwd":"/path/to/Object-Detection","disk":{"free_gb":19.4,"total_gb":228.3},"ffmpeg_binary":"ffmpeg version 8.0.1 Copyright (c) 2000-2025 the FFmpeg developers","memory":{"available_mb":1123,"total_mb":8192,"used_percent":86.3},"model_yolov8m.pt":{"exists":false,"size_mb":null},"model_yolov8n.pt":{"exists":true,"size_mb":6.2},"opencv_ffmpeg":false,"opencv_version":"5.0.0","output_dir_exists":true,"python_version":"3.11.15 (main, Mar  3 2026, 00:52:57) [Clang 21.0.0 (clang-2100.0.123.102)]","torch_version":"2.11.0","ultralytics_version":"8.4.49","upload_dir_exists":true}
```

| Field | Type | Description |
| --- | --- | --- |
| `base_dir` | string | Absolute path of the project folder. |
| `cwd` | string | Current working directory of the server process. |
| `upload_dir_exists` | boolean | Whether `static/uploads` exists. |
| `output_dir_exists` | boolean | Whether `static/outputs` exists. |
| `model_yolov8n.pt` | object | `exists` (boolean) and `size_mb` (number) for the nano weights. |
| `model_yolov8m.pt` | object | The same fields for the medium weights. |
| `memory` | object | `total_mb`, `available_mb`, and `used_percent` for system memory. Replaced by `memory_error` if it cannot be read. |
| `disk` | object | `total_gb` and `free_gb` for the disk that holds the project. Replaced by `disk_error` if it cannot be read. |
| `opencv_version` | string | OpenCV version. |
| `opencv_ffmpeg` | boolean | Whether OpenCV reports FFmpeg support. This is a text search of the build information, so treat it as a hint. |
| `ffmpeg_binary` | string | First line of `ffmpeg -version`, or `"not found"`. |
| `python_version` | string | Full Python version string. |
| `torch_version` | string | PyTorch version. Replaced by `torch_error` if PyTorch fails to import. |
| `cuda_available` | boolean | Whether PyTorch can use CUDA. Present only when PyTorch imports. |
| `ultralytics_version` | string | Ultralytics version. Replaced by `ultralytics_error` if it fails to import. |

### Status codes

| Code | Meaning |
| --- | --- |
| `200` | Enabled, and the information is returned. Individual fields can contain error text. |
| `404` | Disabled (the default). |

## POST /upload

Uploads one video and runs detection and tracking on it. This route does the work. It can take several seconds to minutes, depending on the video length and resolution.

### Parameters

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `video` | form (multipart) | file | Yes | The video to process. The file name must end in `.mp4`, `.avi`, `.mov`, `.mkv`, or `.webm` (case does not matter). The file's first bytes must match that container. Maximum size: 100 MiB (104,857,600 bytes). |
| `X-Requested-With` | header | string | No | Send `XMLHttpRequest` to receive JSON errors instead of HTML. |
| `Accept` | header | string | No | Send `application/json` to receive JSON errors instead of HTML. |

The server checks three things before it saves a file:

1. The extension is one of the allowed types.
2. The declared `Content-Type` is `video/*` or `application/octet-stream`. This is a sanity check only, because clients set that header.
3. The first bytes of the file match the container the extension names. An MP4 or MOV file needs an `ftyp` box, an AVI file needs `RIFF` and `AVI `, and an MKV or WebM file needs the EBML header.

A rejected file is never written to disk. The uploaded file is deleted when processing ends, including when it fails.

### Request examples

curl, with the sample clip:

```bash
curl -s -o /dev/null -D - -F video=@samples/sample.mp4 http://127.0.0.1:8000/upload
```

curl, to get JSON errors. This example sends a JPEG, which the route rejects:

```bash
curl -s -H "X-Requested-With: XMLHttpRequest" -F video=@docs/evidence/sample-frame.jpg http://127.0.0.1:8000/upload
```

Python `requests`:

```python
import requests
from urllib.parse import parse_qs, urlparse

BASE_URL = "http://127.0.0.1:8000"

with open("samples/sample.mp4", "rb") as video:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"video": ("sample.mp4", video, "video/mp4")},
        allow_redirects=False,
        timeout=900,
    )

print(response.status_code)            # 302 on success
location = response.headers["Location"]
print(location)                        # /result/?file=track_sample_...mp4

result_name = parse_qs(urlparse(location).query)["file"][0]
print(result_name)
```

Set `allow_redirects=False`. Otherwise `requests` follows the redirect to the result page, and the `Location` header is lost.

### Response

**Success.** Status `302 Found`. The `Location` header points to the result page. The `file` query parameter holds the name of the processed video. The body is a standard redirect page.

```http
HTTP/1.1 302 FOUND
Content-Type: text/html; charset=utf-8
Location: /result/?file=track_sample_6311d0daa7_b7b6dc424a.mp4
```

```html
<!doctype html>
<html lang=en>
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to the target URL: <a href="/result/?file=track_sample_6311d0daa7_b7b6dc424a.mp4">/result/?file=track_sample_6311d0daa7_b7b6dc424a.mp4</a>. If not, click the link.
```

The name has the form `track_<original-stem>_<10 hex>_<10 hex>.mp4`. Use it with `/download/` and `/result/`.

**Error, JSON form.** Returned when the request has `X-Requested-With: XMLHttpRequest`:

```json
{"error":"Unsupported format. Upload MP4, AVI, MOV, MKV, or WebM."}
```

| Field | Type | Description |
| --- | --- | --- |
| `error` | string | Message for the user. |

**Error, HTML form.** Returned for all other requests. The response is the upload page with a red alert that contains the same message.

### Status codes and errors

| Code | Condition | Message | Evidence |
| --- | --- | --- | --- |
| `302` | Processing succeeded. | (redirect) | `04-post-upload-valid.txt` |
| `400` | No `video` field, or the field is empty. | `Select a video before running tracking.` | `10-post-upload-missing-file.txt` |
| `400` | Unsupported extension, or a declared content type that is not video. | `Unsupported format. Upload MP4, AVI, MOV, MKV, or WebM.` | `08-…`, `09-…` |
| `400` | The file's contents do not match its extension. | `The file is not a supported video. Its contents do not match the file extension.` | `11-post-upload-fake-mp4.txt` |
| `400` | The model cannot open the file, even though its header is valid. | `The video could not be read. Upload a different file.` | Tested in `tests/test_errors.py`. |
| `413` | Request body is larger than 100 MiB. | `File is too large. Maximum upload size is 100 MB.` | `12-post-upload-too-large.txt` |
| `500` | Any other processing failure. | `Processing failed. Reference: <8 hex characters>` | Tested in `tests/test_errors.py`. The server log has the details under the same reference. |

A file name that cleans up to nothing, such as `%%%.mp4`, is accepted and stored with the `.mp4` extension (`14-post-upload-unsanitizable-name.txt`).

The `500` message does not include server paths or internal error text.

## GET /result/

Shows the result page for a processed video. The page plays the video, offers a download link, and shows four values measured while the video was tracked: unique track IDs, detections, frames processed, and processing time. If the measurements are missing, the page shows `—`.

### Parameters

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `file` | query | string | Yes | The processed video name, from the `Location` header of `POST /upload`. The name is sanitized before use. |

### Request examples

curl:

```bash
curl -i "http://127.0.0.1:8000/result/?file=track_sample_6311d0daa7_b7b6dc424a.mp4"
```

Python `requests`:

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/result/",
    params={"file": "track_sample_6311d0daa7_b7b6dc424a.mp4"},
    timeout=10,
)
print(response.status_code, response.headers["Content-Type"])
```

### Response

Status `200 OK`, `Content-Type: text/html; charset=utf-8`. The page contains the video player, a download link to `/download/`, and the four measured values. The page starts like this (abbreviated):

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Tracking Result | TrackVision AI</title>
```

The measured values are also stored next to the video as `<name>.json`, with this shape:

```json
{"frames_processed": 40, "total_detections": 133, "unique_track_ids": 15, "processing_seconds": 0.97}
```

| Field | Type | Description |
| --- | --- | --- |
| `frames_processed` | integer | Sampled frames that the model processed (every third source frame). |
| `total_detections` | integer | Sum of detected boxes across the sampled frames. |
| `unique_track_ids` | integer | Number of distinct track IDs in the video. |
| `processing_seconds` | number | Wall-clock time for tracking, rounded to 0.01 s. |

### Status codes

| Code | Condition | Evidence |
| --- | --- | --- |
| `200` | The file exists in `static/outputs`. | `05-get-result.txt` |
| `404` | The `file` parameter is missing. | `15-get-result-no-file.txt` |
| `404` | No file with that name exists. | `16-get-result-missing-file.txt` |
| `404` | The name points outside `static/outputs` after sanitizing. | `24-get-result-path-traversal.txt` |
| `308` | The request has no trailing slash. Flask redirects to `/result/`. | `21-get-result-no-trailing-slash.txt` |

A `404` from this route is JSON when the request asks for JSON, and the default HTML page otherwise.

## GET /download/

Downloads a processed video.

### Parameters

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `filename` | query | string | Yes* | The processed video name. |
| `file` | query | string | Yes* | Alias for `filename`. Used if `filename` is absent. |

\* Send one of the two. The name is sanitized before use.

### Request examples

curl:

```bash
curl -o tracked.mp4 "http://127.0.0.1:8000/download/?filename=track_sample_6311d0daa7_b7b6dc424a.mp4"
```

Python `requests`:

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/download/",
    params={"filename": "track_sample_6311d0daa7_b7b6dc424a.mp4"},
    timeout=60,
)
with open("tracked.mp4", "wb") as out:
    out.write(response.content)
print(response.status_code, response.headers["Content-Type"])
```

### Response

Status `200 OK`. The body is the MP4 file.

```http
HTTP/1.1 200 OK
Content-Disposition: attachment; filename=track_sample_6311d0daa7_b7b6dc424a.mp4
Content-Type: video/mp4
Accept-Ranges: bytes
```

| Header | Value | Description |
| --- | --- | --- |
| `Content-Type` | `video/mp4` | The MIME type. |
| `Content-Disposition` | `attachment; filename=…` | Tells the browser to save the file. |
| `Accept-Ranges` | `bytes` | The server supports range requests. |

### Status codes

| Code | Condition | Evidence |
| --- | --- | --- |
| `200` | The file exists. | `06-get-download.txt`, `07-get-download-file-alias.txt` |
| `404` | Neither `filename` nor `file` is given. | `17-get-download-no-param.txt` |
| `404` | No file with that name exists. | `18-get-download-missing-file.txt` |
| `404` | Path traversal attempt, such as `../../app.py`. | `23-get-download-path-traversal.txt` |
| `308` | The request has no trailing slash. Flask redirects to `/download/`. | `22-get-download-no-trailing-slash.txt` |

## GET /static/{path}

Flask serves files from the `static/` folder at this path. The result page uses it to play the video. Processed videos are in `static/outputs/`.

### Parameters

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `path` | path | string | Yes | File path inside `static/`, such as `outputs/track_sample_6311d0daa7_b7b6dc424a.mp4`. |

### Request examples

curl, with a byte range:

```bash
curl -s -r 0-15 -D - -o /dev/null "http://127.0.0.1:8000/static/outputs/track_sample_6311d0daa7_b7b6dc424a.mp4"
```

Python `requests`:

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/static/outputs/track_sample_6311d0daa7_b7b6dc424a.mp4",
    timeout=30,
)
print(response.status_code, len(response.content))
```

### Response

Status `200 OK` for the full file, or `206 Partial Content` for a range. The file is served inline, so a browser plays it. Evidence (`25-get-static-output-video.txt`):

```http
HTTP/1.1 206 PARTIAL CONTENT
Content-Disposition: inline; filename=track_sample_6311d0daa7_b7b6dc424a.mp4
Content-Type: video/mp4
Content-Length: 16
```

The app never deletes processed videos, so they stay on disk until someone removes them. Anyone with the link can view them. See [Known limitations](technical-report.md#known-limitations).

### Status codes

| Code | Condition | Evidence |
| --- | --- | --- |
| `200` | The file exists and no range is requested. | `25b-get-static-output-video-full.txt` |
| `206` | The request asked for a byte range, and the file exists. | `25-get-static-output-video.txt` |
| `404` | The file does not exist. | `26-get-static-missing.txt` |

## Calling the API from a script

The following script runs the full flow: upload, then download. It uses only `requests`.

```python
import requests
from urllib.parse import parse_qs, urlparse

BASE_URL = "http://127.0.0.1:8000"

with open("samples/sample.mp4", "rb") as video:
    upload = requests.post(
        f"{BASE_URL}/upload",
        files={"video": ("sample.mp4", video, "video/mp4")},
        allow_redirects=False,
        timeout=900,
    )
if upload.status_code != 302:
    raise SystemExit(f"Upload failed: {upload.status_code} {upload.text[:200]}")

name = parse_qs(urlparse(upload.headers["Location"]).query)["file"][0]
download = requests.get(f"{BASE_URL}/download/", params={"filename": name}, timeout=60)
download.raise_for_status()
with open("tracked.mp4", "wb") as out:
    out.write(download.content)
print("saved tracked.mp4", len(download.content), "bytes")
```
