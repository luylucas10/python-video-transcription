from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True, slots=True)
class TranscriptResult:
    model_name: str
    language: str | None
    language_probability: float | None
    duration_seconds: float | None
    segments: list[TranscriptSegment]


class Transcriber(Protocol):
    def transcribe(self, video_path: Path) -> TranscriptResult:
        ...


class FasterWhisperTranscriber:
    def __init__(
        self,
        *,
        model_name: str,
        device: str,
        compute_type: str,
        language: str | None,
        beam_size: int,
        batch_size: int,
        vad_filter: bool,
        download_root: Path,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.beam_size = beam_size
        self.batch_size = batch_size
        self.vad_filter = vad_filter
        self.download_root = download_root
        self._active: Any = None
        self._use_batched: bool = False

    def _ensure_loaded(self) -> None:
        if self._active is not None:
            return

        faster_whisper = importlib.import_module("faster_whisper")
        WhisperModel = getattr(faster_whisper, "WhisperModel")
        # BatchedInferencePipeline is available in faster-whisper >= 1.0
        BatchedInferencePipeline = getattr(faster_whisper, "BatchedInferencePipeline", None)

        self.download_root.mkdir(parents=True, exist_ok=True)
        model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
            download_root=str(self.download_root),
        )

        if BatchedInferencePipeline is not None and self.batch_size > 1:
            # Process multiple audio chunks in parallel — significant speedup on RTX 3090 (24 GB VRAM)
            self._active = BatchedInferencePipeline(model=model)
            self._use_batched = True
        else:
            self._active = model
            self._use_batched = False

    @staticmethod
    def _to_float_or_none(value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    def transcribe(self, video_path: Path) -> TranscriptResult:
        self._ensure_loaded()

        if self._use_batched:
            segments, info = self._active.transcribe(
                str(video_path),
                batch_size=self.batch_size,
                beam_size=self.beam_size,
                language=self.language,
                task="transcribe",
                vad_filter=self.vad_filter,
            )
        else:
            segments, info = self._active.transcribe(
                str(video_path),
                beam_size=self.beam_size,
                language=self.language,
                task="transcribe",
                vad_filter=self.vad_filter,
                condition_on_previous_text=True,
            )

        collected_segments = [
            TranscriptSegment(
                start_seconds=float(segment.start),
                end_seconds=float(segment.end),
                text=segment.text.strip(),
            )
            for segment in segments
            if segment.text.strip()
        ]
        return TranscriptResult(
            model_name=self.model_name,
            language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
            duration_seconds=self._to_float_or_none(getattr(info, "duration", None)),
            segments=collected_segments,
        )

