"""Models package init – import all models so Alembic can detect them."""

from app.models.command import Command  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.user import User  # noqa: F401
