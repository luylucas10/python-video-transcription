## ADDED Requirements

### Requirement: Try GPU before CPU
The application SHALL attempt transcription with the configured GPU device before using CPU fallback.

#### Scenario: GPU transcription succeeds
- **WHEN** the GPU model loads and transcribes eligible videos successfully
- **THEN** the application completes the run without constructing or using a CPU fallback transcriber

### Requirement: Fall back to CPU before successful processing
The application SHALL retry the run with CPU-compatible transcription settings when the GPU attempt fails before any video is successfully processed.

#### Scenario: GPU model load fails
- **WHEN** the GPU transcription model fails to load before any video is processed
- **THEN** the application logs the GPU failure and retries eligible videos with CPU settings

#### Scenario: First GPU transcription fails
- **WHEN** the GPU model loads but the first transcription fails before any video is processed
- **THEN** the application logs the GPU failure and retries eligible videos with CPU settings

### Requirement: Do not switch devices after success
The application SHALL NOT switch to CPU fallback after one or more videos have already been successfully processed in the current run.

#### Scenario: Later video fails after GPU success
- **WHEN** at least one video has already been transcribed successfully on GPU and a later video fails
- **THEN** the application records the later failure using the existing failed-file behavior and does not retry the run on CPU

### Requirement: Report fallback outcome
The application SHALL log whether the run used GPU successfully or switched to CPU fallback.

#### Scenario: CPU fallback is used
- **WHEN** the application retries with CPU fallback
- **THEN** the log includes the failed GPU attempt and the CPU fallback device settings used for the retry
