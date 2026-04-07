"""Status route: system health and statistics."""

import logging
import platform
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.deps import get_current_user
from app.config import settings
from app.database.session import get_db
from app.models.conversation import Conversation
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return system status and usage statistics."""
    total_conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_tasks = db.query(Task).filter(Task.user_id == current_user.id).count()

    system_info: dict = {
        "os": platform.system(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
    }
    try:
        import psutil  # type: ignore

        system_info["cpu_percent"] = psutil.cpu_percent(interval=0.2)
        system_info["memory_percent"] = psutil.virtual_memory().percent
        system_info["disk_percent"] = psutil.disk_usage("/").percent
    except Exception:  # pylint: disable=broad-except
        pass

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": current_user.username,
        "statistics": {
            "total_conversations": total_conversations,
            "total_tasks": total_tasks,
        },
        "system": system_info,
        "services": {
            "weather": bool(settings.OPENWEATHER_API_KEY),
            "news": bool(settings.NEWS_API_KEY),
            "google_search": bool(settings.GOOGLE_API_KEY and settings.GOOGLE_CSE_ID),
            "calendar": bool(settings.GOOGLE_CREDENTIALS_FILE),
            "email": bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD),
            "smart_home": bool(settings.HOME_ASSISTANT_URL and settings.HOME_ASSISTANT_TOKEN),
        },
    }
