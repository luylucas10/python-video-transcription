## 1. Project Environment

- [x] 1.1 Update `pyproject.toml` for the uv-managed workflow and remove PyInstaller from development dependencies.
- [x] 1.2 Add or update `.python-version` to pin the selected compatible Python version.
- [x] 1.3 Recreate `.venv` with uv and generate or refresh `uv.lock`.

## 2. Faster-Whisper Model Workflow

- [x] 2.1 Keep `faster-whisper` as the transcription backend and preserve the existing `large-v3` default.
- [x] 2.2 Verify the `--model` argument accepts the default shorthand, full Hugging Face model IDs, and local model directories.
- [x] 2.3 Add or update tests for local model path handling without loading the real model.

## 3. Documentation

- [x] 3.1 Rewrite `README.md` as the complete operator guide for Windows, uv setup, `.venv` recreation, model download, execution, state, logs, and troubleshooting.
- [x] 3.2 Document `Systran/faster-whisper-large-v3` as the recommended default model and include the exact `hf download` command with `--local-dir`.
- [x] 3.3 Document `turbo` / `mobiuslabsgmbh/faster-whisper-large-v3-turbo` as an optional speed-focused model.
- [x] 3.4 Remove PyInstaller build-to-exe instructions and executable usage from `README.md`.

## 4. Scripts and Cleanup

- [x] 4.1 Remove executable build scripts or update helper scripts to call `uv run python -m video_to_text`.
- [x] 4.2 Remove generated package metadata or build artifacts that should not be tracked.
- [x] 4.3 Confirm `.gitignore` covers `.venv`, model files, logs, build outputs, and local cache artifacts.

## 5. Verification

- [x] 5.1 Run the test suite with uv.
- [x] 5.2 Run a dry-run command through uv to verify the application entry point starts.
- [x] 5.3 Run OpenSpec validation/status for `modernize-video-transcription-workflow`.
