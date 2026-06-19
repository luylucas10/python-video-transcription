#!/bin/bash

# Linux/macOS launcher for video-to-text
# Equivalent to run.bat on Windows
# Calls: uv run python -m video_to_text [args...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

exec uv run python -m video_to_text "$@"
