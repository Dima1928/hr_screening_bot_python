from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.llm.base import LLMClient
from app.llm.deepseek import DeepSeekClient
from app.llm.stub import StubLLMClient
from app.models.screening import WebhookRequest, WebhookResponse
from app.repositories.history import InMemoryHistoryRepository
from app.repositories.vacancy import JsonVacancyRepository, VacancyNotFoundError
from app.scheduler.calendar import CalendarSimulator
from app.services.processor import ScreeningProcessor

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="HR Screening Bot",
    description="Микросервис HR-бота для первичного скрининга кандидатов",
    version="1.0.0",
)


@lru_cache
def get_history_repository() -> InMemoryHistoryRepository:
    return InMemoryHistoryRepository()


@lru_cache
def get_vacancy_repository() -> JsonVacancyRepository:
    return JsonVacancyRepository(get_settings().vacancies_path)


@lru_cache
def get_calendar() -> CalendarSimulator:
    return CalendarSimulator()


@lru_cache
def get_llm_client() -> LLMClient:
    current_settings = get_settings()
    if current_settings.llm_mode == "deepseek":
        return DeepSeekClient(
            api_key=current_settings.llm_api_key,
            base_url=current_settings.llm_api_base_url,
            model=current_settings.llm_model,
            timeout_seconds=current_settings.llm_timeout_seconds,
        )
    return StubLLMClient()


def get_processor(
    vacancy_repository: JsonVacancyRepository = Depends(get_vacancy_repository),
    history_repository: InMemoryHistoryRepository = Depends(get_history_repository),
    llm_client: LLMClient = Depends(get_llm_client),
    calendar: CalendarSimulator = Depends(get_calendar),
    current_settings: Settings = Depends(get_settings),
) -> ScreeningProcessor:
    return ScreeningProcessor(
        vacancy_repository=vacancy_repository,
        history_repository=history_repository,
        llm_client=llm_client,
        calendar=calendar,
        min_screening_questions=current_settings.min_screening_questions,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook", response_model=WebhookResponse)
async def webhook(
    request: WebhookRequest,
    processor: ScreeningProcessor = Depends(get_processor),
) -> WebhookResponse:
    try:
        return await processor.process(request)
    except VacancyNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
