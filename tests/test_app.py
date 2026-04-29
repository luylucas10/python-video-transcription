from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from video_to_text import app
from video_to_text.state import load_state, save_state
from video_to_text.tokenizer import TranscriptChunk, build_chunks, count_tokens
from video_to_text.transcriber import TranscriptResult, TranscriptSegment


class FakeTranscriber:
    def __init__(self, result: TranscriptResult) -> None:
        self.result = result
        self.calls: list[Path] = []

    def transcribe(self, video_path: Path) -> TranscriptResult:
        self.calls.append(video_path)
        return self.result


class FailingTranscriber:
    """Always raises to exercise the failure path inside run()."""

    def transcribe(self, video_path: Path) -> TranscriptResult:
        raise RuntimeError("GPU crashed")


@pytest.fixture()
def transcript_result() -> TranscriptResult:
    return TranscriptResult(
        model_name="test-model",
        language="pt",
        language_probability=0.99,
        duration_seconds=125.0,
        segments=[
            TranscriptSegment(start_seconds=0.0, end_seconds=2.5, text="Olá mundo."),
            TranscriptSegment(start_seconds=5.0, end_seconds=8.0, text="Tudo bem?"),
        ],
    )


@pytest.fixture()
def temp_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> app.AppSettings:
    watch_directory = tmp_path / "obs"
    watch_directory.mkdir()
    state_directory = tmp_path / "state"
    log_directory = tmp_path / "logs"

    monkeypatch.setattr(app, "DEFAULT_WATCH_DIRECTORY", watch_directory)
    monkeypatch.setattr(app, "default_state_directory", lambda: state_directory)
    monkeypatch.setattr(app, "default_log_directory", lambda: log_directory)

    return app.AppSettings(watch_directory=watch_directory, stability_wait_seconds=0.0)


# ---------------------------------------------------------------------------
# run() — happy path
# ---------------------------------------------------------------------------

def test_run_processes_new_videos(temp_settings: app.AppSettings, transcript_result: TranscriptResult) -> None:
    video_path = temp_settings.watch_directory / "aula.mp4"
    video_path.write_bytes(b"video")
    transcriber = FakeTranscriber(transcript_result)

    summary = app.run(temp_settings, transcriber=transcriber)

    markdown_path = video_path.with_suffix(".md")
    assert summary.processed_count == 1
    assert summary.failed_files == ()
    assert transcriber.calls == [video_path]
    assert markdown_path.exists()
    assert "Olá mundo." in markdown_path.read_text(encoding="utf-8")
    assert temp_settings.state_file.exists()


def test_run_skips_already_processed_video(temp_settings: app.AppSettings, transcript_result: TranscriptResult) -> None:
    video_path = temp_settings.watch_directory / "aula.mp4"
    video_path.write_bytes(b"video")
    markdown_path = video_path.with_suffix(".md")
    markdown_path.write_text("existente", encoding="utf-8")
    fingerprint = app.fingerprint_file(video_path)
    app.save_state(
        temp_settings.state_file,
        {
            "version": 1,
            "videos": {
                app.normalize_path(video_path): {
                    "size_bytes": fingerprint.size_bytes,
                    "modified_time_ns": fingerprint.modified_time_ns,
                }
            },
        },
    )
    transcriber = FakeTranscriber(transcript_result)

    summary = app.run(temp_settings, transcriber=transcriber)

    assert summary.skipped_count == 1
    assert transcriber.calls == []


# ---------------------------------------------------------------------------
# run() — dry_run and reprocess
# ---------------------------------------------------------------------------

def test_run_dry_run_does_not_transcribe(temp_settings: app.AppSettings, transcript_result: TranscriptResult) -> None:
    video_path = temp_settings.watch_directory / "aula.mp4"
    video_path.write_bytes(b"video")
    transcriber = FakeTranscriber(transcript_result)
    dry_settings = app.AppSettings(
        watch_directory=temp_settings.watch_directory,
        stability_wait_seconds=0.0,
        dry_run=True,
    )

    summary = app.run(dry_settings, transcriber=transcriber)

    assert summary.pending_count == 1
    assert summary.processed_count == 0
    assert transcriber.calls == []
    assert not video_path.with_suffix(".md").exists()


