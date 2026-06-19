## Why

The project is currently documented and packaged as a Windows-first workflow, even though the Python application is close to being portable. Linux support will let the same transcription CLI run reliably on Linux workstations and servers without relying on Windows batch files or Windows-only setup instructions.

## What Changes

- Document Linux prerequisites, uv setup, model download, and CLI usage with POSIX paths.
- Add a Linux-friendly launcher or documented command path equivalent to the current `run.bat` workflow.
- Verify and test Linux-safe path handling for input videos, output Markdown, model cache, state, and logs.
- Keep Windows behavior working; this change is additive and not a breaking change.

## Capabilities

### New Capabilities

- `linux-platform-support`: Covers Linux installation, execution, launcher behavior, and cross-platform persistence paths for transcription runs.

### Modified Capabilities

## Impact

- README setup and usage documentation.
- Optional shell launcher alongside `run.bat`.
- Python path, state, log, and model-cache behavior where platform assumptions are present.
- Automated tests for POSIX-style paths and Linux-compatible command flows.
