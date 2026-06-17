from __future__ import annotations

import gc
import logging
import shutil
import threading
import uuid
from pathlib import Path

import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class TrackingError(RuntimeError):
    """Raised when video tracking fails."""


class TrackingService:
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        output_dir: str = "static/outputs",
        confidence: float = 0.3,
    ) -> None:
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir).resolve()
        self.confidence = confidence
        self.device = "cpu"
        self._lock = threading.Lock()
        self._model = None  # lazy-loaded to avoid OOM at startup

        if not self.model_path.exists():
            fallback = Path("yolov8n.pt")
            if fallback.exists():
                self.model_path = fallback
            else:
                raise FileNotFoundError(
                    "No YOLO weights found. Expected yolov8m.pt or yolov8n.pt."
                )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("TrackingService initialized (model=%s, device=%s)", self.model_path, self.device)

    @property
    def model(self) -> YOLO:
        """Lazy-load the YOLO model on first use to reduce startup memory."""
        if self._model is None:
            logger.info("Loading YOLO model: %s", self.model_path)
            self._model = YOLO(str(self.model_path))
            logger.info("Model loaded successfully")
        return self._model

    def process_video(self, video_path: str | Path) -> str:
        source = Path(video_path)
        if not source.exists():
            raise FileNotFoundError(f"Input video not found: {source}")

        file_size_mb = source.stat().st_size / (1024 * 1024)
        logger.info("Processing video: %s (%.1f MB)", source.name, file_size_mb)

        run_name = f"track_{source.stem}_{uuid.uuid4().hex[:10]}"
        run_dir = self.output_dir / run_name

        try:
            with self._lock:
                logger.info("Starting YOLO tracking (imgsz=480, conf=%.2f)", self.confidence)
                results = self.model.track(
                    source=str(source),
                    tracker="bytetrack.yaml",
                    save=True,
                    show=False,
                    conf=self.confidence,
                    persist=True,
                    device=self.device,
                    project=str(self.output_dir),
                    name=run_name,
                    exist_ok=True,
                    stream=True,
                    imgsz=480,
                    vid_stride=2,
                )
                frame_count = 0
                for _ in results:
                    frame_count += 1
                    if frame_count % 50 == 0:
                        logger.info("Processed %d frames...", frame_count)
                        gc.collect()

                logger.info("Tracking complete: %d frames processed", frame_count)
        except Exception as exc:
            logger.error("Inference failed: %s", exc, exc_info=True)
            raise TrackingError(f"Inference failed: {exc}") from exc
        finally:
            # Clean up the uploaded source video to save disk space
            try:
                source.unlink(missing_ok=True)
            except OSError:
                pass
            gc.collect()

        output_video = self._find_output_video(run_dir, source, run_name)
        if output_video is None:
            logger.error("No output video found in %s", run_dir)
            raise TrackingError("Tracking finished but no output video was produced.")

        final_path = self.output_dir / f"{run_name}.mp4"
        if output_video.resolve() != final_path.resolve():
            shutil.move(str(output_video), str(final_path))

        if run_dir.exists():
            shutil.rmtree(run_dir, ignore_errors=True)

        logger.info("Output saved: %s", final_path.name)
        return str(final_path)

    @staticmethod
    def _find_output_video(run_dir: Path, source: Path, run_name: str) -> Path | None:
        search_dirs = [run_dir]
        search_dirs.extend(Path("runs").rglob(run_name))

        preferred_names = [
            f"{source.stem}.mp4",
            f"{source.stem}.avi",
            f"{source.name}",
        ]
        for directory in search_dirs:
            for name in preferred_names:
                candidate = directory / name
                if candidate.exists() and candidate.is_file():
                    return candidate

        videos = sorted(
            [
                path
                for directory in search_dirs
                for path in directory.rglob("*")
                if path.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}
            ]
        )
        return videos[0] if videos else None


service = TrackingService()


def process_video(video_path: str | Path) -> str:
    return service.process_video(video_path)
