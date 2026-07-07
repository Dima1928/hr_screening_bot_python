from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    CANDIDATE = "candidate"
    BOT = "bot"


class ConversationMessage(BaseModel):
    role: MessageRole
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
