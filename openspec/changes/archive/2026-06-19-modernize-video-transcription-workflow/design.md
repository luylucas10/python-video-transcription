## Context

The current application already has the core behavior needed for batch transcription: it scans only the root of `E:\obs`, skips subfolders, writes a `.md` file next to each `.mp4`, stores processed-video state, and exposes a `Transcriber` protocol with a `FasterWhisperTranscriber` implementation. The change should preserve that runtime design and focus on modernizing setup, model management, documentation, and removal of the executable build workflow.

The current README and dependency metadata still describe manual `.venv` activation, pip installation, and PyInstaller packaging. The desired workflow is a uv-managed Python project that can recreate `.venv`, install dependencies, download the selected Hugging Face model, and run the Python entry point directly.

## Goals / Non-Goals

**Goals:**

- Keep `faster-whisper` as the transcription backend.
- Make `Systran/faster-whisper-large-v3` the documented default model because it matches the current `large-v3` default and prioritizes Portuguese/multilingual accuracy.
- Document `turbo` / `mobiuslabsgmbh/faster-whisper-large-v3-turbo` as an optional speed-oriented model.
- Convert setup and execution instructions to uv, including `.venv` recreation, dependency sync, locking, and run commands.
- Remove PyInstaller from the supported project workflow and documentation.
- Keep processed-video memory and Markdown output behavior stable.

**Non-Goals:**

- Do not migrate to `whisper.cpp`.
- Do not add a GUI or background service.
- Do not process subdirectories under `E:\obs`.
- Do not change the Markdown structure unless required by the faster-whisper model path changes.

## Decisions

### Keep faster-whisper as the backend

The existing code already wraps `faster-whisper` behind a protocol and has tests around the application workflow. Keeping it avoids replacing working transcription behavior and preserves the current `cuda`/`float16` assumptions for NVIDIA GPU usage.

Alternative considered: migrating to `whisper.cpp`. That would require a different model format, different runtime integration, and likely a subprocess or binding decision. The user clarified that this is not needed.

### Default to `Systran/faster-whisper-large-v3`

The README should tell users to download `Systran/faster-whisper-large-v3` with `hf download` into a stable local project model directory, for example `models\faster-whisper-large-v3`. The app should allow the model argument to be either the existing shorthand `large-v3`, the full Hugging Face model ID, or a local model directory.

Alternative considered: using `turbo` by default. Turbo is useful for speed, but `large-v3` is the safer default when accuracy for Portuguese video transcription is the priority.

### Use uv as the only supported environment workflow

The project should include uv-friendly metadata and a lockfile. README commands should use `uv python pin`, `uv venv`, `uv sync`, and `uv run`. The supported Python version should be pinned to a concrete compatible version, with Python 3.11 as the conservative choice because the project already targets it and the dependencies support it.

Alternative considered: keeping pip install instructions as a fallback. That would keep two setup paths to maintain, which conflicts with the goal of documenting one reproducible workflow.

### Remove executable packaging from the supported path

PyInstaller should be removed from dev dependencies and README instructions. Any build scripts or batch files that exist only for the executable workflow should be removed or updated to call `uv run python -m video_to_text`.

Alternative considered: keeping PyInstaller as an optional extra. The user explicitly asked to remove the build-to-exe path, so keeping it would preserve unsupported behavior.

## Risks / Trade-offs

- Local model path handling could diverge from faster-whisper's built-in cache behavior -> Add tests or documented manual checks for `--model` accepting both `large-v3` and a local model directory.
- `hf download` may create a different directory layout than faster-whisper's automatic cache -> Document the exact `--local-dir` command and run the app with that local directory path.
- CUDA dependency issues on Windows can be environment-specific -> Keep troubleshooting notes in README and preserve CPU/int8 as an emergency fallback only if already supported by arguments.
- Removing PyInstaller may break a double-click workflow -> Replace it with a simple Python/uv command path, and update any remaining helper script to call uv instead of a packaged executable.

## Migration Plan

1. Update `pyproject.toml` for uv-managed development, remove PyInstaller from dev dependencies, and keep Python 3.11 compatibility.
2. Add or update `.python-version` and generate `uv.lock` through `uv sync`.
3. Update application configuration so the default remains `large-v3`, while README documents the full model ID and local-dir option.
4. Update `README.md` to cover uv setup, `.venv` recreation, `hf download Systran/faster-whisper-large-v3`, running the app, state/log locations, and reprocessing behavior.
5. Remove or update executable build scripts and references.
6. Run tests with uv.
