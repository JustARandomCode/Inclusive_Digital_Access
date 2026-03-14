from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserInDB(BaseModel):
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=utcnow)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class VoiceInput(BaseModel):
    text: str
    language: str
    confidence: float


class FormField(BaseModel):
    field_name: str
    field_value: Any
    field_type: str


class Form(BaseModel):
    form_id: str
    form_type: str
    user_id: str
    fields: List[FormField]
    status: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SimplificationRequest(BaseModel):
    text: str
    language: str = "en"


class SimplificationResponse(BaseModel):
    original_text: str
    simplified_text: str
    language: str


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class TTSResponse(BaseModel):
    audio_url: str
    language: str


# Voice-to-form: text travels in the request body, never in URL query params
class VoiceFormRequest(BaseModel):
    text: str
    form_type: str


class MockServiceRequest(BaseModel):
    service_type: str
    action: str
    data: Dict[str, Any]


class MockServiceResponse(BaseModel):
    service_type: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
    timestamp: datetime = Field(default_factory=utcnow)


class RegisterRequest(BaseModel):
    username: str
    password: str
