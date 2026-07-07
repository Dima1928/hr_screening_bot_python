import json
from pathlib import Path

from app.models.vacancy import Vacancy


class VacancyNotFoundError(KeyError):
    pass


class JsonVacancyRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._vacancies = self._load()

    def _load(self) -> dict[str, Vacancy]:
        with self.path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
        vacancies = [Vacancy.model_validate(item) for item in raw]
        return {vacancy.id: vacancy for vacancy in vacancies}

    def get(self, vacancy_id: str) -> Vacancy:
        vacancy = self._vacancies.get(vacancy_id)
        if vacancy is None:
            raise VacancyNotFoundError(f"Vacancy '{vacancy_id}' not found")
        return vacancy

    def list(self) -> list[Vacancy]:
        return list(self._vacancies.values())
