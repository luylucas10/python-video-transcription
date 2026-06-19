## ADDED Requirements

### Requirement: Process root videos from obs directory
The application SHALL scan only the root of `E:\obs` for `.mp4` files.

#### Scenario: Directory contains files and subdirectories
- **WHEN** `E:\obs` contains root `.mp4` files and nested `.mp4` files in subdirectories
- **THEN** only root `.mp4` files are eligible for transcription

### Requirement: Write Markdown next to source videos
The application SHALL write each transcript as a Markdown file with the same base filename as the video.

#### Scenario: Video is transcribed
- **WHEN** `E:\obs\aula.mp4` is successfully transcribed
- **THEN** the application writes `E:\obs\aula.md`

### Requirement: Remember processed videos
The application SHALL persist processed-video state and skip unchanged videos that already have Markdown output.

#### Scenario: Video already processed
- **WHEN** a video fingerprint exists in state and the matching Markdown file exists
- **THEN** the application skips transcription for that video

#### Scenario: User forces reprocessing
- **WHEN** a user runs the application with the documented reprocess option
- **THEN** the application transcribes eligible videos even if state says they were processed

### Requirement: Avoid files still being written
The application SHALL skip videos whose file fingerprint changes during stability checks.

#### Scenario: Recording is still in progress
- **WHEN** a video changes size or modification time during stability checks
- **THEN** the application leaves it pending for a later run
