## Why

The current application is optimized for scanning a hardcoded `E:\obs` directory, but users need to choose either a directory or one or more specific video files at runtime. The CLI should support `-d path\to\dir`, repeatable `-v path\to\video.mp4`, and an interactive directory prompt when neither input option is provided, while still writing transcripts beside each source video and working on machines where CUDA is unavailable or fails at runtime.

## What Changes

- Add a repeatable `-v`/`--video` CLI option for selecting one or more explicit video files.
- Add a `-d`/`--dir` CLI option for selecting a directory to scan.
- Remove the hardcoded `E:\obs` default directory.
- Prompt the user for a directory only when neither `-d`/`--dir` nor `-v`/`--video` is provided.
- Reject runs that combine `-d`/`--dir` with `-v`/`--video`.
- Transcribe selected inputs and write each `.md` output next to the corresponding source video.
- Try the configured GPU transcription settings first, then automatically fall back to CPU settings when GPU model loading or transcription fails before a video succeeds.
- Preserve existing state, reprocess, dry-run, stability, Markdown, and summary behavior for explicit videos where applicable.
- Update `README.md` so setup and usage examples describe directory input, repeatable video input, no-input prompting, mutual exclusion, output location, and GPU-to-CPU fallback.

## Capabilities

### New Capabilities

- `video-input-selection`: Selecting videos through a directory argument, repeatable explicit video arguments, or an interactive directory prompt.
- `transcription-device-fallback`: Selecting GPU first and falling back to CPU when GPU execution cannot be used.

### Modified Capabilities

- None.

## Impact

- Affects CLI argument parsing in `src/video_to_text/app.py`.
- Affects run orchestration and transcriber construction in `src/video_to_text/app.py` and possibly `src/video_to_text/transcriber.py`.
- Requires focused tests for CLI parsing, directory prompting, mutually exclusive inputs, video iteration, output placement, state handling, and GPU-to-CPU fallback behavior.
- `README.md` must be updated with the new input-selection contract and fallback behavior.
