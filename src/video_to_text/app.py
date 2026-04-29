from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from video_to_text.state import load_state, save_state
from video_to_text.tokenizer import ENCODING_NAME, TranscriptChunk, build_chunks, count_tokens
from video_to_text.transcriber import FasterWhisperTranscriber, TranscriptResult, Transcriber

APP_NAME = "video-to-text"
DEFAULT_WATCH_DIRECTORY = Path(r"E:\obs")
DEFAULT_MODEL_NAME = "large-v3"

# Guard to prevent configure_logging from adding duplicate handlers on repeated calls
_logging_configured = False


def get_app_base_directory() -> Path:
    """Returns the folder containing the executable (packaged) or the project root (dev mode)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle — place data next to the .exe
        return Path(sys.executable).parent
    # __file__ is src/video_to_text/app.py — three parents up reaches the project root
    return Path(__file__).resolve().parents[2]


def default_state_directory() -> Path:
    state_directory = get_app_base_directory() / "data"
    state_directory.mkdir(parents=True, exist_ok=True)
    return state_directory


def default_log_directory() -> Path:
    log_directory = get_app_base_directory() / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    return log_directory


@dataclass(frozen=True, slots=True)
class AppSettings:
    watch_directory: Path = DEFAULT_WATCH_DIRECTORY
    model_name: str = DEFAULT_MODEL_NAME
    device: str = "cuda"
    # float16 maps directly to RTX 3090 tensor cores (no conversion overhead)
    compute_type: str = "float16"
    # "pt" skips Whisper's language detection step and improves Portuguese accuracy
    language: str | None = "pt"
    beam_size: int = 5
    # 16 audio chunks processed simultaneously via BatchedInferencePipeline on the RTX 3090
    batch_size: int = 16
    vad_filter: bool = True
    dry_run: bool = False
    reprocess: bool = False
    stability_wait_seconds: float = 2.0
    stability_checks: int = 2
    # Maximum tokens per RAG chunk written to the markdown file (cl100k_base encoding)
    max_tokens_per_chunk: int = 500

    @property
    def state_directory(self) -> Path:
        return default_state_directory()

    @property
    def state_file(self) -> Path:
        return self.state_directory / "processed_videos.json"

    @property
    def model_cache_directory(self) -> Path:
        # Stored in the user profile so model files (≈3 GB) survive rebuilds and reinstalls.
        cache_dir = Path.home() / ".cache" / APP_NAME / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @property
    def log_file(self) -> Path:
        return default_log_directory() / "last-run.log"


@dataclass(frozen=True, slots=True)
class VideoFingerprint:
    size_bytes: int
    modified_time_ns: int


@dataclass(frozen=True, slots=True)
class RunSummary:
    processed_count: int
    skipped_count: int
    pending_count: int
    failed_files: tuple[str, ...]


def configure_logging(log_file: Path) -> None:
    global _logging_configured
    if _logging_configured:
        return
    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Suppress per-request HTTP logs from huggingface_hub model loading (too verbose at INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    _logging_configured = True


def parse_args(argv: list[str] | None = None) -> AppSettings:
    parser = argparse.ArgumentParser(description="Transcreve .mp4 da raiz de E:\\obs para .md")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria processado sem transcrever")
    parser.add_argument("--reprocess", action="store_true", help="Ignora o estado salvo e processa novamente")
    parser.add_argument("--language", default="pt", help="Idioma para transcrição (padrão: pt). Use 'auto' para detecção automática.")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="Modelo do faster-whisper")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Chunks de áudio processados em paralelo na GPU via BatchedInferencePipeline (padrão: 16 para RTX 3090)",
    )
    parser.add_argument(
        "--max-tokens-per-chunk",
        type=int,
        default=500,
        help="Limite de tokens por chunk no markdown tokenizado (padrão: 500, encoding cl100k_base)",
    )
    parser.add_argument("--stability-wait-seconds", type=float, default=2.0, help="Espera entre verificações de estabilidade do arquivo")
    parser.add_argument("--stability-checks", type=int, default=2, help="Quantidade de comparações para detectar arquivo em escrita")
    arguments = parser.parse_args(argv)
    return AppSettings(
        model_name=arguments.model,
        language=None if arguments.language.lower() in ("auto", "") else arguments.language,
        dry_run=arguments.dry_run,
        reprocess=arguments.reprocess,
        batch_size=max(1, arguments.batch_size),
        max_tokens_per_chunk=max(1, arguments.max_tokens_per_chunk),
        stability_wait_seconds=max(0.0, arguments.stability_wait_seconds),
        stability_checks=max(1, arguments.stability_checks),
    )


def build_transcriber(settings: AppSettings) -> FasterWhisperTranscriber:
    return FasterWhisperTranscriber(
        model_name=settings.model_name,
        device=settings.device,
        compute_type=settings.compute_type,
        language=settings.language,
        beam_size=settings.beam_size,
        batch_size=settings.batch_size,
        vad_filter=settings.vad_filter,
        download_root=settings.model_cache_directory,
    )


def run(settings: AppSettings, transcriber: Transcriber | None = None) -> RunSummary:
    logging.info("Iniciando processamento em %s", settings.watch_directory)
    validate_watch_directory(settings.watch_directory)
    active_transcriber = transcriber or build_transcriber(settings)
    state = load_state(settings.state_file)
    known_videos = state.setdefault("videos", {})

    processed_count = 0
    skipped_count = 0
    pending_count = 0
    failed_files: list[str] = []

    for video_path in iter_root_videos(settings.watch_directory):
        fingerprint = fingerprint_file(video_path)
        output_path = video_path.with_suffix(".md")
        normalized_path = normalize_path(video_path)

        if not settings.reprocess and is_already_processed(known_videos, normalized_path, fingerprint, output_path):
            skipped_count += 1
            logging.info("Ignorando vídeo já processado: %s", video_path.name)
            continue

        if not is_file_stable(video_path, settings.stability_checks, settings.stability_wait_seconds):
            pending_count += 1
            logging.info("Pulando vídeo ainda em gravação: %s", video_path.name)
            continue

        if settings.dry_run:
            pending_count += 1
            logging.info("Dry-run: vídeo elegível para transcrição: %s", video_path.name)
            continue

        started_at = datetime.now(UTC)
        logging.info("Transcrevendo: %s", video_path.name)
        try:
            result = active_transcriber.transcribe(video_path)
            write_markdown(output_path, video_path, result, started_at, datetime.now(UTC), settings.max_tokens_per_chunk)
        except Exception:
            failed_files.append(str(video_path))
            logging.exception("Falha ao transcrever %s", video_path)
            continue

        known_videos[normalized_path] = {
            "size_bytes": fingerprint.size_bytes,
            "modified_time_ns": fingerprint.modified_time_ns,
            "markdown_file": str(output_path),
            "processed_at": datetime.now(UTC).isoformat(),
            "model_name": settings.model_name,
        }
        save_state(settings.state_file, state)
        processed_count += 1
        logging.info("Markdown gerado: %s", output_path.name)

    logging.info(
        "Resumo: %s processado(s), %s ignorado(s), %s pendente(s), %s falha(s)",
        processed_count,
        skipped_count,
        pending_count,
        len(failed_files),
    )
    return RunSummary(
        processed_count=processed_count,
        skipped_count=skipped_count,
        pending_count=pending_count,
        failed_files=tuple(failed_files),
    )


def validate_watch_directory(watch_directory: Path) -> None:
    if not watch_directory.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {watch_directory}")
    if not watch_directory.is_dir():
        raise NotADirectoryError(f"Caminho inválido (não é um diretório): {watch_directory}")


def iter_root_videos(watch_directory: Path) -> Iterable[Path]:
    for entry in sorted(watch_directory.iterdir(), key=lambda item: item.name.lower()):
        if entry.is_file() and entry.suffix.lower() == ".mp4":
            yield entry


def fingerprint_file(video_path: Path) -> VideoFingerprint:
    stat_result = video_path.stat()
    return VideoFingerprint(size_bytes=stat_result.st_size, modified_time_ns=stat_result.st_mtime_ns)


def is_already_processed(
    known_videos: dict[str, dict[str, object]],
    normalized_path: str,
    fingerprint: VideoFingerprint,
    output_path: Path,
) -> bool:
    existing = known_videos.get(normalized_path)
    if not existing or not output_path.exists():
        return False
    return (
        existing.get("size_bytes") == fingerprint.size_bytes
        and existing.get("modified_time_ns") == fingerprint.modified_time_ns
    )


def is_file_stable(video_path: Path, checks: int, wait_seconds: float) -> bool:
    previous_fingerprint = fingerprint_file(video_path)
    for _ in range(checks):
        if wait_seconds:
            time.sleep(wait_seconds)
        current_fingerprint = fingerprint_file(video_path)
        if current_fingerprint != previous_fingerprint:
            return False
        previous_fingerprint = current_fingerprint

    try:
        with video_path.open("rb"):
            return True
    except OSError:
        return False


def normalize_path(path: Path) -> str:
    import os
    return os.path.normcase(str(path.resolve()))


def _yaml_str(value: str) -> str:
    """Wrap *value* in YAML double-quotes, escaping backslashes and double-quotes."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_markdown(
    output_path: Path,
    video_path: Path,
    result: TranscriptResult,
    started_at: datetime,
    finished_at: datetime,
    max_tokens_per_chunk: int = 500,
) -> None:
    markdown_content = build_markdown(video_path, result, started_at, finished_at, max_tokens_per_chunk)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text(markdown_content, encoding="utf-8")
    temporary_path.replace(output_path)