def test_run_reprocess_retranscribes_even_when_state_recorded(
    temp_settings: app.AppSettings, transcript_result: TranscriptResult
) -> None:
    video_path = temp_settings.watch_directory / "aula.mp4"
    video_path.write_bytes(b"video")
    markdown_path = video_path.with_suffix(".md")
    markdown_path.write_text("antigo", encoding="utf-8")
    fingerprint = app.fingerprint_file(video_path)
    app.save_state(
        temp_settings.state_file,
        {
            "version": 1,
            "videos": {
                app.normalize_path(video_path): {
                    "size_bytes": fingerprint.size_bytes,
                    "modified_time_ns": fingerprint.modified_time_ns,
                }
            },
        },
    )
    transcriber = FakeTranscriber(transcript_result)
    reprocess_settings = app.AppSettings(
        watch_directory=temp_settings.watch_directory,
        stability_wait_seconds=0.0,
        reprocess=True,
    )

    summary = app.run(reprocess_settings, transcriber=transcriber)

    assert summary.processed_count == 1
    assert transcriber.calls == [video_path]


# ---------------------------------------------------------------------------
# run() — transcriber failure
# ---------------------------------------------------------------------------

def test_run_records_failed_file_when_transcriber_raises(temp_settings: app.AppSettings) -> None:
    video_path = temp_settings.watch_directory / "problema.mp4"
    video_path.write_bytes(b"video")

    summary = app.run(temp_settings, transcriber=FailingTranscriber())

    assert summary.failed_files == (str(video_path),)
    assert summary.processed_count == 0
    assert not video_path.with_suffix(".md").exists()


# ---------------------------------------------------------------------------
# validate_watch_directory
# ---------------------------------------------------------------------------

def test_validate_watch_directory_accepts_existing_dir(tmp_path: Path) -> None:
    app.validate_watch_directory(tmp_path)  # should not raise


