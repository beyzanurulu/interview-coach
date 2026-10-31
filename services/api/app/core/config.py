import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları. Değerler ortam değişkenlerinden / .env dosyasından okunur."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # LLM (ADR-002)
    llm_provider: Literal["groq", "ollama"] = "groq"
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen3:8b"
    llm_timeout_s: float = 30.0
    llm_max_retry_wait_s: float = 10.0

    # Mülakat
    interview_durations_min: list[int] = [5, 10, 15]
    max_follow_ups: int = 2
    max_job_chars: int = 8000
    max_cv_chars: int = 8000
    max_answer_chars: int = 4000
    max_cv_bytes: int = 2_000_000
    wrap_up_grace_s: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """JSON listesi, virgülle ayrılmış liste veya tek adres kabul eder; boş = boş liste."""
        if not isinstance(value, str):
            return value
        value = value.strip()
        origins = json.loads(value) if value.startswith("[") else value.split(",")
        # Tarayıcı Origin başlığını sonda "/" olmadan gönderir.
        return [origin.strip().rstrip("/") for origin in origins if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
