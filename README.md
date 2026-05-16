# Object Detection and Tracking

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-111F68?style=for-the-badge)](https://docs.ultralytics.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Repo Size](https://img.shields.io/github/repo-size/Shashwat-19/Object-Detection?style=for-the-badge)](https://github.com/Shashwat-19/Object-Detection)

**YOLOv8-based object detection, multi-object tracking, trajectory analysis, and movement visualization.**

[Open in Colab](https://colab.research.google.com/github/Shashwat-19/Object-Detection/blob/main/Object_detection.ipynb)

</div>

## Overview

This project demonstrates an end-to-end computer vision workflow for detecting and tracking objects in video or image-sequence data. It uses Ultralytics YOLOv8 with ByteTrack to assign stable object IDs across frames, generate annotated tracking output, analyze object trajectories, and visualize movement patterns with heatmaps and distribution plots.

The workflow is implemented in [`Object_detection.ipynb`](Object_detection.ipynb), making it easy to run locally in Jupyter or on Google Colab with GPU acceleration.

## Features

- Object detection with YOLOv8 models
- Multi-object tracking with ByteTrack
- Persistent tracking IDs across frames
- Annotated output video generation
- Object trajectory collection and plotting
- Movement heatmap visualization
- Horizontal and vertical movement distribution analysis
- Basic quantitative tracking metrics, including unique object count and average trajectory length
- GPU support through PyTorch and Ultralytics

## Project Structure

```text
Object-Detection/
├── Object_detection.ipynb      # Main notebook for detection, tracking, and analysis
├── requirements.txt            # Python dependencies
├── videos/
│   └── test.mp4                # Sample input video
├── output/
│   └── tracked_output.mp4      # Sample tracked output video
├── trajectory_frame.jpg        # Example trajectory frame
├── yolov8m.pt                  # YOLOv8 medium model weights
├── yolov8n.pt                  # YOLOv8 nano model weights
├── LICENSE                     # MIT license
└── README.md
```

## Tech Stack

| Category | Tools |
| --- | --- |
| Detection and tracking | Ultralytics YOLOv8, ByteTrack |
| Computer vision | OpenCV |
| ML runtime | PyTorch, Torchvision |
| Data analysis | NumPy, Pandas |
| Visualization | Matplotlib |
| Notebook runtime | Jupyter / Google Colab |

## Getting Started

### Prerequisites

- Python 3.10 or newer
- Jupyter Notebook or JupyterLab
- A CUDA-capable GPU is recommended for faster processing, but CPU execution is supported

### Installation

Clone the repository:

```bash
git clone https://github.com/Shashwat-19/Object-Detection.git
cd Object-Detection
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch Jupyter:

```bash
jupyter notebook Object_detection.ipynb
```

## Usage

### Run the Notebook Locally

1. Open [`Object_detection.ipynb`](Object_detection.ipynb).
2. Choose the model weights:

   ```python
   model = YOLO("yolov8m.pt")
   ```

   Use `yolov8n.pt` for faster inference or `yolov8m.pt` for stronger detection quality.

3. Set the input source:

   ```python
   VIDEO_PATH = "videos/test.mp4"
   ```

   The notebook can also process an image folder, such as a MOT dataset frame directory.

4. Run tracking:

   ```python
   results = model.track(
       source=VIDEO_PATH,
       tracker="bytetrack.yaml",
       save=True,
       show=False,
       conf=0.3,
       persist=True
   )
   ```

5. Generate and inspect the tracked output video and trajectory visualizations.

### Run on Google Colab

The notebook includes Colab-oriented cells for mounting Google Drive and cloning this repository. To run on Colab:

1. Open the notebook using the Colab badge above.
2. Enable GPU from `Runtime > Change runtime type > GPU`.
3. Mount Google Drive if your dataset is stored there.
4. Update `VIDEO_PATH` to point to your video or frame directory.
5. Run all notebook cells.

## Outputs

The workflow can produce:

- Annotated tracking frames from YOLOv8 and ByteTrack
- MP4 tracking output, saved as `tracked_output.mp4` or under `output/`
- Object ID logs per frame
- Trajectory history for each tracked object
- Movement heatmap
- Horizontal and vertical movement distribution plots
- Tracking metrics such as unique objects tracked and average trajectory length

## Example Results

| Preview | Description |
| --- | --- |
| [`output/tracked_output.mp4`](output/tracked_output.mp4) | Sample tracked output video |
| [`trajectory_frame.jpg`](trajectory_frame.jpg) | Example frame used for trajectory visualization |

## Configuration

Common values to tune in the notebook:

| Parameter | Description | Default |
| --- | --- | --- |
| `VIDEO_PATH` | Input video or image-frame directory | Colab Drive path / sample video |
| `tracker` | Tracking algorithm configuration | `bytetrack.yaml` |
| `conf` | Detection confidence threshold | `0.3` |
| `persist` | Reuse object IDs across frames | `True` |
| `device` | Inference device, such as `0` for GPU or `cpu` | `0` in Colab cells |
| `max_trajectories_to_show` | Number of trajectories plotted | `10` |

## Notes

- The included `.pt` files are YOLOv8 model weights. If they are removed, Ultralytics can download supported weights automatically when requested.
- For local CPU-only runs, replace `device=0` with `device="cpu"` or remove the `device` argument.
- The Colab notebook references `/content/drive/MyDrive/MOT17-02-FRCNN/img1` as an example dataset path. Update it to match your own dataset location.
- Large video outputs and model weights can make the repository heavy. Consider using Git LFS for future model and media assets.

## Documentation

Comprehensive documentation for this project is available on [Hashnode](https://hashnode.com/@Shashwat56).

> At present, this README serves as the primary source of documentation.

## License

This project is distributed under the MIT License.  
For detailed licensing information, please refer to the [LICENSE](./LICENSE) file included in this repository.

## Contact  
## Shashwat

**Machine Learning Engineer | Scalable AI Systems**

🔹 **ML systems:** (CV, NLP) + data pipelines<br>
🔹 **End-to-end:** training → deployment<br>
🔹 **Backend & Cloud:** Python, Flask, Node.js, Docker, AWS<br>
🔹 **Projects:** Traffic AI, Video Summarizer, AI Assistants<br>

---

## Open Source | Tech Innovation  
Building robust applications and leveraging cloud technologies for high-performance solutions.

---

### Find me here:  
[<img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" />](https://github.com/Shashwat-19)  [<img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" />](https://www.linkedin.com/in/shashwatk1956/)  [<img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" />](mailto:shashwat1956@gmail.com)  [<img src="https://img.shields.io/badge/Hashnode-2962FF?style=for-the-badge&logo=hashnode&logoColor=white" />](https://hashnode.com/@Shashwat56)
[<img src="https://img.shields.io/badge/HackerRank-15%2B-2EC866?style=for-the-badge&logo=HackerRank&logoColor=white" />](https://www.hackerrank.com/profile/shashwat1956)

> Feel free to connect for tech collaborations, open-source contributions, or brainstorming innovative solutions!