def build_markdown(
    video_path: Path,
    result: TranscriptResult,
    started_at: datetime,
    finished_at: datetime,
    max_tokens_per_chunk: int = 500,
) -> str:
    chunks = build_chunks(result.segments, max_tokens_per_chunk)
    # When no segments produce chunks (empty transcript), total_tokens is 0
    total_tokens = sum(c.token_count for c in chunks)

    language = result.language or "desconhecido"
    language_confidence = (
        f"{result.language_probability:.4f}" if result.language_probability is not None else "null"
    )
    duration = (
        format_timestamp(result.duration_seconds) if result.duration_seconds is not None else "null"
    )
    duration_seconds_val = (
        f"{result.duration_seconds:.3f}" if result.duration_seconds is not None else "null"
    )

    # YAML frontmatter gives AI tooling (LlamaIndex, LangChain, etc.) structured metadata
    # for filtering, deduplication, and provenance tracking without parsing the body.
    frontmatter = (
        "---\n"
        f"title: {_yaml_str(f'Transcrição de {video_path.name}')}\n"
        f"source: {_yaml_str(str(video_path))}\n"
        f"generated_at: {_yaml_str(finished_at.isoformat())}\n"
        f"processing_started_at: {_yaml_str(started_at.isoformat())}\n"
        f"model: {_yaml_str(result.model_name)}\n"
        f"language: {_yaml_str(language)}\n"
        f"language_confidence: {language_confidence}\n"
        f"duration: {_yaml_str(duration)}\n"
        f"duration_seconds: {duration_seconds_val}\n"
        f"total_tokens: {total_tokens}\n"
        f"chunk_count: {len(chunks)}\n"
        f"tokens_per_chunk_limit: {max_tokens_per_chunk}\n"
        f"tokenizer: {_yaml_str(ENCODING_NAME)}\n"
        "---\n\n"
    )

    # Each chunk section is a self-contained unit for RAG ingestion.
    # The header encodes position, time range, and token count so a retriever can
    # reconstruct context without loading the full document.
    total = len(chunks)
    chunk_sections: list[str] = []
    for chunk in chunks:
        start_ts = format_timestamp(chunk.start_seconds)
        end_ts = format_timestamp(chunk.end_seconds)
        header = f"### Chunk {chunk.index}/{total} · {start_ts} – {end_ts} · {chunk.token_count} tokens"
        chunk_sections.append(f"{header}\n\n{chunk.text}")

    chunks_block = (
        "\n\n---\n\n".join(chunk_sections) if chunk_sections else "_Nenhuma fala detectada._"
    )

    # Fine-grained timestamp list preserved for human review and time-aligned search.
    timestamp_lines = [
        f"- [{format_timestamp(s.start_seconds)} - {format_timestamp(s.end_seconds)}] {s.text}"
        for s in result.segments
    ]
    timestamps_block = (
        "\n".join(timestamp_lines) if timestamp_lines else "- Nenhum trecho de fala detectado."
    )

    return (
        frontmatter
        + f"# Transcrição de {video_path.name}\n\n"
        + "## Chunks\n\n"
        + chunks_block
        + "\n\n"
        + "## Trechos com timestamps\n\n"
        + timestamps_block
        + "\n"
    )


def format_timestamp(total_seconds: float) -> str:
    bounded_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(bounded_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main(argv: list[str] | None = None) -> int:
    settings = parse_args(argv)
    configure_logging(settings.log_file)
    try:
        summary = run(settings)
    except Exception:
        logging.exception("Execução encerrada com erro")
        return 1

    return 0 if not summary.failed_files else 2
