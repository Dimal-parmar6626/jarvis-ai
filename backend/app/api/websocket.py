"""WebSocket endpoint for real-time voice/chat streaming."""

import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.conversation_memory import ConversationMemory
from app.core.nlp_engine import NLPEngine
from app.core.speech_engine import SpeechEngine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

_nlp = NLPEngine()
_speech = SpeechEngine()
_memory = ConversationMemory()


@router.websocket("/voice/stream")
async def voice_stream(websocket: WebSocket):
    """Real-time voice streaming over WebSocket.

    Client can send JSON messages with type:
    - ``{"type": "text", "content": "..."}``  – text message
    - ``{"type": "audio", "data": "<base64>"}`` – raw audio bytes
    """
    await websocket.accept()
    session_id = str(id(websocket))
    logger.info("WebSocket connected: session=%s", session_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "text")

            if msg_type == "audio":
                # Decode base64 audio and transcribe
                audio_data = base64.b64decode(msg.get("data", ""))
                transcript = _speech.transcribe_audio_bytes(audio_data)
                if not transcript:
                    await websocket.send_json({"type": "error", "content": "Could not transcribe audio"})
                    continue
                await websocket.send_json({"type": "transcript", "content": transcript})
                text = transcript
            else:
                text = msg.get("content", "")

            if not text:
                continue

            # NLP processing
            result = _nlp.process(text)
            _memory.add_message(session_id, "user", text, {"intent": result.intent})

            response_text = _generate_response(result)
            _memory.add_message(session_id, "assistant", response_text)

            await websocket.send_json(
                {
                    "type": "response",
                    "content": response_text,
                    "intent": result.intent,
                    "confidence": result.confidence,
                }
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)
        _memory.clear_session(session_id)


def _generate_response(result) -> str:
    """Generate a simple text response based on intent."""
    intent = result.intent
    responses = {
        "greeting": "Hello! I'm Jarvis, your AI assistant. How can I help you?",
        "farewell": "Goodbye! Have a great day!",
        "weather": "I can check the weather for you. Please specify a city.",
        "news": "Let me fetch the latest news for you.",
        "search": "I'll search that for you.",
        "calendar": "I can manage your calendar. What would you like to do?",
        "email": "I can help you with email. What would you like to send or check?",
        "music": "I can control your music. What would you like to play?",
        "time": __import__("datetime").datetime.now().strftime("The current time is %H:%M on %A, %B %d, %Y."),
        "timer": "I'll set a timer for you. How long?",
        "smart_home": "I can control your smart home devices. What would you like to do?",
        "system": "I can open applications for you. Which one?",
        "file": "I can help with file operations.",
        "calculate": "Let me calculate that for you.",
        "joke": "Why don't scientists trust atoms? Because they make up everything! 😄",
        "help": "I can help with weather, news, search, calendar, email, smart home, music, and more!",
        "unknown": f"I heard you say: \"{result.text}\". I'm not sure how to help with that. Try asking about weather, news, or search.",
    }
    return responses.get(intent, responses["unknown"])
