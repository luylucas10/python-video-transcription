## 1. CLI Inputs

- [x] 1.1 Add input-selection settings for optional `watch_directory: Path | None` and `video_paths: tuple[Path, ...]`.
- [x] 1.2 Add mutually exclusive `-d`/`--dir` and repeatable `-v`/`--video` parsing with `argparse`.
- [x] 1.3 Remove the hardcoded `E:\obs` default directory from runtime input selection.
- [x] 1.4 Implement a directory-only prompt when neither `-d`/`--dir` nor `-v`/`--video` is provided.
- [x] 1.5 Implement directory validation and explicit video validation before model loading.
- [x] 1.6 Add an eligible-video iterator that returns explicit videos in argument order or root directory videos from the selected or prompted directory.

## 2. Transcription Flow

- [x] 2.1 Reuse existing output, fingerprint, state, stability, dry-run, and reprocess handling for selected video inputs.
- [x] 2.2 Ensure selected video transcripts are written beside each source video with the same base filename and `.md` suffix.
- [x] 2.3 Preserve current run summary counts and failed-file behavior for both explicit and scanned modes.

## 3. Device Fallback

- [x] 3.1 Add transcriber construction support for primary GPU settings and CPU fallback settings.
- [x] 3.2 Retry the eligible-video run with CPU fallback when GPU model load or first transcription fails before any video succeeds.
- [x] 3.3 Prevent device switching after one or more videos have already succeeded in the current run.
- [x] 3.4 Log the GPU failure and CPU fallback settings when fallback is used.

## 4. Tests

- [x] 4.1 Add tests for `-d`/`--dir`, repeatable `-v`/`--video`, no-input directory prompt, and mixed-input parser rejection.
- [x] 4.2 Add tests for directory and explicit video validation failures before transcriber loading.
- [x] 4.3 Add tests that selected videos write Markdown beside their source and use existing state skip/reprocess behavior.
- [x] 4.4 Add tests for GPU success, GPU-load fallback, first-video fallback, and no fallback after a successful GPU transcription.

## 5. Documentation

- [x] 5.1 Update README usage examples to show `-d path\to\videos` and `-v path\to\video.mp4 -v path\to\another.mp4`.
- [x] 5.2 Document the no-input directory prompt and that `-d`/`--dir` cannot be combined with `-v`/`--video`.
- [x] 5.3 Document that output Markdown stays beside each selected video.
- [x] 5.4 Document GPU-first execution and automatic CPU fallback behavior.
