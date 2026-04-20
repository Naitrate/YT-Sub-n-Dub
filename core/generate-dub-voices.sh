#!/usr/bin/env bash
set -e

FILE="$1"

BASENAME="$(basename "$FILE")"
NAME="${BASENAME%.*}"

VOICE_FILE="${FILE%.*}.wav"

OUT_DIR="./temp/dub/${NAME}"
mkdir -p "$OUT_DIR"

JSON_FILE="${FILE%.*}.json"

echo "Input text: $FILE"
echo "Input audio: $VOICE_FILE"
echo "JSON file: $JSON_FILE"
echo "Output dir: $OUT_DIR"

python3 srt-to-json.py "${FILE%.*}.srt" "$JSON_FILE"

jq -c '.[]' "$JSON_FILE" | while read -r item
do
    IDX=$(echo "$item" | jq -r '.index')
    TEXT=$(echo "$item" | jq -r '.text')

    echo "Processing segment $IDX"

    TEXT="$(echo "$TEXT" | tr '\n' ' ' | sed 's/  */ /g')"

    RESP=$(curl -s -X POST "http://localhost:8000/clone-with-upload" \
      -F "file=@${VOICE_FILE};type=audio/wav" \
      --form-string "text=$TEXT" \
      -F "language=auto")

    TASK_ID=$(echo "$RESP" | jq -r '.task_id')

    while true; do
      STATUS=$(curl -s "http://localhost:8000/tasks/$TASK_ID" | jq -r '.status')
      echo "Status: $STATUS"
      [ "$STATUS" = "completed" ] && break
      sleep 2
    done

    curl "http://localhost:8000/tasks/$TASK_ID/audio" \
      --output "${OUT_DIR}/${IDX}.wav"
done

echo "Done → ${OUT_DIR}/"