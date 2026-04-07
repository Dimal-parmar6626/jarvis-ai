"""Tasks routes: execute and schedule tasks."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.routes.deps import get_current_user
from app.core.task_executor import TaskExecutor
from app.database.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.command import TaskExecuteRequest, TaskListResponse, TaskResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])

_executor = TaskExecutor()


@router.post("/execute", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def execute_task(
    payload: TaskExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a task immediately or schedule it."""
    task = Task(
        user_id=current_user.id,
        name=payload.name or payload.task_type,
        description=payload.description,
        task_type=payload.task_type,
        payload=json.dumps(payload.payload),
        status="running",
        scheduled_at=payload.schedule_at,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    result: dict = {}
    try:
        if payload.task_type == "open_app":
            result = _executor.open_application(payload.payload.get("app", ""))
        elif payload.task_type == "system_info":
            result = _executor.get_system_info()
        elif payload.task_type == "file_create":
            result = _executor.create_file(
                payload.payload.get("path", ""),
                payload.payload.get("content", ""),
            )
        elif payload.task_type == "file_read":
            result = _executor.read_file(payload.payload.get("path", ""))
        elif payload.task_type == "file_delete":
            result = _executor.delete_file(payload.payload.get("path", ""))
        elif payload.task_type == "list_dir":
            result = _executor.list_directory(payload.payload.get("path", "."))
        else:
            result = {"success": False, "error": f"Unknown task type: {payload.task_type}"}
    except Exception as exc:  # pylint: disable=broad-except
        result = {"success": False, "error": str(exc)}

    task.status = "done" if result.get("success") else "failed"
    task.result = json.dumps(result)
    task.executed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


@router.get("/scheduled", response_model=TaskListResponse)
def list_scheduled_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List scheduled (pending) tasks for the current user."""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.id, Task.status == "pending")
        .order_by(Task.scheduled_at)
        .all()
    )
    return TaskListResponse(items=tasks, total=len(tasks))


@router.get("", response_model=TaskListResponse)
def list_tasks(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tasks for the current user."""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .all()
    )
    return TaskListResponse(items=tasks, total=len(tasks))
