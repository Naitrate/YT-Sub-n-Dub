#!/usr/bin/env bash

# Usage: ./yt_whisper_embed.sh "YOUTUBE_URL"

set -e

URL="$1"
API_URL="http://localhost:8000/health"

if [ -z "$URL" ]; then
  echo "Usage: $0 <youtube-url>"
  exit 1
fi

TEMP_DIR="./temp"
OUT_DIR="./output"

mkdir $TEMP_DIR
mkdir $OUT_DIR

echo "⬇️ Downloading video..."
yt-dlp -f "bv*+ba/best" -o "$TEMP_DIR/%(title)s.%(ext)s" "$URL"

# Get downloaded video filename
VIDEO="$(ls -t "$TEMP_DIR"/*.mp4 "$TEMP_DIR"/*.mkv "$TEMP_DIR"/*.webm 2>/dev/null | head -n 1)"

if [ -z "$VIDEO" ]; then
  echo "❌ Could not find downloaded video"
  exit 1
fi

BASENAME="$(printf '%s\n' "$VIDEO" | sed 's/\.[^.]*$//')"

echo "🎧 Extracting audio..."
ffmpeg -i "$VIDEO" -vn -acodec pcm_s16le -ar 16000 -ac 1 "${BASENAME}.wav"

echo "🧠 Transcribing with Whisper..."

# Path to your whisper model (adjust as needed)
MODEL=$(ls models/ggml-medium*.bin | head -n 1)

# Run whisper-cli
whisper-cli \
  -m "$MODEL" \
  -f "${BASENAME}.wav" \
  -of "${BASENAME}" \
  --max-len 50 \
  -osrt

# Fix segmentation issues with the subtitles.
python ./core/fix-srt-segmentation.py "${BASENAME}.srt"
rm "${BASENAME}.srt" && mv "${BASENAME}_fixed.srt" "${BASENAME}.srt"

echo "✅ Done! Subtitles generated."

echo "🗣️ Generating voice dubbing..."

echo "🔍 Checking if TTS server is running..."
if curl -s --max-time 2 "$API_URL" >/dev/null; then
  echo "✅ Server already running"
else
  echo "🚀 Server not detected, starting it..."

  # start server in background
  (
    cd ./core/qwen3-tts-webui

    direnv allow

    nix develop --command bash -c "
      uv sync &&
      uv run start_server.py
    "
  ) &
  SERVER_PID=$!

  echo "⏳ Waiting for server to be ready..."

  MAX_WAIT=30
  COUNT=0

  until curl -s --max-time 2 "$API_URL" >/dev/null; do
    sleep 1
    COUNT=$((COUNT+1))

    if [ "$COUNT" -ge "$MAX_WAIT" ]; then
      echo "❌ Server failed to start"
      exit 1
    fi
  done
fi

./core/generate-dub-voices.sh "${BASENAME}.srt"

echo "📺 Embedding subtitles into video..."
BASENAME="$(basename "$VIDEO" | sed 's/\.[^.]*$//')"
FINAL_OUT="$OUT_DIR/${BASENAME}_av1.mp4"

# Create our dub track.
./generate-dub-track.sh "$TEMP_DIR/${BASENAME}.json" "$TEMP_DIR/dub/${BASENAME}" "$TEMP_DIR/${BASENAME}.wav" "$TEMP_DIR/${BASENAME}_dub.wav"

# Finally encode the video with both the subtitles and our dub track.
ffmpeg -i "$VIDEO" \
  -i "$TEMP_DIR/${BASENAME}_dub.wav" \
  -i "$TEMP_DIR/${BASENAME}.srt" \
  -map 0:v:0 \
  -map 0:a:0 \
  -map 1:a:0 \
  -map 2:s:0 \
  -c:v av1_nvenc \
  -preset p5 \
  -cq 30 \
  -b:v 0 \
  -c:a libopus \
  -c:s mov_text \
  -metadata:s:a:1 language=eng \
  -metadata:s:a:2 language=kor \
  "$FINAL_OUT"

#ffmpeg -i "$VIDEO" \
  #-i "$TEMP_DIR/${BASENAME}.srt" \
  #-c:v av1_nvenc \
  #-preset p5 \
  #-cq 30 \
  #-b:v 0 \
  #-c:a copy \
  #-c:s mov_text \
  #"$FINAL_OUT"

echo "✅ Done!"
echo "Output: $FINAL_OUT"
