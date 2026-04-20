import re
import sys

file_path = sys.argv[1]

segments = []

pattern = re.compile(r"\[(.*?)\]\s*(.*)")

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if match:
            timestamp = match.group(1)
            text = match.group(2).strip()
            segments.append(text)

for i, seg in enumerate(segments):
    print(f"{i:04d}|{seg}")