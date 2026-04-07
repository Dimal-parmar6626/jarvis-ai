"""Chat routes: send messages and retrieve history."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.routes.deps import get_current_user
from app.core.conversation_memory import ConversationMemory
from app.core.nlp_engine import NLPEngine
from app.database.session import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationHistoryItem,
    ConversationHistoryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

_nlp = NLPEngine()
_memory = ConversationMemory()

_RESPONSES = {
    "greeting": "Hello! I'm Jarvis, your AI assistant. How can I help?",
    "farewell": "Goodbye! Have a great day!",
    "weather": "I can check the weather. Which city?",
    "news": "Fetching the latest headlines for you.",
    "search": "I'll search that right away.",
    "calendar": "What calendar action would you like to perform?",
    "email": "I can help with email. What would you like to do?",
    "music": "What would you like to play?",
    "timer": "How long should I set the timer for?",
    "smart_home": "Which device would you like to control?",
    "help": "I can help with weather, news, search, calendar, email, smart home, timers, and more!",
    "joke": "Why don't scientists trust atoms? Because they make up everything! 😄",
    "calculate": "Please share the calculation you need.",
    "unknown": "I'm not sure how to help with that. Type 'help' to see what I can do.",
}


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process a text message and return a response."""
    result = _nlp.process(payload.message)

    # Store user message
    _memory.add_message(payload.session_id, "user", payload.message, {"intent": result.intent})
    _memory.save_to_db(db, current_user.id, payload.session_id, "user", payload.message, result.intent)

    # Build response
    response_text = _RESPONSES.get(result.intent, _RESPONSES["unknown"])

    _memory.add_message(payload.session_id, "assistant", response_text)
    _memory.save_to_db(db, current_user.id, payload.session_id, "assistant", response_text)

    return ChatMessageResponse(
        message=response_text,
        intent=result.intent,
        confidence=result.confidence,
        session_id=payload.session_id,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/history", response_model=ConversationHistoryResponse)
def get_history(
    session_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve conversation history for the current user."""
    records = _memory.load_from_db(db, current_user.id, session_id=session_id, limit=limit)
    items = [ConversationHistoryItem.model_validate(r) for r in records]
    return ConversationHistoryResponse(items=items, total=len(items), session_id=session_id)
