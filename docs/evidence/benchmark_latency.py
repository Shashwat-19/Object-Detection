"""Measure inference latency for the YOLO settings this app uses.

Two measurements are taken:

1. Detection latency: one image, repeated runs, using the same weights and
   arguments as tracker.py (imgsz=320, conf=0.3, device=cpu). Preprocessing,
   inference and NMS are inside Ultralytics predict(), so the per-stage times
   come from results.speed.
2. End-to-end upload latency (optional, --upload-url): POST a real video to
   the running server and time the full request, including tracking.

Run from the repository root with the project's environment:

    python docs/evidence/benchmark_latency.py \
        --image docs/evidence/sample-frame.jpg --runs 50 \
        --upload-url http://127.0.0.1:8000/upload --video samples/sample.mp4 \
        --upload-runs 5 --out docs/evidence/results/latency-results.json

The first detection call is reported as the cold call. The timed runs after
it are warm.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
import requests
import torch
import ultralytics
from ultralytics import YOLO

WEIGHTS = "yolov8n.pt"  # TrackingService default in tracker.py
IMGSZ = 320  # tracker.py, model.track(imgsz=320)
CONF = 0.3  # tracker.py, TrackingService.confidence
DEVICE = "cpu"  # TrackingService.device


def hardware_name() -> str:
    try:
        out = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return platform.processor() or platform.machine()


def summarize(values_ms: list[float]) -> dict:
    arr = np.asarray(values_ms, dtype=float)
    return {
        "n": int(arr.size),
        "mean_ms": round(float(arr.mean()), 2),
        "p50_ms": round(float(np.percentile(arr, 50)), 2),
        "p95_ms": round(float(np.percentile(arr, 95)), 2),
        "min_ms": round(float(arr.min()), 2),
        "max_ms": round(float(arr.max()), 2),
    }


def measure_detection(image_path: Path, runs: int) -> dict:
    frame = cv2.imread(str(image_path))  # decode is excluded from timing
    if frame is None:
        raise SystemExit(f"Could not read image: {image_path}")

    load_start = time.perf_counter()
    model = YOLO(WEIGHTS)
    load_ms = (time.perf_counter() - load_start) * 1000

    def one_call():
        start = time.perf_counter()
        result = model.predict(frame, imgsz=IMGSZ, conf=CONF, device=DEVICE, verbose=False)[0]
        wall_ms = (time.perf_counter() - start) * 1000
        return result, wall_ms

    cold_result, cold_ms = one_call()

    wall, pre, inf, post, detections = [], [], [], [], []
    for _ in range(runs):
        result, wall_ms = one_call()
        wall.append(wall_ms)
        pre.append(result.speed["preprocess"])
        inf.append(result.speed["inference"])
        post.append(result.speed["postprocess"])
        detections.append(len(result.boxes))

    return {
        "image": str(image_path),
        "image_shape": list(frame.shape),
        "model_load_ms": round(load_ms, 2),
        "cold_call_ms": round(cold_ms, 2),
        "cold_call_detections": len(cold_result.boxes),
        "warm_wall_clock": summarize(wall),
        "warm_stage_preprocess": summarize(pre),
        "warm_stage_inference": summarize(inf),
        "warm_stage_postprocess": summarize(post),
        "warm_detections_per_run": {
            "min": int(min(detections)),
            "max": int(max(detections)),
        },
    }


def measure_upload(upload_url: str, video: Path, runs: int) -> dict:
    timings = []
    statuses = []
    for _ in range(runs):
        with video.open("rb") as handle:
            start = time.perf_counter()
            response = requests.post(
                upload_url,
                files={"video": (video.name, handle, "video/mp4")},
                allow_redirects=False,
                timeout=900,
            )
            timings.append((time.perf_counter() - start) * 1000)
        statuses.append(response.status_code)
    return {
        "url": upload_url,
        "video": str(video),
        "status_codes": statuses,
        "end_to_end": summarize(timings),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=50, help="Warm detection runs (minimum 20)")
    parser.add_argument("--upload-url", help="Running server's /upload URL")
    parser.add_argument("--video", type=Path, default=Path("samples/sample.mp4"))
    parser.add_argument("--upload-runs", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path("docs/evidence/results/latency-results.json"))
    args = parser.parse_args()

    if args.runs < 20:
        raise SystemExit("Use at least 20 runs.")

    results = {
        "hardware": {
            "cpu": hardware_name(),
            "logical_cores": os.cpu_count(),
            "os": platform.platform(),
            "device_used": DEVICE,
        },
        "software": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "ultralytics": ultralytics.__version__,
        },
        "settings": {
            "weights": WEIGHTS,
            "imgsz": IMGSZ,
            "conf": CONF,
            "iou": "Ultralytics default (0.7), not passed by the app",
        },
        "detection": measure_detection(args.image, args.runs),
    }

    if args.upload_url:
        results["upload"] = measure_upload(args.upload_url, args.video, args.upload_runs)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
