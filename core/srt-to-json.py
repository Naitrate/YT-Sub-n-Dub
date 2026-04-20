#!/usr/bin/env python3

import re
import json
import sys
from pathlib import Path


TIME_PATTERN = re.compile(
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})"
)


def parse_time(t: str) -> float:
    t = t.replace(",", ".")
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def read_srt(path: str):
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    subs = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # skip index lines
        if line.isdigit():
            i += 1
            continue

        match = TIME_PATTERN.match(line)
        if not match:
            i += 1
            continue

        start_str, end_str = match.groups()
        start = parse_time(start_str)
        end = parse_time(end_str)

        i += 1
        text_lines = []

        while i < len(lines) and lines[i].strip() != "":
            text_lines.append(lines[i].strip())
            i += 1

        text = " ".join(text_lines).strip()

        subs.append({
            "index": len(subs),
            "start": start,
            "end": end,
            "duration": round(end - start, 3),
            "start_time": start_str,
            "end_time": end_str,
            "text": text
        })

        i += 1

    return subs


def main():
    if len(sys.argv) < 2:
        print("Usage: srt_to_json.py input.srt [output.json]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else str(
        Path(input_path).with_suffix(".json")
    )

    data = read_srt(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote {len(data)} subtitles → {output_path}")


if __name__ == "__main__":
    main()