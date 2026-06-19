## ADDED Requirements

### Requirement: Linux setup is documented
The project documentation SHALL describe how to install prerequisites, create the uv-managed environment, download a faster-whisper model, and run transcription commands on Linux using POSIX shell syntax.

#### Scenario: User reads Linux setup instructions
- **WHEN** a Linux user opens the project README
- **THEN** the documentation includes Linux-specific prerequisite and setup commands that do not depend on PowerShell, `winget`, backslash paths, or `run.bat`

### Requirement: Linux command execution is supported
The system SHALL support running the transcription CLI on Linux through `uv run python -m video_to_text` and the installed `video-to-text` console script with POSIX paths.

#### Scenario: User runs dry-run on a Linux directory
- **WHEN** a user runs the CLI with `-d /path/to/videos --dry-run`
- **THEN** the system validates the directory, scans only its root for `.mp4` files, and reports eligible videos without transcribing them

#### Scenario: User transcribes a specific Linux video path
- **WHEN** a user runs the CLI with `-v /path/to/video.mp4`
- **THEN** the system writes `/path/to/video.md` beside the source video after a successful transcription

### Requirement: Linux launcher is available
The project SHALL provide a POSIX shell launcher that offers the same project-local convenience role as `run.bat` while forwarding user-provided CLI arguments.

#### Scenario: User invokes Linux launcher with arguments
- **WHEN** a user runs the Linux launcher with valid CLI arguments
- **THEN** the launcher executes the Python module through uv and forwards those arguments unchanged

### Requirement: Cross-platform persistence paths are stable
The system SHALL use platform-safe filesystem APIs for state, log, model cache, and Markdown output paths on Linux and Windows.

#### Scenario: Linux run persists state and logs
- **WHEN** a transcription run processes or evaluates videos on Linux
- **THEN** the system uses the project-local `data/processed_videos.json`, project-local `logs/last-run.log`, and the user's home `.cache/video-to-text/models` directory without Windows-only path assumptions

#### Scenario: Windows behavior remains unchanged
- **WHEN** a user runs the existing Windows workflow
- **THEN** state, logs, model cache, and Markdown output behavior remain compatible with the current documented Windows usage
