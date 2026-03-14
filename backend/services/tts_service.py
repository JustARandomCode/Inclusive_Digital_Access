from gtts import gTTS
import asyncio
import os
import tempfile
import base64
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {"en": "en", "hi": "hi", "mr": "mr"}


class TTSService:

    def _generate_sync(self, text: str, lang_code: str) -> Tuple[str, str]:
        """Blocking gTTS call — must run in executor."""
        tts = gTTS(text=text, lang=lang_code, slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            path = f.name
        try:
            tts.save(path)
            with open(path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("utf-8")
            return audio_b64, "audio/mp3"
        finally:
            if os.path.exists(path):
                os.unlink(path)

    async def generate_speech(self, text: str, language: str = "en") -> Tuple[str, str]:
        lang_code = LANGUAGE_MAP.get(language, "en")
        loop = asyncio.get_event_loop()
        audio_b64, mime = await loop.run_in_executor(
            None, self._generate_sync, text, lang_code
        )
        logger.info(f"TTS generated for language: {lang_code}")
        return audio_b64, mime


tts_service = TTSService()
