import json

import httpx
import pytest

from app.llm.deepseek import DeepSeekClient
from app.models.message import ConversationMessage, MessageRole
from app.models.screening import RecommendationStatus
from app.repositories.vacancy import JsonVacancyRepository


@pytest.mark.asyncio
async def test_deepseek_next_question_uses_post_chat_completions() -> None:
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("Authorization")
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps({"question": "Сколько лет опыта с Python?"})}}
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = DeepSeekClient(
            api_key="test-key",
            base_url="https://api.deepseek.com",
            http_client=http_client,
        )
        vacancy = JsonVacancyRepository("app/data/vacancies.json").get("python_backend")

        question = await client.next_question(vacancy, [], "Иван")

    assert question == "Сколько лет опыта с Python?"
    assert captured["method"] == "POST"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "deepseek-chat"
    assert captured["payload"]["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_deepseek_analyze_candidate_parses_screening_json() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "status": "подходит",
                                    "score": 86,
                                    "summary": "Опыт соответствует требованиям.",
                                    "strengths": ["Python", "Docker"],
                                    "risks": [],
                                    "missing_info": [],
                                    "next_question": None,
                                    "feedback": None,
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = DeepSeekClient(api_key="test-key", http_client=http_client)
        vacancy = JsonVacancyRepository("app/data/vacancies.json").get("python_backend")
        history = [ConversationMessage(role=MessageRole.CANDIDATE, text="Python, Docker, 3 года")]

        analysis = await client.analyze_candidate(vacancy, history)

    assert analysis.status == RecommendationStatus.SUITABLE
    assert analysis.score == 86
