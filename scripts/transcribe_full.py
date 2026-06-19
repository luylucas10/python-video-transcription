"""
transcribe_full.py — Transcrição completa de um único vídeo, sem tokenização.

Gera um arquivo .md com:
  - Frontmatter YAML com metadados básicos
  - Texto corrido da transcrição (sem divisão em chunks)
  - Seção de trechos com timestamps por segmento

Uso:
    python scripts/transcribe_full.py <caminho_do_video> [opções]

Exemplos:
    python scripts/transcribe_full.py E:\\obs\\aula.mp4
    python scripts/transcribe_full.py E:\\obs\\aula.mp4 --output E:\\transcrições\\aula.md
    python scripts/transcribe_full.py E:\\obs\\aula.mp4 --model large-v3 --language pt
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve o caminho do pacote video_to_text quando executado direto
# (sem instalar o pacote — apenas com o venv ativo).
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from video_to_text.transcriber import FasterWhisperTranscriber, TranscriptResult  # noqa: E402

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "large-v3"
DEFAULT_LANGUAGE = "pt"
DEFAULT_BATCH_SIZE = 16
MODEL_CACHE_DIR = Path.home() / ".cache" / "video-to-text" / "models"


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------

def _fmt_ts(total_seconds: float) -> str:
    """Converte segundos para HH:MM:SS."""
    bounded = max(0, int(total_seconds))
    h, remainder = divmod(bounded, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _yaml_str(value: str) -> str:
    """Envolve value em aspas duplas YAML, escapando barras e aspas."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# Geração do markdown
# ---------------------------------------------------------------------------

def build_markdown(
    video_path: Path,
    result: TranscriptResult,
    started_at: datetime,
    finished_at: datetime,
) -> str:
    language = result.language or "desconhecido"
    language_confidence = (
        f"{result.language_probability:.4f}"
        if result.language_probability is not None
        else "null"
    )
    duration = (
        _fmt_ts(result.duration_seconds)
        if result.duration_seconds is not None
        else "null"
    )
    duration_seconds_val = (
        f"{result.duration_seconds:.3f}"
        if result.duration_seconds is not None
        else "null"
    )
    segment_count = len(result.segments)

    # Frontmatter YAML com metadados de proveniência
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
        f"segment_count: {segment_count}\n"
        "---\n\n"
    )

    # Texto corrido — todos os segmentos concatenados em parágrafos naturais.
    # A quebra de linha dupla acontece quando há uma pausa longa (> 2 s) entre segmentos,
    # criando parágrafos que respeitam o ritmo da fala.
    paragraphs: list[str] = []
    current: list[str] = []
    previous_end: float | None = None
    PAUSE_THRESHOLD = 2.0

    for seg in result.segments:
        if previous_end is not None and (seg.start_seconds - previous_end) > PAUSE_THRESHOLD:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        current.append(seg.text)
        previous_end = seg.end_seconds

    if current:
        paragraphs.append(" ".join(current))

    full_text = "\n\n".join(paragraphs) if paragraphs else "_Nenhuma fala detectada._"

    # Timestamps granulares por segmento para referência humana e busca time-aligned
    timestamp_lines = [
        f"- [{_fmt_ts(s.start_seconds)} – {_fmt_ts(s.end_seconds)}] {s.text}"
        for s in result.segments
    ]
    timestamps_block = (
        "\n".join(timestamp_lines) if timestamp_lines else "- Nenhum trecho de fala detectado."
    )

    return (
        frontmatter
        + f"# Transcrição de {video_path.name}\n\n"
        + "## Texto completo\n\n"
        + full_text
        + "\n\n"
        + "## Trechos com timestamps\n\n"
        + timestamps_block
        + "\n"
    )


# ---------------------------------------------------------------------------
# Escrita atômica
# ---------------------------------------------------------------------------

def write_markdown(output_path: Path, content: str) -> None:
    """Escreve *content* em *output_path* via arquivo temporário para evitar corrupção."""
    tmp = output_path.with_suffix(f"{output_path.suffix}.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(output_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcreve um único vídeo MP4 para Markdown sem tokenização.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "video",
        type=Path,
        help="Caminho para o arquivo de vídeo .mp4",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Arquivo de saída .md (padrão: mesmo diretório e nome do vídeo)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Modelo faster-whisper (padrão: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help=f"Idioma da transcrição (padrão: {DEFAULT_LANGUAGE}). Use 'auto' para detecção automática.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Chunks de áudio em paralelo na GPU (padrão: {DEFAULT_BATCH_SIZE} para RTX 3090)",
    )
    return parser.parse_args(argv)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Suprime logs de HTTP do HuggingFace durante download do modelo
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    args = parse_args(argv)

    video_path: Path = args.video.resolve()
    if not video_path.exists():
        logging.error("Arquivo não encontrado: %s", video_path)
        return 1
    if not video_path.is_file():
        logging.error("Caminho não é um arquivo: %s", video_path)
        return 1

    output_path: Path = (
        args.output.resolve()
        if args.output
        else video_path.with_suffix(".md")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    language: str | None = (
        None if args.language.lower() in ("auto", "") else args.language
    )

    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    transcriber = FasterWhisperTranscriber(
        model_name=args.model,
        device="cuda",
        # float16 usa diretamente os tensor cores da RTX 3090 sem conversão
        compute_type="float16",
        language=language,
        beam_size=5,
        batch_size=args.batch_size,
        vad_filter=True,
        download_root=MODEL_CACHE_DIR,
    )

    logging.info("Transcrevendo: %s", video_path.name)
    logging.info("Modelo: %s | Idioma: %s | Saída: %s", args.model, language or "auto", output_path)

    started_at = datetime.now(UTC)
    try:
        result: TranscriptResult = transcriber.transcribe(video_path)
    except Exception:
        logging.exception("Falha ao transcrever %s", video_path)
        return 1

    finished_at = datetime.now(UTC)
    elapsed = (finished_at - started_at).total_seconds()

    content = build_markdown(video_path, result, started_at, finished_at)
    write_markdown(output_path, content)

    duration_str = _fmt_ts(result.duration_seconds) if result.duration_seconds else "?"
    logging.info(
        "Concluído em %.1fs | Duração do vídeo: %s | %d segmentos | Saída: %s",
        elapsed,
        duration_str,
        len(result.segments),
        output_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

