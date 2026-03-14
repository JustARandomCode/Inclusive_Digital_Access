from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from models import VoiceInput, SimplificationRequest, SimplificationResponse, TTSRequest, TTSResponse
from services.stt_service import stt_service
from services.llm_service import llm_service
from services.tts_service import tts_service
from routers.auth import verify_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB hard limit
ALLOWED_MIME_PREFIXES = ("audio/",)


@router.post("/transcribe", response_model=VoiceInput)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Query(default="en"),
    username: str = Depends(verify_token),
):
    # Validate content type before reading the full file
    content_type = audio.content_type or ""
    if not any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Send an audio file.",
        )

    audio_data = await audio.read()

    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    if len(audio_data) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Maximum size is {MAX_AUDIO_BYTES // (1024*1024)}MB",
        )

    try:
        text, confidence = await stt_service.transcribe_audio(audio_data, language)
        return VoiceInput(text=text, language=language, confidence=confidence)
    except Exception as e:
        logger.error(f"Transcription error for user {username}: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Speech transcription failed")


@router.post("/simplify", response_model=SimplificationResponse)
async def simplify_text(
    request: SimplificationRequest,
    username: str = Depends(verify_token),
):
    try:
        simplified = await llm_service.simplify_text(request.text, request.language)
        return SimplificationResponse(
            original_text=request.text,
            simplified_text=simplified,
            language=request.language,
        )
    except Exception as e:
        logger.error(f"Simplification error for user {username}: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Text simplification failed")


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(
    request: TTSRequest,
    username: str = Depends(verify_token),
):
    try:
        audio_base64, mime_type = await tts_service.generate_speech(
            request.text, request.language
        )
        return TTSResponse(
            audio_url=f"data:{mime_type};base64,{audio_base64}",
            language=request.language,
        )
    except Exception as e:
        logger.error(f"TTS error for user {username}: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")
