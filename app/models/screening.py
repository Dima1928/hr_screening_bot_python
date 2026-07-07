from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RecommendationStatus(StrEnum):
    SUITABLE = "подходит"
    NOT_SUITABLE = "не подходит"
    NEEDS_CLARIFICATION = "требуется уточнение"


class BotStage(StrEnum):
    IN_PROGRESS = "in_progress"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"
    INTERVIEW_PLANNED = "interview_planned"


class ScreeningAnalysis(BaseModel):
    status: RecommendationStatus
    score: int = Field(ge=0, le=100)
    summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    next_question: str | None = None
    feedback: str | None = None


class InterviewSlot(BaseModel):
    slot_id: str
    starts_at: str
    ends_at: str
    recruiter: str


class WebhookRequest(BaseModel):
    candidate_id: str = Field(..., examples=["cand-123"])
    candidate_name: str | None = Field(default=None, examples=["Иван Петров"])
    vacancy_id: str = Field(default="python_backend", examples=["python_backend"])
    text: str = Field(..., examples=["Здравствуйте, хочу откликнуться на вакансию"])
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    candidate_id: str
    vacancy_id: str
    stage: BotStage
    reply: str
    recommendation: ScreeningAnalysis | None = None
    interview_slots: list[InterviewSlot] = Field(default_factory=list)
