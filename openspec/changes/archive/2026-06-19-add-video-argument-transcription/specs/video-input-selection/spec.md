## ADDED Requirements

### Requirement: Accept a directory argument
The application SHALL accept a directory to scan through `-d` or `--dir`.

#### Scenario: User passes a directory
- **WHEN** the user runs the application with `-d path\to\videos`
- **THEN** the application scans only the root of that directory for supported video files

#### Scenario: Directory path does not exist
- **WHEN** the user passes `-d` with a path that does not exist or is not a directory
- **THEN** the application exits with an error identifying the invalid directory before loading a transcription model

### Requirement: Prompt for directory when no input argument is provided
The application SHALL prompt the user for a directory only when neither `-d`/`--dir` nor `-v`/`--video` is provided.

#### Scenario: User passes no input arguments
- **WHEN** the user runs the application without `-d`, `--dir`, `-v`, or `--video`
- **THEN** the application asks the user to enter a directory path before scanning for videos

#### Scenario: User passes explicit inputs
- **WHEN** the user runs the application with `-d`, `--dir`, `-v`, or `--video`
- **THEN** the application does not prompt for a directory

### Requirement: Accept repeatable video arguments
The application SHALL accept one or more explicit video files through repeatable `-v` or `--video` CLI options.

#### Scenario: User passes multiple videos
- **WHEN** the user runs the application with `-v path\to\video.mp4 -v path\to\another.mp4`
- **THEN** the application uses exactly those video paths as the eligible transcription inputs

### Requirement: Reject mixed directory and video arguments
The application SHALL reject a run that combines `-d`/`--dir` with `-v`/`--video`.

#### Scenario: User passes directory and video inputs
- **WHEN** the user runs the application with `-d path\to\videos -v path\to\video.mp4`
- **THEN** the application exits with a CLI error explaining that directory and video inputs are mutually exclusive

### Requirement: Validate explicit video inputs
The application SHALL validate each explicit video path before transcription begins.

#### Scenario: Explicit path does not exist
- **WHEN** a `-v` path does not exist
- **THEN** the application exits with an error identifying the missing path before loading a transcription model

#### Scenario: Explicit path is not a supported video file
- **WHEN** a `-v` path is not a file with the supported `.mp4` suffix
- **THEN** the application exits with an error identifying the invalid path before loading a transcription model

### Requirement: Write transcript beside selected video
The application SHALL write each selected video transcript as a Markdown file beside the source video, using the source base filename.

#### Scenario: Explicit video is transcribed
- **WHEN** the user transcribes `C:\courses\aula.mp4` through `-v`
- **THEN** the application writes `C:\courses\aula.md`

#### Scenario: Directory video is transcribed
- **WHEN** the user transcribes `C:\courses\aula.mp4` through `-d C:\courses`
- **THEN** the application writes `C:\courses\aula.md`

### Requirement: Preserve state behavior for selected videos
The application SHALL apply existing fingerprint, Markdown-existence, dry-run, reprocess, and stability behavior to selected video inputs.

#### Scenario: Selected video was already processed
- **WHEN** a selected video has a matching state fingerprint and its Markdown output exists
- **THEN** the application skips transcription unless `--reprocess` is set

#### Scenario: Selected video is still being written
- **WHEN** a selected video changes size or modification time during stability checks
- **THEN** the application leaves it pending for a later run
