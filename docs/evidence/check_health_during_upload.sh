#!/usr/bin/env bash
# Start one upload, then request /health every 0.5 s while it runs.
# Shows whether the single gunicorn worker can answer other requests during
# inference. Times are Unix epoch seconds with nanoseconds (macOS date +%s.%N).
#
# Usage (server already running):
#   BASE=http://127.0.0.1:5055 bash docs/evidence/check_health_during_upload.sh

set -u
BASE="${BASE:-http://127.0.0.1:5055}"
HERE="$(cd "$(dirname "$0")" && pwd)"
VIDEO="${VIDEO:-$HERE/../../samples/sample.mp4}"
OUT="${OUT:-$HERE/results/health-during-upload.txt}"
mkdir -p "$HERE/results"

TMP="$(mktemp -d)"

(
  start=$(date +%s.%N)
  code=$(curl -s -o /dev/null -w '%{http_code}' -F "video=@$VIDEO" "$BASE/upload")
  end=$(date +%s.%N)
  echo "UPLOAD http_code=$code start=$start end=$end"
) > "$TMP/upload.txt" 2>&1 &

sleep 1.5
for i in $(seq 1 12); do
  start=$(date +%s.%N)
  code=$(curl -s -o /dev/null -m 30 -w '%{http_code}' "$BASE/health")
  end=$(date +%s.%N)
  echo "HEALTH i=$i http_code=$code start=$start end=$end"
  sleep 0.5
done > "$TMP/health.txt" 2>&1

wait
{
  echo "# curl -F video=@$VIDEO $BASE/upload  (in background)"
  echo "# curl $BASE/health every ~0.5 s while the upload runs"
  cat "$TMP/upload.txt"
  cat "$TMP/health.txt"
} > "$OUT"
rm -rf "$TMP"
cat "$OUT"
