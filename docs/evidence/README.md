# Evidence

This folder holds the raw output behind the claims in the technical report. Each file names the script that produced it. Run the scripts from the repository root.

| File or folder | Produced by | What it shows |
| --- | --- | --- |
| `curl/*.txt` (28 files) | `run-curl-checks.sh` | The exact `curl` command, status line, response headers, and body for each route, plus error cases. Needs the server running at `BASE` (set `BASE=http://127.0.0.1:8000`). |
| `benchmark_latency.py` | (script) | Detection latency for one frame (warm and cold) and end-to-end upload latency. |
| `results/latency-results.json` | `benchmark_latency.py --runs 50 --upload-runs 5 --upload-url http://127.0.0.1:8000/upload` | Measured timings, with hardware and software versions. The upload clip is `samples/sample.mp4`. |
| `check_tracker_persist.py` | (script) | Compares track IDs across two videos in one process, with `persist=True` and `persist=False`. |
| `results/tracker-persist-check.txt` | `check_tracker_persist.py` with a 2-second clip made from `samples/sample.mp4` | Track IDs per frame for both settings. |
| `check_health_during_upload.sh` | (script) | Polls `/health` while a video uploads. |
| `results/health-during-upload-before-fix.txt` | `check_health_during_upload.sh` against the sync worker | `/health` waits for the upload to finish. |
| `results/health-during-upload.txt` | `check_health_during_upload.sh` against the gthread worker | `/health` answers while the upload runs. |
| `quickstart_check.sh` | (script) | Runs the steps in `../quickstart.md` from a fresh clone, with timings. |
| `results/quickstart-run.txt` | `quickstart_check.sh` | Timings and output from one run. |
| `sample-frame.jpg` | `ffmpeg -ss 2 -i <original 4K clip> -frames:v 1` | A 3840 × 2160 frame used for the detection benchmark and the wrong-type upload test. The original clip is not in the repository. |

## Notes

- **Redaction.** The local repository path is replaced with `/path/to/Object-Detection` in the `curl/` transcripts. Nothing else in the transcripts was changed.
- **Health-check clip.** The 20-second clip used for the health check was made by looping the sample four times: `ffmpeg -stream_loop 3 -i samples/sample.mp4 -c copy clip-20s.mp4`. It is not committed.
- **Environment.** Apple M3, 8 GB, macOS 27.0.1, Python 3.11.15, PyTorch 2.11.0, Ultralytics 8.4.49. The numbers do not apply to other machines.
- **Generated files.** Upload checks create MP4 and JSON files in `static/outputs/`. The app does not delete them, and Git ignores them.
