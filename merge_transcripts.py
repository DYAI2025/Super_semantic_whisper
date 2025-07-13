#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge Audio Transcripts into an existing chat history.

This tool scans a directory for already transcribed audio messages and
inserts them at the correct position inside a chat text file based on the
recording timestamp.

The expected transcript file name is something like
```
YYYY-MM-DD_HH-MM-SS.txt
```
where the time corresponds roughly (±60s) to the time stamps inside the
chat.

Optionally a YAML/JSON settings file can be provided that contains a
`speaker_mapping` dictionary used to resolve speaker names from file
name fragments.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import yaml


def parse_transcript_timestamp(filename: str) -> Optional[datetime]:
    """Parse timestamp from transcript file name.

    Accepts formats like `YYYY-MM-DD_HH-MM-SS.txt` or without seconds.
    Returns ``None`` if no timestamp could be parsed.
    """
    match = re.search(r"(\d{4}-\d{2}-\d{2})[ _-](\d{2})-(\d{2})(?:-(\d{2}))?", filename)
    if not match:
        return None

    date_part, hour, minute, second = match.groups()
    second = second or "00"
    try:
        return datetime.strptime(f"{date_part} {hour}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def infer_speaker(filename: str, mapping: Dict[str, str]) -> str:
    """Infer speaker name from filename using optional mapping."""
    lower_name = filename.lower()
    for key, val in mapping.items():
        if key.lower() in lower_name:
            return val

    match = re.search(r"\d{4}-\d{2}-\d{2}_[\d-]+_(.+)\.txt", filename)
    if match:
        return match.group(1)

    match = re.search(r"_(\w+)\.txt$", filename)
    if match:
        return match.group(1)

    return "Unbekannt"


def parse_chat_line_time(line: str) -> Optional[datetime]:
    """Extract timestamp from chat line.

    Supports WhatsApp style lines like::

        [28.06.24, 14:23:15] Max: Nachricht

    Returns ``None`` if no timestamp could be parsed.
    """
    match = re.match(
        r"\[(\d{1,2}\.\d{1,2}\.(\d{2,4})), (\d{1,2}:\d{2})(?::(\d{2}))?\]",
        line,
    )
    if not match:
        return None

    day_month_year, year_part, time_part, seconds = match.group(1), match.group(2), match.group(3), match.group(4)
    seconds = seconds or "00"

    # Normalize year to 4 digits
    if len(year_part) == 2:
        year = int("20" + year_part)
    else:
        year = int(year_part)

    day, month = map(int, day_month_year.split(".")[:2])
    hour, minute = map(int, time_part.split(":"))
    second = int(seconds)

    return datetime(year, month, day, hour, minute, second)


def merge_transcripts(chat_txt_path: Path, transcript_dir: Path, output_path: Path, settings_path: Optional[Path] = None) -> None:
    """Merge transcripts into chat text file.

    Parameters
    ----------
    chat_txt_path : Path
        Path to chat text file.
    transcript_dir : Path
        Directory containing transcript ``.txt`` files.
    output_path : Path
        Destination file for merged output.
    settings_path : Path, optional
        YAML/JSON file with ``speaker_mapping`` dictionary.
    """
    speaker_mapping: Dict[str, str] = {}
    if settings_path and settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                speaker_mapping = data.get("speaker_mapping", {})

    transcripts: List[Dict[str, any]] = []
    for file in transcript_dir.glob("*.txt"):
        ts = parse_transcript_timestamp(file.name)
        if ts:
            transcripts.append({"path": file, "timestamp": ts})

    with open(chat_txt_path, "r", encoding="utf-8") as f:
        chat_lines = [line.rstrip("\n") for line in f]

    events: List[Dict[str, any]] = []
    for line in chat_lines:
        events.append({"type": "chat", "timestamp": parse_chat_line_time(line), "line": line})

    for tr in transcripts:
        events.append({"type": "transcript", **tr})

    events.sort(key=lambda e: (e.get("timestamp") or datetime.min, 0 if e["type"] == "chat" else 1))

    result_lines: List[str] = []
    for ev in events:
        if ev["type"] == "chat":
            result_lines.append(ev["line"])
        else:
            speaker = infer_speaker(ev["path"].name, speaker_mapping)
            result_lines.append(f"[Sprecher: {speaker} | Audio: {ev['timestamp'].strftime('%H:%M')}]")
            with open(ev["path"], "r", encoding="utf-8") as tf:
                text = tf.read().strip()
                if text:
                    result_lines.extend(text.splitlines())

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge audio transcripts into chat history")
    parser.add_argument("chat", type=Path, help="Chat text file")
    parser.add_argument("transcripts", type=Path, help="Directory with transcript txt files")
    parser.add_argument("output", type=Path, help="Output file path")
    parser.add_argument("--settings", type=Path, default=None, help="Optional YAML/JSON settings file")
    args = parser.parse_args()

    merge_transcripts(args.chat, args.transcripts, args.output, args.settings)
