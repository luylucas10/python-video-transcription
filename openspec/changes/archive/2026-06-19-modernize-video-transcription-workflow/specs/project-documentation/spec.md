## ADDED Requirements

### Requirement: README is the complete operator guide
The README SHALL document setup, model download, execution, output, state, logs, reprocessing, and troubleshooting for the supported workflow.

#### Scenario: New user reads README
- **WHEN** a user starts from a clean checkout
- **THEN** the README provides enough commands to install uv-managed dependencies, download the default model, and run transcription

### Requirement: README documents state and output behavior
The README SHALL explain where Markdown files, processed-video state, and logs are written.

#### Scenario: User checks what was processed
- **WHEN** a user wants to know why a video was skipped
- **THEN** the README identifies the state file and log file locations

### Requirement: README excludes executable build workflow
The README SHALL not include PyInstaller build instructions or generated executable usage as supported commands.

#### Scenario: User searches for build instructions
- **WHEN** a user reads the README
- **THEN** the only supported execution path is Python through uv

### Requirement: README documents model choice
The README SHALL explain that `Systran/faster-whisper-large-v3` is the default recommended model and that turbo is optional for speed.

#### Scenario: User does not know which model to download
- **WHEN** a user reads the model section
- **THEN** the README names the default model repository and gives the exact download command
