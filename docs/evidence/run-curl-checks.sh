#!/usr/bin/env bash
# Calls every HTTP route in the app and saves each request and raw response
# to docs/evidence/curl/. Used to verify docs/api-reference.md.
#
# Usage:
#   WORK=/path/to/empty/scratch/dir bash docs/evidence/run-curl-checks.sh
#   BASE=http://127.0.0.1:5000 WORK=... bash docs/evidence/run-curl-checks.sh
#
# The server must already be running. Generated fixtures go in $WORK and are
# never written into the repository.

set -u

BASE="${BASE:-http://127.0.0.1:5055}"
WORK="${WORK:?Set WORK to an empty scratch directory}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
EVID="$HERE/curl"

mkdir -p "$EVID" "$WORK"

# ---- Fixtures (generated, not committed) -----------------------------------
ffmpeg -v error -y -i "$REPO/samples/sample.mp4" -t 2 -vf scale=640:-2 -an "$WORK/short.mp4"
printf 'this is plain text, not a video\n' > "$WORK/fake.mp4"
head -c 104857601 /dev/zero > "$WORK/too-large.mp4"   # 100 MiB + 1 byte
SAMPLE_FRAME="$HERE/sample-frame.jpg"

# ---- Helpers ----------------------------------------------------------------
# record NAME COMMAND_TEXT HEADER_FILE BODY_FILE
# Writes the command, the status line, the response headers and the body.
record() {
  local name="$1" cmd="$2" hdr="$3" body="$4" status="$5"
  {
    echo "\$ $cmd"
    echo
    echo "# status: $status"
    echo
    echo "# response headers"
    tr -d '\r' < "$hdr"
    if [ -n "$body" ] && [ -s "$body" ]; then
      echo
      echo "# response body"
      cat "$body"
      echo
    fi
  } > "$EVID/$name.txt"
  echo "[$name] $status"
}

# ---- Routes that do not process a video ------------------------------------
H="$WORK/h.txt"; B="$WORK/b.txt"
cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' $BASE/"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE/")
record 01-get-index "$cmd" "$H" "$B" "$s"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' $BASE/health"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE/health")
record 02-get-health "$cmd" "$H" "$B" "$s"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' $BASE/debug"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE/debug")
record 03-get-debug "$cmd" "$H" "$B" "$s"

# ---- Successful upload (real sample video from the repository) -------------
H="$WORK/h-upload.txt"; B="$WORK/b-upload.txt"
cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -F video=@samples/sample.mp4 $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -F "video=@$REPO/samples/sample.mp4" "$BASE/upload")
record 04-post-upload-valid "$cmd" "$H" "$B" "$s"

LOC=$(tr -d '\r' < "$H" | awk 'tolower($1)=="location:" {print $2}')
RESULT_FILE=$(printf '%s' "$LOC" | sed -n 's/.*file=//p')
echo "redirect location: $LOC"
echo "result file: $RESULT_FILE"

if [ -n "$LOC" ]; then
  H="$WORK/h-result.txt"; B="$WORK/b-result.txt"
  cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' '$BASE$LOC'"
  s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE$LOC")
  record 05-get-result "$cmd" "$H" "$B" "$s"

  H="$WORK/h-dl.txt"; B="$WORK/dl.mp4"
  cmd="curl -s -D h.txt -o out.mp4 -w '%{http_code} %{time_total}s' '$BASE/download/?filename=$RESULT_FILE'"
  s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE/download/?filename=$RESULT_FILE")
  {
    echo "$cmd"
    echo; echo "# status: $s"; echo
    echo "# response headers"; tr -d '\r' < "$H"
    echo; echo "# body: binary MP4, $(wc -c < "$B" | tr -d ' ') bytes (not saved)"
  } > "$EVID/06-get-download.txt"
  echo "[06-get-download] $s"

  H="$WORK/h-dl2.txt"; B="$WORK/dl2.mp4"
  cmd="curl -s -D h.txt -o out.mp4 -w '%{http_code} %{time_total}s' '$BASE/download/?file=$RESULT_FILE'"
  s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE/download/?file=$RESULT_FILE")
  {
    echo "$cmd"
    echo; echo "# status: $s"; echo
    echo "# response headers"; tr -d '\r' < "$H"
    echo; echo "# body: binary MP4, $(wc -c < "$B" | tr -d ' ') bytes (not saved)"
  } > "$EVID/07-get-download-file-alias.txt"
  echo "[07-get-download-file-alias] $s"
fi

