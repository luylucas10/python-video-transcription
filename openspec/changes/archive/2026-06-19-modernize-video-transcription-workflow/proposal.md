## Why

The project already transcribes videos from `E:\obs` into Markdown with `faster-whisper`, but its setup still documents manual pip/venv usage and a PyInstaller executable path that no longer matches the desired workflow. This change keeps the current `faster-whisper` implementation, makes the project reproducible as a uv-managed Python application, documents which Hugging Face model to download, and keeps processing state explicit so completed videos are not transcribed again.

## What Changes

- Replace the executable build workflow with Python-only execution through uv.
- Convert project setup to uv conventions, including lockfile-managed dependencies and a recreated `.venv`.
- Document the full workflow in `README.md`: prerequisites, uv installation/setup, model download with `hf download`, model location, execution, state, logs, and troubleshooting.
- Use a compatible Python version for the implementation and document that version as the project runtime.
- Keep the current `faster-whisper` transcription implementation and document `Systran/faster-whisper-large-v3` as the default Hugging Face model to download for Portuguese/multilingual accuracy.
- Document `mobiuslabsgmbh/faster-whisper-large-v3-turbo` / `turbo` as an optional speed-oriented model.
- Preserve directory processing behavior for videos in `E:\obs`, including remembering processed videos and writing Markdown outputs next to the source video.
- Remove PyInstaller build artifacts, build scripts, and documentation from the supported workflow.

## Capabilities

### New Capabilities

- `uv-python-workflow`: Defines the uv-managed Python project, virtual environment recreation, supported Python version, dependency groups, and Python-only run commands.
- `faster-whisper-model-management`: Defines how the project downloads and references Hugging Face-hosted CTranslate2 faster-whisper model files with the `hf` CLI.
- `video-directory-transcription`: Defines the expected behavior for scanning `E:\obs`, skipping already processed videos, transcribing new videos, and writing Markdown outputs.
- `project-documentation`: Defines the README coverage required for setup, operation, state, logs, model download, and removed executable build workflow.

### Modified Capabilities

None.

## Impact

- Affected code: `pyproject.toml`, lockfile/environment files, source modules under `src/video_to_text`, tests under `tests`, and helper scripts such as `run.bat` or build scripts.
- Affected documentation: `README.md` becomes the complete operator guide and removes PyInstaller/executable build instructions.
- Dependency impact: remove PyInstaller from the supported dev workflow, add uv-compatible project metadata, keep `faster-whisper`, and include Hugging Face Hub CLI support for model downloads.
- Operational impact: users recreate `.venv` with uv, download a local model before running, and run the application with Python/uv commands instead of a generated `.exe`.
