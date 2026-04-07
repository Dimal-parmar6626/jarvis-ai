"""Pydantic schemas for voice endpoints."""

from typing import Optional

from pydantic import BaseModel


class VoiceProcessResponse(BaseModel):
    """Response from audio processing."""

    transcript: str
    intent: str
    confidence: float
    response_text: str
    audio_response: Optional[str] = None  # base64-encoded audio


class VoiceStreamMessage(BaseModel):
    """WebSocket message for real-time voice streaming."""

    type: str  # "transcript" | "response" | "error"
    content: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
