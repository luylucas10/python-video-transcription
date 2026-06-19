## ADDED Requirements

### Requirement: Default model is faster-whisper large-v3
The project SHALL document `Systran/faster-whisper-large-v3` as the default Hugging Face model for the current `faster-whisper` implementation.

#### Scenario: User downloads default model
- **WHEN** a user follows the model download instructions
- **THEN** the README provides an `hf download Systran/faster-whisper-large-v3` command that stores the model in a stable local directory

#### Scenario: Application uses default model shorthand
- **WHEN** the user runs the application without overriding the model
- **THEN** the application uses the existing `large-v3` faster-whisper model default

### Requirement: Local model directories are supported
The project SHALL support passing a local faster-whisper model directory as the model value.

#### Scenario: Run with downloaded local model
- **WHEN** a user passes a local model directory downloaded with `hf download`
- **THEN** the transcriber loads the model from that directory and transcribes videos

### Requirement: Optional turbo model is documented
The project SHALL document `turbo` or `mobiuslabsgmbh/faster-whisper-large-v3-turbo` as an optional speed-oriented model, not the default.

#### Scenario: User chooses speed over accuracy
- **WHEN** a user wants faster transcription
- **THEN** the README shows the turbo model option and explains that it trades default accuracy guidance for speed

### Requirement: Hugging Face CLI usage is documented
The project SHALL document how to install or run the Hugging Face Hub CLI and use `hf download` for faster-whisper models.

#### Scenario: User prepares model files
- **WHEN** a user follows README setup
- **THEN** the instructions include the repository ID, local destination directory, and command needed to download model files
