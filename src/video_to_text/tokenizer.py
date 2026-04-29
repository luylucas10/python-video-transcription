from __future__ import annotations

import logging
from dataclasses import dataclass

from video_to_text.transcriber import TranscriptSegment

# cl100k_base is the BPE encoding used by GPT-4, GPT-3.5-turbo, and text-embedding-ada-002.
# It is also a reasonable approximation for other LLMs (Mistral, LLaMA, Claude).
ENCODING_NAME = "cl100k_base"

_encoder: object | None = None


class _FallbackEncoder:
    """Used when tiktoken is unavailable. Approximates 4 characters per token."""

    def encode(self, text: str) -> list[int]:
        return [0] * max(1, len(text) // 4)


def _get_encoder() -> object:
    global _encoder
    if _encoder is not None:
        return _encoder
    try:
        import tiktoken  # type: ignore[import-untyped]

        try:
            _encoder = tiktoken.get_encoding(ENCODING_NAME)
        except ValueError:
            # PyInstaller bundles don't preserve importlib.metadata entry points,
            # so the tiktoken plugin registry comes up empty. Construct the encoding
            # directly from tiktoken_ext, bypassing the registry entirely.
            from tiktoken_ext.openai_public import cl100k_base  # type: ignore[import-untyped]

            _encoder = tiktoken.Encoding(**cl100k_base())
    except Exception as exc:
        logging.warning(
            "tiktoken não disponível (%s) — contagem de tokens com estimativa (len/4). "
            "Instale com: pip install tiktoken",
            exc,
        )
        _encoder = _FallbackEncoder()
    return _encoder


def count_tokens(text: str) -> int:
    """Return the BPE token count for *text* using cl100k_base (GPT-4 compatible)."""
    return len(_get_encoder().encode(text))  # type: ignore[attr-defined]


@dataclass(frozen=True, slots=True)
class TranscriptChunk:
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    token_count: int


def build_chunks(segments: list[TranscriptSegment], max_tokens: int) -> list[TranscriptChunk]:
    """Group consecutive segments into chunks whose token count does not exceed *max_tokens*.

    Each chunk preserves the natural reading order and keeps segments contiguous in time,
    making the output suitable for direct ingestion into RAG pipelines.
    """
    if not segments:
        return []

    chunks: list[TranscriptChunk] = []
    buffer_texts: list[str] = []
    buffer_start = segments[0].start_seconds
    buffer_end = segments[0].end_seconds
    buffer_tokens = 0
    chunk_index = 1

    for segment in segments:
        seg_tokens = count_tokens(segment.text)
        if buffer_texts and buffer_tokens + seg_tokens > max_tokens:
            chunks.append(
                TranscriptChunk(
                    index=chunk_index,
                    start_seconds=buffer_start,
                    end_seconds=buffer_end,
                    text=" ".join(buffer_texts),
                    token_count=buffer_tokens,
                )
            )
            chunk_index += 1
            buffer_texts = [segment.text]
            buffer_start = segment.start_seconds
            buffer_tokens = seg_tokens
        else:
            buffer_texts.append(segment.text)
            buffer_tokens += seg_tokens
        buffer_end = segment.end_seconds

    if buffer_texts:
        chunks.append(
            TranscriptChunk(
                index=chunk_index,
                start_seconds=buffer_start,
                end_seconds=buffer_end,
                text=" ".join(buffer_texts),
                token_count=buffer_tokens,
            )
        )

    return chunks

