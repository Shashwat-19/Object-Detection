# Quickstart: run your first detection

This guide takes you from a fresh clone to a tracked video in six steps. Setup takes about two minutes on a fast connection, plus the time to download PyTorch.

## Before you start

- Python 3.11. The project pins `python-3.11.9` in `runtime.txt`.
- About 1.2 GB of free disk space for the virtual environment. The environment measured 1.1 GB on macOS (Apple silicon).
- Port 8000 free. On macOS, port 5000 is often used by AirPlay Receiver, so this guide does not use it.

## Steps

1. Clone the repository and go into it.

   ```bash
   git clone https://github.com/Shashwat-19/Object-Detection.git
   cd Object-Detection
   ```

2. Create and activate a virtual environment.

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the dependencies.

   On Linux, run this command:

   ```bash
   pip install -r requirements.txt
   ```

   On macOS, the pinned `+cpu` PyTorch builds are not available. Remove the `+cpu` suffixes and install from the default index:

   ```bash
   sed -e '/extra-index-url/d' -e 's/+cpu//' requirements.txt > "${TMPDIR:-/tmp}/requirements-macos.txt"
   pip install -r "${TMPDIR:-/tmp}/requirements-macos.txt"
   ```

4. Start the server.

   ```bash
   export PORT=8000
   gunicorn app:app --bind 127.0.0.1:$PORT --timeout 600 --workers 1 --worker-class gthread --threads 4
   ```

   The server loads the model when the worker starts, which can take 15 to 20 seconds. On the first start, Ultralytics also downloads the weights (`yolov8n.pt`, about 6.5 MB) into the project folder. The server is ready when the log shows `Model loaded successfully`. Requests sent before that wait until the model is loaded. The weights stay on disk, so later starts do not download them again.

   Set `PORT` with `export`, as shown. Setting it inline, as in `PORT=8000 gunicorn … $PORT`, leaves the bind address empty.

5. Send a detection request.

   Run this command in the same terminal:

   ```bash
   LOCATION=$(curl -s -o /dev/null -D - -F video=@samples/sample.mp4 http://127.0.0.1:8000/upload | tr -d '\r' | awk '/^Location:/ {print $2}')
   echo "$LOCATION"
   ```

   The command prints a path such as `/result/?file=track_sample_0123456789_0123456789.mp4`. The `Location` header comes from the `302 Found` redirect that `/upload` returns. The sample is a 5-second, 640-pixel clip, so the upload finishes in a few seconds.

6. Download the tracked video.

   ```bash
   FILE="${LOCATION#*file=}"
   curl -s -o tracked.mp4 "http://127.0.0.1:8000/download/?filename=$FILE"
   ```

   Open `tracked.mp4` in a video player. Each detected object has a label with its class, confidence score, and track ID, such as `id:293 car 0.95`. The file contains only every third frame of the source, so it plays for about one third of the original length. See [Known limitations](technical-report.md#known-limitations) for details.

## If something goes wrong

- **`Address already in use`:** Another process uses the port. Choose a different `PORT`, such as `8001`, and use it in steps 4 to 6.
- **`'' is not a valid port number`:** `PORT` is not set in the shell. Run `export PORT=8000` before the `gunicorn` command.
- **`The file is not a supported video`:** The file's contents do not match its extension. Use a real video file.

## Next steps

- Read the [API reference](api-reference.md) for every route and its responses.
- Read the [technical report](technical-report.md) for the architecture, the model settings, and the known limitations.
