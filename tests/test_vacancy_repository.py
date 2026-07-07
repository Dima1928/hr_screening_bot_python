from pathlib import Path

import pytest

from app.repositories.vacancy import JsonVacancyRepository, VacancyNotFoundError


def test_get_vacancy_by_id() -> None:
    repo = JsonVacancyRepository(Path("app/data/vacancies.json"))

    vacancy = repo.get("python_backend")

    assert vacancy.title == "Python Backend Developer"
    assert "Python" in vacancy.must_have


def test_unknown_vacancy_raises_error() -> None:
    repo = JsonVacancyRepository(Path("app/data/vacancies.json"))

    with pytest.raises(VacancyNotFoundError):
        repo.get("unknown")
