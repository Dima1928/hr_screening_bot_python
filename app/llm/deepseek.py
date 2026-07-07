import json
import re
from typing import Any

import httpx

from app.llm.base import LLMClient
from app.models.message import ConversationMessage, MessageRole
from app.models.screening import RecommendationStatus, ScreeningAnalysis
from app.models.vacancy import Vacancy


class DeepSeekClient(LLMClient):
    """LLM-клиент, который обращается к DeepSeek через POST /chat/completions."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout_seconds: float = 30,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("LLM_API_KEY is required when LLM_MODE=deepseek")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._http_client = http_client

    async def next_question(
        self,
        vacancy: Vacancy,
        history: list[ConversationMessage],
        candidate_name: str | None = None,
    ) -> str:
        payload = await self._send_messages(
            [
                {
                    "role": "system",
                    "content": (
                        "Ты HR-бот для первичного скрининга кандидатов. "
                        "Задай ровно один следующий вопрос кандидату. "
                        "Вопрос должен быть адаптивным: не повторяй уже заданное, "
                        "учитывай ответы кандидата и требования вакансии. "
                        "Ответь строго JSON-объектом вида {\"question\": \"...\"}."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "candidate_name": candidate_name,
                            "vacancy": vacancy.model_dump(),
                            "history": self._history_for_prompt(history),
                        },
                        ensure_ascii=False,
                    ),
                },
            ]
        )
        question = str(payload.get("question", "")).strip()
        if not question:
            return "Расскажите, пожалуйста, подробнее о вашем релевантном опыте для этой вакансии?"
        return question

    async def analyze_candidate(
        self,
        vacancy: Vacancy,
        history: list[ConversationMessage],
    ) -> ScreeningAnalysis:
        payload = await self._send_messages(
            [
                {
                    "role": "system",
                    "content": (
                        "Ты HR-бот для первичного скрининга кандидатов. "
                        "Оцени кандидата по требованиям вакансии, опыту, навыкам и ожиданиям. "
                        "Верни строго JSON без markdown. Поля: "
                        "status: одно из ['подходит','не подходит','требуется уточнение']; "
                        "score: число 0-100; summary: строка; strengths: массив строк; "
                        "risks: массив строк; missing_info: массив строк; "
                        "next_question: строка или null; feedback: строка или null. "
                        "Если кандидат не подходит, feedback должен быть вежливым отказом с краткой обратной связью."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "vacancy": vacancy.model_dump(),
                            "history": self._history_for_prompt(history),
                        },
                        ensure_ascii=False,
                    ),
                },
            ]
        )
        return self._analysis_from_payload(payload)

    async def _send_messages(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        request_payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"

        if self._http_client is not None:
            response = await self._http_client.post(url, json=request_payload, headers=headers)
            response.raise_for_status()
            return self._parse_response(response.json())

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, json=request_payload, headers=headers)
            response.raise_for_status()
            return self._parse_response(response.json())

    @staticmethod
    def _parse_response(raw_response: dict[str, Any]) -> dict[str, Any]:
        try:
            content = raw_response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("Unexpected LLM response format") from error

        if isinstance(content, dict):
            return content
        if not isinstance(content, str):
            raise ValueError("LLM content must be a string or JSON object")

        cleaned = content.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise ValueError(f"LLM returned non-JSON content: {cleaned[:200]}") from error

    @staticmethod
    def _history_for_prompt(history: list[ConversationMessage]) -> list[dict[str, str]]:
        return [
            {
                "role": "assistant" if message.role == MessageRole.BOT else "user",
                "content": message.text,
            }
            for message in history
        ]

    @staticmethod
    def _analysis_from_payload(payload: dict[str, Any]) -> ScreeningAnalysis:
        status = payload.get("status")
        if status not in {item.value for item in RecommendationStatus}:
            payload["status"] = RecommendationStatus.NEEDS_CLARIFICATION.value
        return ScreeningAnalysis.model_validate(payload)
