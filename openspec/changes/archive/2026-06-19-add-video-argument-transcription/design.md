## Context

The application currently builds `AppSettings` from `argparse`, scans only the root of a hardcoded `E:\obs` directory, writes Markdown next to each discovered `.mp4`, and constructs one `FasterWhisperTranscriber` with CUDA-oriented defaults. This change replaces the hardcoded input default with explicit input selection: scan a user-provided directory, transcribe selected video files, or prompt for a directory when no input argument is provided.

The current transcriber loads the faster-whisper model lazily on first transcription. That is a useful boundary for fallback because CUDA failures can happen during model load as well as during transcription. The fallback must happen before any video is successfully processed, so the state file and Markdown output do not mix device attempts for the same run.

## Goals / Non-Goals

**Goals:**

- Support `-d`/`--dir` for scanning a directory root.
- Support repeatable `-v`/`--video` arguments for one or more explicit `.mp4` files.
- Prompt for a directory only when no directory or video input argument is provided.
- Reject combined directory and explicit-video inputs.
- Write each selected video transcript beside the source video using the existing Markdown format.
- Preserve existing scan, state, dry-run, reprocess, stability, logging, and summary semantics.
- Try CUDA/float16 first, then use CPU-friendly settings automatically when CUDA load or transcription fails before processing succeeds.
- Keep the implementation small and testable with injected transcribers.

**Non-Goals:**

- Add recursive directory inputs or glob expansion.
- Add interactive prompts for device selection.
- Change the transcript Markdown schema.
- Retry a video after a partial Markdown write or after a later per-file transcription error once earlier files have already succeeded.

## Decisions

1. Add input-selection fields to `AppSettings`.

   `parse_args` will define `-d`/`--dir` as a single directory path and `-v`/`--video` with `action="append"` for explicit videos. `AppSettings` should carry the selected directory as `watch_directory: Path | None` and explicit inputs as `video_paths: tuple[Path, ...]`, with no hardcoded directory default.

   Alternative considered: keep `E:\obs` as a fallback. Removing the default makes every run's input source intentional, either by argument or by the directory prompt.

2. Use an `argparse` mutually exclusive group for input arguments.

   `-d`/`--dir` and `-v`/`--video` should be mutually exclusive at the parser level so users get a direct CLI error if they provide both. The group should not be required because the no-input case intentionally prompts for a directory.

   Alternative considered: manually validate mixed inputs after parsing. The parser-level group gives clearer help output and consistent argument errors.

3. Prompt for a directory only in the no-input path.

   After parsing, if no directory and no videos were supplied, call a small prompt function that asks for a directory path and returns a `Path`. Keep the prompt scoped to directory selection only; all other options remain CLI flags.

   Alternative considered: prompt for missing or invalid video paths too. That would make non-interactive/scripted usage unpredictable and is outside the requested behavior.

4. Use a single eligible-video iterator that switches by mode.

   When `video_paths` is populated, the run validates and iterates exactly those files in argument order. Otherwise, the run validates the selected or prompted directory and scans only its root. This avoids surprising scans and keeps output beside each selected source path.

   Alternative considered: convert explicit videos into a temporary watch directory abstraction. That would obscure path-specific validation and make per-video error reporting less direct.

5. Validate selected inputs before model loading.

   Directory inputs must exist and be directories. Explicit video paths must exist, be files, and currently use `.mp4`, matching the existing project scope. Validation errors should fail the run before transcriber work begins.

   Alternative considered: let faster-whisper handle unsupported files. Early validation gives clearer CLI failures and avoids starting model load for invalid input.

6. Implement fallback by constructing a primary and fallback transcriber.

   The application will try the CUDA transcriber first. If model loading or transcription raises before any video is successfully processed, it logs the failure, constructs a CPU transcriber with CPU-safe compute settings, and restarts the run loop from the same eligible videos. Once a video succeeds, later per-file errors remain normal transcription failures and do not switch devices mid-run.

   Alternative considered: catch CUDA errors inside `FasterWhisperTranscriber`. Keeping orchestration in `app.py` preserves the simple transcriber protocol and makes tests easier with fake transcribers.

7. Keep state keys based on normalized source paths.

   Explicit videos use the same fingerprint, output existence, and normalized path checks as scanned videos. This means a video transcribed explicitly and later seen in a scan can still be skipped if the path and fingerprint match.

   Alternative considered: maintain separate state namespaces for explicit and scanned videos. That would create duplicate processing for the same file without adding user value.

## Risks / Trade-offs

- Fallback may hide a CUDA configuration problem by completing on CPU -> Mitigation: log the primary failure and the fallback device clearly.
- CPU fallback can be much slower for large videos -> Mitigation: use CPU only after the GPU attempt fails before successful processing.
- Re-running the whole eligible list after primary failure repeats validation and stability checks -> Mitigation: validation is cheap, and repeating stability checks is safer for actively written files.
- Prompting can block non-interactive runs that omit inputs -> Mitigation: documented scripted usage should pass `-d` or `-v`, and the prompt happens only when no input option is provided.
- Explicit paths and directories can point anywhere on disk -> Mitigation: this is intentional; output remains beside each source, and existing normalized path state still applies.

## Migration Plan

Implement behind the existing CLI entry point with a changed input contract: users must provide `-d`, provide one or more `-v` options, or answer the directory prompt. Rollback is limited to restoring the previous default directory behavior and removing the new input-selection path.

## Open Questions

- None.
