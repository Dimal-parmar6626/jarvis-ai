"""Commands routes: list built-in commands and manage custom commands."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.deps import get_current_user
from app.database.session import get_db
from app.models.command import Command
from app.models.user import User
from app.schemas.command import CommandCreate, CommandListResponse, CommandResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/commands", tags=["commands"])

# Built-in command catalogue
BUILTIN_COMMANDS = [
    {"name": "Weather", "trigger": "what's the weather in {city}", "description": "Get current weather for a city."},
    {"name": "News", "trigger": "what's in the news", "description": "Fetch top headlines."},
    {"name": "Search", "trigger": "search for {query}", "description": "Web search via Google."},
    {"name": "Wikipedia", "trigger": "tell me about {topic}", "description": "Wikipedia summary."},
    {"name": "Set Timer", "trigger": "set a timer for {duration}", "description": "Start a countdown timer."},
    {"name": "Open App", "trigger": "open {app}", "description": "Launch an application."},
    {"name": "Send Email", "trigger": "send email to {name}", "description": "Compose and send an email."},
    {"name": "Calendar Events", "trigger": "what's on my calendar", "description": "List upcoming events."},
    {"name": "Smart Home", "trigger": "turn on/off {device}", "description": "Control smart home devices."},
    {"name": "System Info", "trigger": "system status", "description": "Get CPU, memory, and disk usage."},
    {"name": "Joke", "trigger": "tell me a joke", "description": "Hear a joke."},
    {"name": "Help", "trigger": "help", "description": "List available commands."},
]


@router.get("", response_model=dict)
def list_commands():
    """List all built-in commands."""
    return {"built_in": BUILTIN_COMMANDS, "total": len(BUILTIN_COMMANDS)}


@router.post("/custom", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
def create_custom_command(
    payload: CommandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a custom command for the current user."""
    cmd = Command(
        user_id=current_user.id,
        name=payload.name,
        trigger=payload.trigger,
        action=payload.action,
        description=payload.description,
    )
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    logger.info("Custom command created: id=%d user=%s", cmd.id, current_user.username)
    return cmd


@router.get("/custom", response_model=CommandListResponse)
def list_custom_commands(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all custom commands for the current user."""
    cmds = db.query(Command).filter(Command.user_id == current_user.id, Command.is_active.is_(True)).all()
    return CommandListResponse(items=cmds, total=len(cmds))


@router.delete("/custom/{command_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_command(
    command_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a custom command."""
    cmd = db.query(Command).filter(Command.id == command_id, Command.user_id == current_user.id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found.")
    db.delete(cmd)
    db.commit()
    logger.info("Custom command deleted: id=%d", command_id)
