import re
import argparse
from pathlib import Path

def parse_time(t):
    t = t.replace(",", ".")
    h, m, s = t.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"

def clean_text(text):
    text = text.strip()
    if text in {".", "..."}:
        return ""
    if text.startswith("[") and text.endswith("]"):
        return ""
    return text

def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

def split_with_timestamps(text, start, end, max_chars=200):
    sentences = split_sentences(text)

    total_duration = end - start
    total_chars = sum(len(s) for s in sentences if s)

    chunks = []
    current = []
    current_chars = 0

    for s in sentences:
        if not s:
            continue

        if current_chars + len(s) <= max_chars:
            current.append(s)
            current_chars += len(s)
        else:
            chunks.append((current, current_chars))
            current = [s]
            current_chars = len(s)

    if current:
        chunks.append((current, current_chars))

    # assign timestamps proportionally
    results = []
    cursor = start

    for chunk_sentences, char_count in chunks:
        duration = (char_count / total_chars) * total_duration if total_chars > 0 else 0
        chunk_text = " ".join(chunk_sentences).strip()

        results.append({
            "start": cursor,
            "end": cursor + duration,
            "text": chunk_text
        })

        cursor += duration

    return results


def process_srt(input_path, output_path, gap_threshold, max_chars):
    time_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})"
    )

    segments = []
    current_segment = []
    prev_end = None

    with open(input_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.isdigit():
            i += 1
            continue

        match = time_pattern.match(line)
        if match:
            start, end = match.groups()
            start_t = parse_time(start)
            end_t = parse_time(end)

            i += 1
            text_lines = []

            while i < len(lines) and lines[i].strip() != "":
                text_lines.append(lines[i].strip())
                i += 1

            text = clean_text(" ".join(text_lines))

            if text:
                if prev_end is not None and (start_t - prev_end) > gap_threshold:
                    segments.append(current_segment)
                    current_segment = []

                current_segment.append({
                    "start": start_t,
                    "end": end_t,
                    "text": text
                })

                prev_end = end_t

        i += 1

    if current_segment:
        segments.append(current_segment)

    # process + split
    final_chunks = []

    for seg in segments:
        seg_text = " ".join(x["text"] for x in seg)
        seg_start = seg[0]["start"]
        seg_end = seg[-1]["end"]

        split_chunks = split_with_timestamps(seg_text, seg_start, seg_end, max_chars)
        final_chunks.extend(split_chunks)

    # write output
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in final_chunks:
            f.write(
                f"[{format_time(chunk['start'])} --> {format_time(chunk['end'])}] {chunk['text']}\n\n"
            )

    print(f"Done! {len(final_chunks)} chunks written to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input .srt file")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("-g", "--gap", type=float, default=0.8)
    parser.add_argument("-c", "--chars", type=int, default=200)

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".txt")

    process_srt(input_path, output_path, args.gap, args.chars)
