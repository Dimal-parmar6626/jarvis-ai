"""User preferences routes."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.command import UserPreferences

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["user"])


@router.get("/preferences", response_model=UserPreferences)
def get_preferences(current_user: User = Depends(get_current_user)):
    """Retrieve current user preferences."""
    try:
        prefs = json.loads(current_user.preferences or "{}")
    except json.JSONDecodeError:
        prefs = {}
    return UserPreferences(**prefs)


@router.put("/preferences", response_model=UserPreferences)
def update_preferences(
    payload: UserPreferences,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user preferences."""
    current_user.preferences = payload.model_dump_json()
    db.commit()
    db.refresh(current_user)
    return payload


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }
