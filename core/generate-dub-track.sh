#!/usr/bin/env bash
set -e

ARGS=("$@")

JSON_FILE="${ARGS[0]}"
AUDIO_DIR="${ARGS[1]}"
ORIGINAL_AUDIO="${ARGS[2]}"
OUT_FILE="${ARGS[3]}"

JSON_FILE="$(realpath "$JSON_FILE")"
AUDIO_DIR="$(realpath "$AUDIO_DIR")"
ORIGINAL_AUDIO="$(realpath "$ORIGINAL_AUDIO")"
OUT_FILE="$(realpath "$OUT_FILE")"

echo "JSON_FILE=[$JSON_FILE]"
echo "AUDIO_DIR=[$AUDIO_DIR]"
echo "ORIGINAL_AUDIO=[$ORIGINAL_AUDIO]"
echo "OUT_FILE=[$OUT_FILE]"

FILTER=""
INPUTS=()
COUNT=0

# IMPORTANT: safe JSON iteration (no read loop issues)
while IFS= read -r item; do
    IDX=$(jq -r '.index' <<< "$item")

    START=$(jq -r '.start' <<< "$item")
    END=$(jq -r '.end' <<< "$item")
    SUB_DUR=$(echo "$END - $START" | bc -l)

    AUDIO="${AUDIO_DIR}/${IDX}.wav"

    if [ ! -f "$AUDIO" ]; then
        continue
    fi

    AUDIO_DUR=$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "$AUDIO")

    SPEED=$(echo "$AUDIO_DUR / $SUB_DUR" | bc -l)

    if (( $(echo "$SPEED > 2.0" | bc -l) )); then SPEED=2.0; fi
    if (( $(echo "$SPEED < 0.5" | bc -l) )); then SPEED=0.5; fi

    INPUTS+=(-i "$AUDIO")

    FILTER+="[$COUNT]atempo=${SPEED},adelay=$(echo "$START * 1000" | bc -l)|$(echo "$START * 1000" | bc -l)[a$COUNT];"

    COUNT=$((COUNT+1))

done < <(jq -c 'sort_by(.index)[]' "$JSON_FILE")

# safety check
if [ "$COUNT" -eq 0 ]; then
    echo "ERROR: No audio files found"
    exit 1
fi

# build mix inputs
MIX=""
for ((i=0;i<COUNT;i++)); do
    MIX+="[a$i]"
done

#FILTER+="${MIX}amix=inputs=${COUNT}:normalize=0[aout]"

ORIGINAL_DURATION=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$ORIGINAL_AUDIO")

FILTER+="${MIX}amix=inputs=${COUNT}:normalize=0[aout];[aout]atrim=0:${ORIGINAL_DURATION}[aout_final]"

ffmpeg -y "${INPUTS[@]}" -filter_complex "$FILTER" -map "[aout_final]" "$OUT_FILE"

# IMPORTANT FIX: array-safe ffmpeg call
#ffmpeg -y "${INPUTS[@]}" -filter_complex "$FILTER" -map "[aout]" "$OUT_FILE"