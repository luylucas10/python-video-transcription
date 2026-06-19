## Context

The application is a Python CLI using `pathlib` for most filesystem operations and `uv` for environment management. Current user-facing setup is Windows-first: the README lists Windows as a prerequisite, examples use PowerShell and backslash paths, and double-click execution depends on `run.bat`. The implementation stores state under the project `data` directory, logs under `logs`, and model cache under `Path.home() / ".cache" / "video-to-text" / "models"`, which is suitable for Linux if tests cover it.

## Goals / Non-Goals

**Goals:**

- Make Linux a supported execution environment for the CLI.
- Provide Linux setup and usage documentation with POSIX shell examples.
- Provide a Linux-friendly launcher path that preserves the same default model behavior as `run.bat`.
- Add tests that protect cross-platform path handling for state, logs, output files, and model cache.
- Preserve existing Windows usage and behavior.

**Non-Goals:**

- Packaging a system service, desktop shortcut, container image, or distribution package.
- Guaranteeing CUDA availability on every Linux host.
- Changing transcription quality defaults or faster-whisper model behavior.
- Moving existing state or logs to platform-specific user data directories.

## Decisions

1. Keep the Python CLI as the primary supported interface.

   Rationale: `python -m video_to_text` and the installed `video-to-text` entry point are already cross-platform. Linux support should reinforce these paths rather than introduce a second execution model.

   Alternative considered: make a Linux shell script the primary interface. This would make script behavior more important than the package entry point and add duplicated argument parsing responsibility.

2. Add a minimal POSIX shell launcher for parity with `run.bat`.

   Rationale: users who rely on a simple project-local launcher should have an equivalent on Linux. The launcher should call `uv run python -m video_to_text` and pass through all arguments.

   Alternative considered: remove launchers and document only `uv run`. That would be simpler but leaves Windows and Linux with noticeably different convenience workflows.

3. Treat Linux CPU fallback as supported and Linux CUDA as environment-dependent.

   Rationale: the application already attempts CUDA/float16 first and falls back to CPU/int8 on early failure. Linux documentation should explain NVIDIA driver/CUDA requirements without making GPU mandatory.

   Alternative considered: add explicit `--device` and `--compute-type` flags in this change or a future Linux-specific follow-up. That would expand the behavioral surface beyond platform support, so this change will not expose those flags.

4. Preserve project-local state and logs.

   Rationale: the app currently writes `data/processed_videos.json` and `logs/last-run.log` relative to the project root. Keeping this behavior avoids migration work and keeps Windows behavior unchanged.

   Alternative considered: move Linux state/logs to XDG directories. That would be more idiomatic on Linux but would create migration and discoverability complexity that is not required for basic platform support.

## Risks / Trade-offs

- Linux hosts may lack `ffmpeg` or compatible CTranslate2/CUDA libraries -> document prerequisites and verify the CLI can still fall back to CPU when GPU initialization fails.
- Shell launchers can drift from the Python CLI -> keep the launcher as a thin pass-through wrapper with no duplicated option logic.
- Tests run on Windows in this repository may not execute on a real Linux kernel -> add POSIX-path/unit-level coverage and document any manual Linux smoke test needed.
- Existing README text appears with encoding artifacts -> avoid broad copy edits during implementation and touch only the Linux support sections needed for this change.

## Migration Plan

1. Add the Linux launcher and documentation.
2. Add or adjust tests for POSIX paths, model cache, and launcher expectations.
3. Run the existing test suite.
4. Perform a Linux dry-run smoke test where available: `uv run python -m video_to_text -d /path/to/videos --dry-run`.

Rollback is straightforward: remove the Linux documentation and launcher, and revert the added tests. No persisted user data migration is required.
