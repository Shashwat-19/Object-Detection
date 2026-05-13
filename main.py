from ultralytics import YOLO

model = YOLO("yolov8n.pt")

results = model.track(
    source="videos/test.mp4",
    show=True,
    save=True,
    tracker="bytetrack.yaml"
)