import re

from app.llm.base import LLMClient
from app.models.message import ConversationMessage, MessageRole
from app.models.screening import RecommendationStatus, ScreeningAnalysis
from app.models.vacancy import Vacancy


class StubLLMClient(LLMClient):
    """Детерминированная замена LLM для локальных тестов без API-ключа."""

    async def next_question(
        self,
        vacancy: Vacancy,
        history: list[ConversationMessage],
        candidate_name: str | None = None,
    ) -> str:
        asked = sum(1 for message in history if message.role == MessageRole.BOT and "?" in message.text)
        questions = [
            f"{self._name(candidate_name)}Расскажите, пожалуйста, о последнем релевантном опыте для вакансии «{vacancy.title}»: сколько лет опыта и какие задачи выполняли?",
            "С какими технологиями из требований вакансии вы работали на практике и на каком уровне?",
            "Какие у вас зарплатные ожидания и какой формат работы вам подходит?",
            "Когда вы готовы выйти на работу и есть ли ограничения по графику или собеседованиям?",
            "Есть ли проекты или достижения, которые лучше всего подтверждают ваш опыт?",
        ]
        return questions[min(asked, len(questions) - 1)]

    async def analyze_candidate(
        self,
        vacancy: Vacancy,
        history: list[ConversationMessage],
    ) -> ScreeningAnalysis:
        transcript = "\n".join(message.text for message in history if message.role == MessageRole.CANDIDATE)
        normalized = transcript.lower()

        matched_requirements = [item for item in vacancy.must_have if self._matches_requirement(item, normalized)]
        years = self._extract_years(normalized)
        salary = self._extract_salary(normalized)

        score = 20
        if vacancy.must_have:
            score += int(45 * len(matched_requirements) / len(vacancy.must_have))
        if years >= vacancy.min_experience_years:
            score += 20
        elif years > 0:
            score += 10
        if self._salary_is_ok(salary, vacancy):
            score += 10
        if "готов" in normalized or "могу" in normalized:
            score += 5
        score = max(0, min(100, score))

        missing = [item for item in vacancy.must_have if item not in matched_requirements]
        strengths = []
        if matched_requirements:
            strengths.append("Есть совпадения с ключевыми требованиями: " + ", ".join(matched_requirements))
        if years:
            strengths.append(f"Заявлен опыт около {years} лет")

        risks = []
        if missing:
            risks.append("Не подтверждены требования: " + ", ".join(missing))
        if salary and vacancy.salary_to and salary > vacancy.salary_to:
            risks.append("Зарплатные ожидания выше верхней границы вакансии")

        if score >= 70 and not missing[:2]:
            status = RecommendationStatus.SUITABLE
            summary = "Кандидат в целом соответствует базовым требованиям вакансии."
            feedback = None
            next_question = None
        elif score <= 45:
            status = RecommendationStatus.NOT_SUITABLE
            summary = "Кандидат пока не проходит базовый первичный скрининг."
            feedback = (
                "Спасибо за ответы. Сейчас опыт не полностью совпадает с требованиями вакансии, "
                "поэтому мы не готовы пригласить вас на следующий этап. Рекомендуем усилить "
                "практику по ключевым технологиям из описания вакансии."
            )
            next_question = None
        else:
            status = RecommendationStatus.NEEDS_CLARIFICATION
            summary = "Для решения не хватает информации по части требований."
            feedback = None
            next_question = "Уточните, пожалуйста, опыт по следующим требованиям: " + ", ".join(missing[:3])

        return ScreeningAnalysis(
            status=status,
            score=score,
            summary=summary,
            strengths=strengths,
            risks=risks,
            missing_info=missing,
            next_question=next_question,
            feedback=feedback,
        )

    @staticmethod
    def _name(candidate_name: str | None) -> str:
        if not candidate_name:
            return ""
        first_name = candidate_name.split()[0]
        return f"{first_name}, "

    @staticmethod
    def _extract_years(text: str) -> int:
        matches = re.findall(r"(\d+)\s*(?:год|года|лет|year|years)", text)
        return max([int(item) for item in matches], default=0)

    @staticmethod
    def _extract_salary(text: str) -> int | None:
        matches = re.findall(r"(\d{2,4})\s*(?:к|тыс|000|руб|₽)", text)
        if not matches:
            return None
        value = max(int(item) for item in matches)
        if value < 10_000:
            value *= 1000
        return value

    @staticmethod
    def _salary_is_ok(salary: int | None, vacancy: Vacancy) -> bool:
        if salary is None:
            return False
        if vacancy.salary_from and salary < vacancy.salary_from:
            return False
        if vacancy.salary_to and salary > vacancy.salary_to:
            return False
        return True

    @staticmethod
    def _matches_requirement(requirement: str, text: str) -> bool:
        tokens = [token for token in re.split(r"[^a-zA-Zа-яА-Я0-9+#]+", requirement.lower()) if len(token) > 1]
        sentences = re.split(r"[.!?\n]+", text)
        for sentence in sentences:
            has_token = any(token in sentence for token in tokens)
            if not has_token:
                continue
            negative_markers = ("не знаю", "нет опыта", "не работал", "не работала", "не умею", "с нуля")
            if any(marker in sentence for marker in negative_markers):
                continue
            return True
        return False
