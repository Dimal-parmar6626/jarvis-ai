"""Voice processing routes."""

import base64
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.routes.deps import get_current_user
from app.core.nlp_engine import NLPEngine
from app.core.speech_engine import SpeechEngine
from app.models.user import User
from app.schemas.voice import VoiceProcessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

_speech = SpeechEngine()
_nlp = NLPEngine()


@router.post("/process", response_model=VoiceProcessResponse)
async def process_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Process an uploaded audio file: transcribe and return NLP result."""
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="Uploaded file must be an audio file.")

    audio_bytes = await audio.read()
    transcript = _speech.transcribe_audio_bytes(audio_bytes)
    if not transcript:
        raise HTTPException(status_code=422, detail="Could not transcribe audio. Please try again.")

    nlp_result = _nlp.process(transcript)

    # Generate TTS audio response
    response_text = f"I understood: {transcript}. Intent detected: {nlp_result.intent}."
    audio_response_bytes = _speech.synthesize_to_bytes(response_text)
    audio_b64 = base64.b64encode(audio_response_bytes).decode() if audio_response_bytes else None

    return VoiceProcessResponse(
        transcript=transcript,
        intent=nlp_result.intent,
        confidence=nlp_result.confidence,
        response_text=response_text,
        audio_response=audio_b64,
    )


@router.post("/synthesize")
async def synthesize_text(
    text: str,
    current_user: User = Depends(get_current_user),
):
    """Convert text to speech and return base64-encoded MP3."""
    audio_bytes = _speech.synthesize_to_bytes(text)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Speech synthesis failed.")
    return {"audio": base64.b64encode(audio_bytes).decode(), "format": "mp3"}
