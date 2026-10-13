"""Check whether track IDs carry over from one video to the next in one process.

The app keeps a single YOLO model for all uploads. This script runs the same
track() arguments as tracker.py on a shared model and compares two settings:

- persist=True: the setting the app used before the fix (IDs carried over).
- persist=False: the setting the app uses now.

Run from the repository root:

    python docs/evidence/check_tracker_persist.py <second-video>

Use a short second clip so the run is quick. For example, the 2-second clip
used by the curl checks:

    ffmpeg -y -i samples/sample.mp4 -t 2 -vf scale=640:-2 -an /tmp/short.mp4
"""

import sys

from ultralytics import YOLO

FIRST = "samples/sample.mp4"
SECOND = sys.argv[1]

BASE_ARGS = dict(
    tracker="bytetrack.yaml",
    conf=0.3,
    imgsz=320,
    device="cpu",
    vid_stride=3,
    stream=True,
    save=False,
    verbose=False,
)


def first_frame_ids(model, source, persist, frames=3):
    """Return the sorted track IDs for the first few frames of a source."""
    ids_per_frame = []
    for index, result in enumerate(model.track(source=source, persist=persist, **BASE_ARGS)):
        if index >= frames:
            break
        ids = result.boxes.id
        ids_per_frame.append(sorted(ids.int().tolist()) if ids is not None else [])
    return ids_per_frame


def run(persist):
    shared = YOLO("yolov8n.pt")
    for _ in shared.track(source=FIRST, persist=persist, **BASE_ARGS):  # earlier upload, read to the end
        pass
    after_first = first_frame_ids(shared, SECOND, persist)

    fresh = YOLO("yolov8n.pt")
    alone = first_frame_ids(fresh, SECOND, persist)

    print(f"persist={persist}")
    print("  second video after first video (shared model):")
    for frame, ids in enumerate(after_first):
        print(f"    frame {frame}: {ids}")
    print("  second video alone (fresh model):")
    for frame, ids in enumerate(alone):
        print(f"    frame {frame}: {ids}")


run(persist=True)
run(persist=False)
