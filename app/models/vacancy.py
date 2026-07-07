from pydantic import BaseModel, Field


class Vacancy(BaseModel):
    id: str
    title: str
    description: str
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    min_experience_years: int = 0
    salary_from: int | None = None
    salary_to: int | None = None
    currency: str = "RUB"
    recruiter_email: str | None = None
