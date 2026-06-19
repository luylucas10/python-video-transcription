## 1. Documentation

- [x] 1.1 Update README prerequisites to list supported Windows and Linux environments.
- [x] 1.2 Add Linux uv installation and environment setup commands using POSIX shell syntax.
- [x] 1.3 Add Linux model download examples using forward-slash paths.
- [x] 1.4 Add Linux execution examples for directory scans, explicit video files, interactive mode, dry-run, and reprocess.
- [x] 1.5 Document Linux troubleshooting notes for ffmpeg, CUDA/CTranslate2, and CPU fallback.

## 2. Linux Launcher

- [x] 2.1 Add a POSIX shell launcher that calls `uv run python -m video_to_text` from the project root.
- [x] 2.2 Ensure the launcher forwards all user-provided CLI arguments unchanged.
- [x] 2.3 Document the launcher as the Linux equivalent of the existing `run.bat` convenience workflow.

## 3. Cross-Platform Behavior

- [x] 3.1 Review state, log, model cache, and Markdown output path handling for Windows-only assumptions.
- [x] 3.2 Add tests for POSIX-style input directories and explicit video paths.
- [x] 3.3 Add tests or assertions covering Linux model cache path behavior under `Path.home()/.cache/video-to-text/models`.
- [x] 3.4 Preserve existing Windows path and launcher documentation behavior.

## 4. Verification

- [x] 4.1 Run the existing pytest suite.
- [x] 4.2 Verify the Linux dry-run command documented in the README works when run in a Linux-capable environment.
- [x] 4.3 Verify OpenSpec status reports the change as ready for implementation.
