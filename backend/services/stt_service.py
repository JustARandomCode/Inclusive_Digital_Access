from faster_whisper import WhisperModel
import asyncio
import os
import subprocess
import tempfile
from typing import Tuple, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class STTService:
    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self.model_name = settings.whisper_model
        self._lock = asyncio.Lock()

    def _load_model_sync(self):
        """Blocking model load — must be run in a thread executor."""
        logger.info(f"Loading Whisper model: {self.model_name}")
        self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded")

    async def load_model(self):
        """Called once at application startup from the lifespan event."""
        async with self._lock:
            if self.model is None:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._load_model_sync)

    def _convert_to_wav(self, audio_bytes: bytes, source_suffix: str) -> str:
        """
        Use ffmpeg to convert any browser audio format (webm, ogg, mp4, etc.)
        to a 16kHz mono WAV that Whisper expects.
        Returns path to the temporary WAV file — caller must delete it.
        """
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=source_suffix
        ) as src_file:
            src_file.write(audio_bytes)
            src_path = src_file.name

        wav_path = src_path.replace(source_suffix, ".wav")
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", src_path,
                    "-ar", "16000",   # 16kHz — Whisper's native rate
                    "-ac", "1",       # mono
                    "-f", "wav",
                    wav_path,
                ],
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg conversion failed: {result.stderr.decode()}"
                )
            return wav_path
        finally:
            os.unlink(src_path)

    def _transcribe_sync(self, wav_path: str, language: Optional[str]) -> Tuple[str, float]:
        assert self.model is not None
        segments, info = self.model.transcribe(
            wav_path,
            language=language or None,
            beam_size=5,
        )
        text = " ".join(seg.text for seg in segments).strip()
        return text, info.language_probability

    async def transcribe_audio(
        self, audio_bytes: bytes, language: Optional[str] = None
    ) -> Tuple[str, float]:
        if self.model is None:
            raise RuntimeError("STT model not loaded. Call load_model() at startup.")

        loop = asyncio.get_event_loop()

        # Conversion is CPU/subprocess — run off the event loop
        wav_path = await loop.run_in_executor(
            None, self._convert_to_wav, audio_bytes, ".webm"
        )

        try:
            text, confidence = await loop.run_in_executor(
                None, self._transcribe_sync, wav_path, language
            )
            logger.info(f"Transcription done: {text[:60]}...")
            return text, confidence
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)


stt_service = STTService()
