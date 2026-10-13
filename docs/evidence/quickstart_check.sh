#!/usr/bin/env bash
# Runs the commands in docs/quickstart.md from a fresh clone and times each step.
# Downloads from GitHub and PyPI, so it needs network access.
#
# Usage:
#   WORK=/path/to/empty/dir bash docs/evidence/quickstart_check.sh
#
# PIP_NO_CACHE_DIR=1 makes pip download every wheel, so the install time is
# a cold-download figure rather than a cache hit.

set -u
WORK="${WORK:?Set WORK to an empty directory}"
PORT=8000
PY="${PY:-python3.11}"

if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT is busy. Stop the other process or change PORT." >&2
  exit 1
fi

mkdir -p "$WORK" && cd "$WORK" || exit 1
step() { echo; echo "== $1 ($(date +%T))"; }
t0=$SECONDS

step "1. Clone the repository"
git clone -q "${REPO_URL:-https://github.com/Shashwat-19/Object-Detection.git}"
cd Object-Detection || exit 1
ls -l samples/sample.mp4
echo "elapsed: $((SECONDS - t0))s"

step "2. Create and activate a virtual environment"
$PY -m venv .venv
source .venv/bin/activate
python --version

step "3. Install the dependencies (macOS form)"
t1=$SECONDS
sed -e '/extra-index-url/d' -e 's/+cpu//' requirements.txt > "${TMPDIR:-/tmp}/requirements-macos.txt"
PIP_NO_CACHE_DIR=1 pip install -q -r "${TMPDIR:-/tmp}/requirements-macos.txt"
echo "pip exit=$?  install time: $((SECONDS - t1))s"
du -sh .venv

step "4. Start the server"
export PORT
gunicorn app:app --bind 127.0.0.1:$PORT --timeout 600 --workers 1 --worker-class gthread --threads 4 > "$WORK/server.log" 2>&1 &
SERVER_PID=$!
for _ in $(seq 1 60); do
  curl -s -o /dev/null http://127.0.0.1:$PORT/health && break
  sleep 1
done
curl -s -i http://127.0.0.1:$PORT/health | tr -d '\r' | head -1

step "5. Send a detection request"
t2=$SECONDS
LOCATION=$(curl -s -o /dev/null -D - -F video=@samples/sample.mp4 http://127.0.0.1:$PORT/upload | tr -d '\r' | awk '/^Location:/ {print $2}')
echo "$LOCATION"
echo "upload time: $((SECONDS - t2))s"

step "6. Download the tracked video"
FILE="${LOCATION#*file=}"
curl -s -o tracked.mp4 -w 'HTTP %{http_code}, %{size_download} bytes\n' "http://127.0.0.1:$PORT/download/?filename=$FILE"
ffprobe -v error -show_entries stream=width,height -show_entries format=duration -of default=nw=1 tracked.mp4 2>/dev/null \
  || echo "ffprobe not installed; skipped resolution and duration check"

echo
echo "total elapsed: $((SECONDS - t0))s"
kill "$SERVER_PID" 2>/dev/null
wait "$SERVER_PID" 2>/dev/null