# ---- Upload error cases -----------------------------------------------------
H="$WORK/h.txt"; B="$WORK/b.txt"
cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -F video=@image.jpg $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -F "video=@$SAMPLE_FRAME;type=image/jpeg" "$BASE/upload")
record 08-post-upload-wrong-type-html "$cmd" "$H" "$B" "$s"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -H 'X-Requested-With: XMLHttpRequest' -F video=@image.jpg $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -H 'X-Requested-With: XMLHttpRequest' -F "video=@$SAMPLE_FRAME;type=image/jpeg" "$BASE/upload")
record 09-post-upload-wrong-type-json "$cmd" "$H" "$B" "$s"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -F note=hello $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -F "note=hello" "$BASE/upload")
record 10-post-upload-missing-file "$cmd" "$H" "$B" "$s"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -F video=@fake.mp4 $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -F "video=@$WORK/fake.mp4" "$BASE/upload")
record 11-post-upload-fake-mp4 "$cmd" "$H" "$B" "$s"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -H 'X-Requested-With: XMLHttpRequest' -F video=@too-large.mp4 $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -H 'X-Requested-With: XMLHttpRequest' -F "video=@$WORK/too-large.mp4;type=video/mp4" "$BASE/upload")
record 12-post-upload-too-large "$cmd" "$H" "$B" "$s"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -F 'video=@short.mp4;filename=../../evil.mp4' $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -F "video=@$WORK/short.mp4;filename=../../evil.mp4;type=video/mp4" "$BASE/upload")
record 13-post-upload-path-traversal-name "$cmd" "$H" "$B" "$s"
echo "traversal location: $(tr -d '\r' < "$H" | awk 'tolower($1)=="location:" {print $2}')"

cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' -F 'video=@short.mp4;filename=%%%.mp4' $BASE/upload"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -F "video=@$WORK/short.mp4;filename=%%%.mp4;type=video/mp4" "$BASE/upload")
record 14-post-upload-unsanitizable-name "$cmd" "$H" "$B" "$s"
echo "unsanitizable-name location: $(tr -d '\r' < "$H" | awk 'tolower($1)=="location:" {print $2}')"

# ---- Not-found and method cases --------------------------------------------
H="$WORK/h.txt"; B="$WORK/b.txt"
for spec in \
  "15-get-result-no-file|$BASE/result/" \
  "16-get-result-missing-file|$BASE/result/?file=missing.mp4" \
  "17-get-download-no-param|$BASE/download/" \
  "18-get-download-missing-file|$BASE/download/?filename=missing.mp4" \
  "19-get-upload-method-not-allowed|$BASE/upload" \
  "20-get-unknown-route|$BASE/does-not-exist"; do
  name="${spec%%|*}"; url="${spec#*|}"
  cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' '$url'"
  s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$url")
  record "$name" "$cmd" "$H" "$B" "$s"
done

# ---- Path and slash edge cases ----------------------------------------------
H="$WORK/h.txt"; B="$WORK/b.txt"
for spec in \
  "21-get-result-no-trailing-slash|$BASE/result?file=missing.mp4" \
  "22-get-download-no-trailing-slash|$BASE/download?filename=missing.mp4" \
  "23-get-download-path-traversal|$BASE/download/?filename=../../app.py" \
  "24-get-result-path-traversal|$BASE/result/?file=../../app.py"; do
  name="${spec%%|*}"; url="${spec#*|}"
  cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' '$url'"
  s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$url")
  record "$name" "$cmd" "$H" "$B" "$s"
done

# ---- Static files (Flask serves static/ at /static/<path>) -----------------
if [ -n "${RESULT_FILE:-}" ]; then
  H="$WORK/h-static.txt"; B="$WORK/b-static.txt"
  cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' '$BASE/static/outputs/$RESULT_FILE' -r 0-15"
  s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' -r 0-15 "$BASE/static/outputs/$RESULT_FILE")
  {
    echo "$cmd"; echo; echo "# status: $s"; echo
    echo "# response headers"; tr -d '\r' < "$H"
    echo; echo "# body: first 16 bytes of binary MP4 (not saved)"
  } > "$EVID/25-get-static-output-video.txt"
  echo "[25-get-static-output-video] $s"
fi

if [ -n "${RESULT_FILE:-}" ]; then
  H="$WORK/h-static-full.txt"; B="$WORK/static-full.mp4"
  cmd="curl -s -D h.txt -o static.mp4 -w '%{http_code} %{time_total}s' '$BASE/static/outputs/$RESULT_FILE'"
  s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE/static/outputs/$RESULT_FILE")
  {
    echo "$cmd"; echo; echo "# status: $s"; echo
    echo "# response headers"; tr -d '\r' < "$H"
    echo; echo "# body: full binary MP4, $(wc -c < "$B" | tr -d ' ') bytes (not saved)"
  } > "$EVID/25b-get-static-output-video-full.txt"
  echo "[25b-get-static-output-video-full] $s"
fi

H="$WORK/h.txt"; B="$WORK/b.txt"
cmd="curl -s -D h.txt -o b.txt -w '%{http_code} %{time_total}s' '$BASE/static/outputs/does-not-exist.mp4'"
s=$(curl -s -D "$H" -o "$B" -w '%{http_code} %{time_total}s' "$BASE/static/outputs/does-not-exist.mp4")
record 26-get-static-missing "$cmd" "$H" "$B" "$s"

# ---- Redact the local repository path from the saved transcripts ------------
# Only the prefix is replaced, so every other byte of each response is unchanged.
for f in "$EVID"/*.txt; do
  sed "s#$REPO#/path/to/Object-Detection#g" "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done

echo "done"