def test_validate_watch_directory_raises_for_nonexistent(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        app.validate_watch_directory(tmp_path / "nao_existe")


def test_validate_watch_directory_raises_for_file(tmp_path: Path) -> None:
    file_path = tmp_path / "arquivo.txt"
    file_path.write_text("x")
    with pytest.raises(NotADirectoryError):
        app.validate_watch_directory(file_path)


# ---------------------------------------------------------------------------
# is_file_stable
# ---------------------------------------------------------------------------

def test_is_file_stable_returns_true_for_static_file(tmp_path: Path) -> None:
    video = tmp_path / "video.mp4"
    video.write_bytes(b"abc")
    assert app.is_file_stable(video, checks=2, wait_seconds=0.0) is True


def test_is_file_stable_returns_false_when_file_grows(tmp_path: Path) -> None:
    video = tmp_path / "video.mp4"
    # Start with one byte
    video.write_bytes(b"a")

    # is_file_stable reads the fingerprint, then waits, then reads again.
    # We simulate growth by rewriting the file between calls using a side-effecting stat mock.
    original_stat = Path.stat

    call_count = 0

    def growing_stat(self: Path, **kwargs):  # type: ignore[override]
        nonlocal call_count
        result = original_stat(self, **kwargs)
        # Each stat() call returns a progressively larger apparent size
        call_count += 1
        # Use __class__ to build a mock-like namespace object (avoid dataclass complications)
        class _FakeStat:
            st_size = result.st_size + call_count
            st_mtime_ns = result.st_mtime_ns + call_count

        return _FakeStat()

    import unittest.mock as mock
    with mock.patch.object(Path, "stat", growing_stat):
        assert app.is_file_stable(video, checks=2, wait_seconds=0.0) is False


# ---------------------------------------------------------------------------
# load_state / save_state edge cases
# ---------------------------------------------------------------------------

def test_load_state_returns_default_for_missing_file(tmp_path: Path) -> None:
    state = load_state(tmp_path / "nao_existe.json")
    assert state == {"version": 1, "videos": {}}


def test_load_state_returns_default_for_empty_file(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text("   ", encoding="utf-8")
    state = load_state(state_file)
    assert state == {"version": 1, "videos": {}}


def test_load_state_returns_default_for_corrupt_json(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        # json.loads raises — caller gets an exception rather than silently corrupt state
        load_state(state_file)


def test_load_state_resets_on_version_mismatch(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps({"version": 99, "videos": {"old": {"size_bytes": 1}}}),
        encoding="utf-8",
    )
    state = load_state(state_file)
    assert state == {"version": 1, "videos": {}}


def test_save_and_load_state_roundtrip(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    original = {"version": 1, "videos": {"E:\\obs\\video.mp4": {"size_bytes": 42}}}
    save_state(state_file, original)
    loaded = load_state(state_file)
    assert loaded["videos"] == original["videos"]


# ---------------------------------------------------------------------------
# build_markdown / format_timestamp
# ---------------------------------------------------------------------------

def test_build_markdown_contains_metadata(transcript_result: TranscriptResult) -> None:
    content = app.build_markdown(
        Path(r"E:\obs\video.mp4"),
        transcript_result,
        datetime(2026, 4, 28, 10, 0, tzinfo=UTC),
        datetime(2026, 4, 28, 10, 5, tzinfo=UTC),
    )

    assert "# Transcrição de video.mp4" in content
    assert "## Chunks" in content
    assert "## Trechos com timestamps" in content
    assert "00:00:05 - 00:00:08" in content


def test_build_markdown_has_yaml_frontmatter(transcript_result: TranscriptResult) -> None:
    content = app.build_markdown(
        Path(r"E:\obs\aula.mp4"),
        transcript_result,
        datetime(2026, 4, 28, 10, 0, tzinfo=UTC),
        datetime(2026, 4, 28, 10, 5, tzinfo=UTC),
    )

    assert content.startswith("---\n"), "Markdown deve iniciar com YAML frontmatter"
    assert "title:" in content
    assert "source:" in content
    assert "total_tokens:" in content
    assert "chunk_count:" in content
    assert "tokenizer:" in content
    assert "language:" in content
    assert "model:" in content


def test_build_markdown_chunk_header_format(transcript_result: TranscriptResult) -> None:
    content = app.build_markdown(
        Path(r"E:\obs\aula.mp4"),
        transcript_result,
        datetime(2026, 4, 28, tzinfo=UTC),
        datetime(2026, 4, 28, tzinfo=UTC),
        max_tokens_per_chunk=500,
    )

    # All segments fit in one chunk of 500 tokens — expect "Chunk 1/1"
    assert "### Chunk 1/1" in content
    assert "tokens" in content


def test_build_markdown_chunks_contain_transcript_text(transcript_result: TranscriptResult) -> None:
    content = app.build_markdown(
        Path(r"E:\obs\aula.mp4"),
        transcript_result,
        datetime(2026, 4, 28, tzinfo=UTC),
        datetime(2026, 4, 28, tzinfo=UTC),
    )

    assert "Olá mundo." in content
    assert "Tudo bem?" in content


def test_build_markdown_small_chunk_limit_creates_multiple_chunks() -> None:
    # Use very short segments and a tiny chunk limit to force multiple chunks
    result = TranscriptResult(
        model_name="test-model",
        language="pt",
        language_probability=0.99,
        duration_seconds=10.0,
        segments=[
            TranscriptSegment(0.0, 1.0, "Alpha beta"),
            TranscriptSegment(1.0, 2.0, "Gamma delta"),
            TranscriptSegment(2.0, 3.0, "Epsilon zeta"),
        ],
    )
    # A limit of 1 token forces a new chunk for every segment
    content = app.build_markdown(Path(r"E:\obs\test.mp4"), result, datetime(2026, 4, 28, tzinfo=UTC), datetime(2026, 4, 28, tzinfo=UTC), max_tokens_per_chunk=1)

    assert "Chunk 1/" in content
    assert "Chunk 2/" in content
    assert "Chunk 3/" in content


def test_build_markdown_no_speech_shows_placeholder() -> None:
    empty_result = TranscriptResult(
        model_name="test-model",
        language=None,
        language_probability=None,
        duration_seconds=None,
        segments=[],
    )
    content = app.build_markdown(
        Path(r"E:\obs\silencio.mp4"),
        empty_result,
        datetime(2026, 4, 28, tzinfo=UTC),
        datetime(2026, 4, 28, tzinfo=UTC),
    )
    assert "_Nenhuma fala detectada._" in content
    assert "- Nenhum trecho de fala detectado." in content
    assert "total_tokens: 0" in content


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00:00"),
        (59, "00:00:59"),
        (60, "00:01:00"),
        (3661, "01:01:01"),
    ],
)
def test_format_timestamp(seconds: float, expected: str) -> None:
    assert app.format_timestamp(seconds) == expected


# ---------------------------------------------------------------------------
# tokenizer — count_tokens and build_chunks
# ---------------------------------------------------------------------------


def test_count_tokens_returns_positive_integer() -> None:
    n = count_tokens("Olá mundo, como vai você?")
    assert isinstance(n, int)
    assert n > 0


def test_count_tokens_empty_string_returns_zero() -> None:
    assert count_tokens("") == 0


def test_build_chunks_empty_segments_returns_empty_list() -> None:
    assert build_chunks([], max_tokens=500) == []


def test_build_chunks_single_segment_yields_one_chunk() -> None:
    segments = [TranscriptSegment(0.0, 5.0, "Olá mundo.")]
    chunks = build_chunks(segments, max_tokens=500)
    assert len(chunks) == 1
    assert chunks[0].text == "Olá mundo."
    assert chunks[0].index == 1
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 5.0
    assert chunks[0].token_count > 0


def test_build_chunks_respects_max_tokens_limit() -> None:
    # A limit of 1 means each segment must get its own chunk
    segments = [
        TranscriptSegment(0.0, 1.0, "Alpha beta gamma"),
        TranscriptSegment(1.0, 2.0, "Delta epsilon zeta"),
        TranscriptSegment(2.0, 3.0, "Eta theta iota"),
    ]
    chunks = build_chunks(segments, max_tokens=1)
    assert len(chunks) == 3
    for i, chunk in enumerate(chunks, start=1):
        assert chunk.index == i


def test_build_chunks_combines_segments_within_limit() -> None:
    # All three short segments should fit into one chunk if limit is large enough
    segments = [
        TranscriptSegment(0.0, 1.0, "A"),
        TranscriptSegment(1.0, 2.0, "B"),
        TranscriptSegment(2.0, 3.0, "C"),
    ]
    chunks = build_chunks(segments, max_tokens=1000)
    assert len(chunks) == 1
    assert "A" in chunks[0].text
    assert "B" in chunks[0].text
    assert "C" in chunks[0].text
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 3.0


def test_build_chunks_time_range_is_correct() -> None:
    segments = [
        TranscriptSegment(10.0, 20.0, "Primeiro"),
        TranscriptSegment(20.0, 30.0, "Segundo"),
    ]
    chunks = build_chunks(segments, max_tokens=1000)
    assert chunks[0].start_seconds == 10.0
    assert chunks[0].end_seconds == 30.0


def test_build_chunks_token_count_is_positive_for_non_empty_text() -> None:
    segments = [TranscriptSegment(0.0, 5.0, "Texto de exemplo para teste de tokenização.")]
    chunks = build_chunks(segments, max_tokens=500)
    assert chunks[0].token_count > 0


