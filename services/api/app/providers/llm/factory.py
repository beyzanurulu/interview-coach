from app.core.config import Settings
from app.providers.llm.base import LLMProvider
from app.providers.llm.openai_compat import OpenAICompatibleProvider


def build_llm(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "ollama":
        # Sadece yerel geliştirme için.
        return OpenAICompatibleProvider(
            name="ollama",
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_s=settings.llm_timeout_s,
        )
    return OpenAICompatibleProvider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        timeout_s=settings.llm_timeout_s,
        max_retry_wait_s=settings.llm_max_retry_wait_s,
    )
