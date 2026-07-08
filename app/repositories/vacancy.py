from __future__ import annotations

from typing import Protocol

from app.data.default_vacancies import DEFAULT_VACANCIES
from app.models.vacancy import Vacancy


class VacancyNotFoundError(KeyError):
    pass


class VacancyRepository(Protocol):
    def get(self, vacancy_id: str) -> Vacancy:
        ...

    def list(self) -> list[Vacancy]:
        ...


class InMemoryVacancyRepository:
    """Репозиторий для тестов и локальной демонстрации без PostgreSQL."""

    def __init__(self, vacancies: list[Vacancy] | None = None) -> None:
        source = vacancies or [Vacancy.model_validate(item) for item in DEFAULT_VACANCIES]
        self._vacancies = {vacancy.id: vacancy for vacancy in source}

    def get(self, vacancy_id: str) -> Vacancy:
        vacancy = self._vacancies.get(vacancy_id)
        if vacancy is None:
            raise VacancyNotFoundError(f"Vacancy '{vacancy_id}' not found")
        return vacancy

    def list(self) -> list[Vacancy]:
        return list(self._vacancies.values())


class PostgresVacancyRepository:
    """PostgreSQL-репозиторий вакансий.

    Вакансии больше не читаются из JSON-файла. Таблица создаётся самим
    микросервисом, а стартовые вакансии находятся в коде проекта и при первом
    запуске добавляются в PostgreSQL.
    """

    def __init__(self, database_url: str, seed_on_startup: bool = True) -> None:
        self.database_url = database_url
        self.initialize(seed_on_startup=seed_on_startup)

    def initialize(self, seed_on_startup: bool = True) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vacancies (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        must_have JSONB NOT NULL DEFAULT '[]'::jsonb,
                        nice_to_have JSONB NOT NULL DEFAULT '[]'::jsonb,
                        min_experience_years INTEGER NOT NULL DEFAULT 0,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        currency TEXT NOT NULL DEFAULT 'RUB',
                        recruiter_email TEXT
                    )
                    """
                )
                if seed_on_startup:
                    for item in DEFAULT_VACANCIES:
                        vacancy = Vacancy.model_validate(item)
                        cursor.execute(
                            """
                            INSERT INTO vacancies (
                                id,
                                title,
                                description,
                                must_have,
                                nice_to_have,
                                min_experience_years,
                                salary_from,
                                salary_to,
                                currency,
                                recruiter_email
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                title = EXCLUDED.title,
                                description = EXCLUDED.description,
                                must_have = EXCLUDED.must_have,
                                nice_to_have = EXCLUDED.nice_to_have,
                                min_experience_years = EXCLUDED.min_experience_years,
                                salary_from = EXCLUDED.salary_from,
                                salary_to = EXCLUDED.salary_to,
                                currency = EXCLUDED.currency,
                                recruiter_email = EXCLUDED.recruiter_email
                            """,
                            (
                                vacancy.id,
                                vacancy.title,
                                vacancy.description,
                                self._jsonb(vacancy.must_have),
                                self._jsonb(vacancy.nice_to_have),
                                vacancy.min_experience_years,
                                vacancy.salary_from,
                                vacancy.salary_to,
                                vacancy.currency,
                                vacancy.recruiter_email,
                            ),
                        )
            connection.commit()

    def get(self, vacancy_id: str) -> Vacancy:
        with self._connect() as connection:
            with connection.cursor(row_factory=self._dict_row()) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        title,
                        description,
                        must_have,
                        nice_to_have,
                        min_experience_years,
                        salary_from,
                        salary_to,
                        currency,
                        recruiter_email
                    FROM vacancies
                    WHERE id = %s
                    """,
                    (vacancy_id,),
                )
                row = cursor.fetchone()

        if row is None:
            raise VacancyNotFoundError(f"Vacancy '{vacancy_id}' not found")
        return Vacancy.model_validate(row)

    def list(self) -> list[Vacancy]:
        with self._connect() as connection:
            with connection.cursor(row_factory=self._dict_row()) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        title,
                        description,
                        must_have,
                        nice_to_have,
                        min_experience_years,
                        salary_from,
                        salary_to,
                        currency,
                        recruiter_email
                    FROM vacancies
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()
        return [Vacancy.model_validate(row) for row in rows]

    def _connect(self):
        try:
            from psycopg import connect
        except ImportError as error:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. Install dependencies: pip install -r requirements.txt"
            ) from error
        return connect(self.database_url)

    @staticmethod
    def _dict_row():
        from psycopg.rows import dict_row

        return dict_row

    @staticmethod
    def _jsonb(value):
        from psycopg.types.json import Jsonb

        return Jsonb(value)
