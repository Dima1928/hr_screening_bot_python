import re

from app.llm.base import LLMClient
from app.models.message import ConversationMessage, MessageRole
from app.models.screening import BotStage, RecommendationStatus, WebhookRequest, WebhookResponse
from app.repositories.history import InMemoryHistoryRepository
from app.repositories.vacancy import JsonVacancyRepository
from app.scheduler.calendar import CalendarSimulator


class ScreeningProcessor:
    def __init__(
        self,
        vacancy_repository: JsonVacancyRepository,
        history_repository: InMemoryHistoryRepository,
        llm_client: LLMClient,
        calendar: CalendarSimulator,
        min_screening_questions: int = 4,
    ) -> None:
        self.vacancy_repository = vacancy_repository
        self.history_repository = history_repository
        self.llm_client = llm_client
        self.calendar = calendar
        self.min_screening_questions = min_screening_questions

    async def process(self, request: WebhookRequest) -> WebhookResponse:
        vacancy = self.vacancy_repository.get(request.vacancy_id)
        self.history_repository.add(
            request.candidate_id,
            ConversationMessage(role=MessageRole.CANDIDATE, text=request.text),
        )
        history = self.history_repository.list(request.candidate_id)

        selected_slot_id = self._extract_slot_id(request.text)
        if selected_slot_id:
            slots = self.calendar.get_free_slots(vacancy, count=6)
            selected_slot = next((slot for slot in slots if slot.slot_id == selected_slot_id), None)
            if selected_slot:
                self.calendar.book(selected_slot)
                reply = (
                    "Готово, интервью запланировано. "
                    f"Слот: {selected_slot.starts_at} — {selected_slot.ends_at}."
                )
                self._add_bot_reply(request.candidate_id, reply)
                return WebhookResponse(
                    candidate_id=request.candidate_id,
                    vacancy_id=request.vacancy_id,
                    stage=BotStage.INTERVIEW_PLANNED,
                    reply=reply,
                    interview_slots=[selected_slot],
                )

        if self._bot_questions_count(history) < self.min_screening_questions:
            question = await self.llm_client.next_question(vacancy, history, request.candidate_name)
            self._add_bot_reply(request.candidate_id, question)
            return WebhookResponse(
                candidate_id=request.candidate_id,
                vacancy_id=request.vacancy_id,
                stage=BotStage.IN_PROGRESS,
                reply=question,
            )

        analysis = await self.llm_client.analyze_candidate(vacancy, history)

        if analysis.status == RecommendationStatus.SUITABLE:
            slots = self.calendar.get_free_slots(vacancy)
            slot_lines = "\n".join(
                f"- {slot.slot_id}: {slot.starts_at} — {slot.ends_at}" for slot in slots
            )
            reply = (
                "Спасибо за ответы. По результатам первичного скрининга вы подходите "
                f"для вакансии «{vacancy.title}».\n\n"
                "Можем запланировать интервью с рекрутером. Доступные слоты:\n"
                f"{slot_lines}\n\n"
                "Напишите id подходящего слота, например: slot-202607081000."
            )
            stage = BotStage.QUALIFIED
            response_slots = slots
        elif analysis.status == RecommendationStatus.NOT_SUITABLE:
            reply = analysis.feedback or (
                "Спасибо за уделенное время. Сейчас ваш опыт не полностью совпадает "
                "с базовыми требованиями вакансии, поэтому мы не готовы пригласить вас "
                "на следующий этап."
            )
            stage = BotStage.REJECTED
            response_slots = []
        else:
            reply = analysis.next_question or "Уточните, пожалуйста, ваш опыт по ключевым требованиям вакансии."
            stage = BotStage.NEEDS_CLARIFICATION
            response_slots = []

        self._add_bot_reply(request.candidate_id, reply)
        return WebhookResponse(
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id,
            stage=stage,
            reply=reply,
            recommendation=analysis,
            interview_slots=response_slots,
        )

    def _add_bot_reply(self, candidate_id: str, reply: str) -> None:
        self.history_repository.add(candidate_id, ConversationMessage(role=MessageRole.BOT, text=reply))

    @staticmethod
    def _bot_questions_count(history: list[ConversationMessage]) -> int:
        return sum(1 for message in history if message.role == MessageRole.BOT and "?" in message.text)

    @staticmethod
    def _extract_slot_id(text: str) -> str | None:
        match = re.search(r"slot-\d{12}", text)
        return match.group(0) if match else None
