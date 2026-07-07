from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8090, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    llm_mode: Literal["stub", "deepseek"] = Field(default="stub", alias="LLM_MODE")
    llm_api_base_url: str = Field(default="https://api.deepseek.com", alias="LLM_API_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=30, alias="LLM_TIMEOUT_SECONDS")

    vacancies_path: str = Field(default="app/data/vacancies.json", alias="VACANCIES_PATH")
    min_screening_questions: int = Field(default=4, alias="MIN_SCREENING_QUESTIONS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
