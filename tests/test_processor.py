import pytest

from app.llm.stub import StubLLMClient
from app.models.screening import BotStage, WebhookRequest
from app.repositories.history import InMemoryHistoryRepository
from app.repositories.vacancy import JsonVacancyRepository
from app.scheduler.calendar import CalendarSimulator
from app.services.processor import ScreeningProcessor


@pytest.mark.asyncio
async def test_processor_asks_first_question() -> None:
    processor = ScreeningProcessor(
        vacancy_repository=JsonVacancyRepository("app/data/vacancies.json"),
        history_repository=InMemoryHistoryRepository(),
        llm_client=StubLLMClient(),
        calendar=CalendarSimulator(),
        min_screening_questions=4,
    )

    response = await processor.process(
        WebhookRequest(
            candidate_id="cand-1",
            candidate_name="Иван",
            vacancy_id="python_backend",
            text="Здравствуйте, хочу откликнуться",
        )
    )

    assert response.stage == BotStage.IN_PROGRESS
    assert "опыт" in response.reply.lower()


@pytest.mark.asyncio
async def test_processor_returns_slots_for_suitable_candidate_after_screening() -> None:
    processor = ScreeningProcessor(
        vacancy_repository=JsonVacancyRepository("app/data/vacancies.json"),
        history_repository=InMemoryHistoryRepository(),
        llm_client=StubLLMClient(),
        calendar=CalendarSimulator(),
        min_screening_questions=2,
    )

    messages = [
        "У меня 4 года опыта Python, FastAPI, REST API, SQL, Docker, Git.",
        "Работал с микросервисами, pytest и Redis. Ожидания 180 тыс, готов выйти через 2 недели.",
        "Дополнительно делал интеграции и внутренние сервисы.",
    ]

    last_response = None
    for text in messages:
        last_response = await processor.process(
            WebhookRequest(candidate_id="cand-2", vacancy_id="python_backend", text=text)
        )

    assert last_response is not None
    assert last_response.stage == BotStage.QUALIFIED
    assert last_response.recommendation is not None
    assert last_response.recommendation.score >= 70
    assert len(last_response.interview_slots) == 3


@pytest.mark.asyncio
async def test_processor_rejects_weak_candidate() -> None:
    processor = ScreeningProcessor(
        vacancy_repository=JsonVacancyRepository("app/data/vacancies.json"),
        history_repository=InMemoryHistoryRepository(),
        llm_client=StubLLMClient(),
        calendar=CalendarSimulator(),
        min_screening_questions=2,
    )

    messages = [
        "Опыта в Python нет, хочу попробовать себя в IT.",
        "Docker, SQL и API не знаю. Ожидания 200 тыс.",
        "Готов учиться с нуля.",
    ]

    last_response = None
    for text in messages:
        last_response = await processor.process(
            WebhookRequest(candidate_id="cand-3", vacancy_id="python_backend", text=text)
        )

    assert last_response is not None
    assert last_response.stage == BotStage.REJECTED
    assert last_response.recommendation is not None
    assert last_response.recommendation.feedback is not None
