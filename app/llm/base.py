from abc import ABC, abstractmethod

from app.models.message import ConversationMessage
from app.models.screening import ScreeningAnalysis
from app.models.vacancy import Vacancy


class LLMClient(ABC):
    @abstractmethod
    async def next_question(
        self,
        vacancy: Vacancy,
        history: list[ConversationMessage],
        candidate_name: str | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def analyze_candidate(
        self,
        vacancy: Vacancy,
        history: list[ConversationMessage],
    ) -> ScreeningAnalysis:
        raise NotImplementedError
