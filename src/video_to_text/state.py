from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATE_VERSION = 1


def load_state(state_file: Path) -> dict[str, Any]:
    if not state_file.exists():
        return {"version": STATE_VERSION, "videos": {}}

    raw_text = state_file.read_text(encoding="utf-8")
    if not raw_text.strip():
        return {"version": STATE_VERSION, "videos": {}}

    data = json.loads(raw_text)
    if not isinstance(data, dict):
        return {"version": STATE_VERSION, "videos": {}}

    # Reset state when the file was written by an incompatible version to avoid corrupt reads
    if data.get("version") != STATE_VERSION:
        return {"version": STATE_VERSION, "videos": {}}

    videos = data.get("videos")
    if not isinstance(videos, dict):
        videos = {}

    return {"version": STATE_VERSION, "videos": videos}


def save_state(state_file: Path, state: dict[str, Any]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = state_file.with_suffix(f"{state_file.suffix}.tmp")
    temporary_file.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary_file.replace(state_file)

