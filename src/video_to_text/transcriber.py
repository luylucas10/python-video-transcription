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
        initial_prompt: str | None = None,
        no_speech_threshold: float = 0.6,
        compression_ratio_threshold: float = 2.4,
        log_prob_threshold: float = -1.0,
        temperature: float = 0.0,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.beam_size = beam_size
        self.batch_size = batch_size
        self.vad_filter = vad_filter
        self.download_root = download_root
        self.initial_prompt = initial_prompt
        self.no_speech_threshold = no_speech_threshold
        self.compression_ratio_threshold = compression_ratio_threshold
        self.log_prob_threshold = log_prob_threshold
        self.temperature = temperature
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

        common_kwargs = {
            "beam_size": self.beam_size,
            "language": self.language,
            "task": "transcribe",
            "vad_filter": self.vad_filter,
            "initial_prompt": self.initial_prompt,
            "no_speech_threshold": self.no_speech_threshold,
            "compression_ratio_threshold": self.compression_ratio_threshold,
            "log_prob_threshold": self.log_prob_threshold,
            "temperature": self.temperature,
        }

        if self._use_batched:
            segments, info = self._active.transcribe(
                str(video_path),
                batch_size=self.batch_size,
                **common_kwargs,
            )
        else:
            segments, info = self._active.transcribe(
                str(video_path),
                condition_on_previous_text=True,
                **common_kwargs,
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

