from src.domain.entities.system_config import SystemConfig
from src.domain.exceptions import AIProviderError
from src.domain.ports.ai_provider import IAIProvider
from src.infrastructure.llm.gemma_adapter import GemmaAdapter, GeminiAdapter, GroqAdapter, MockAIProvider


class AIProviderFactory:

    @staticmethod
    def create(config: SystemConfig, use_mock: bool = False) -> IAIProvider:
        if use_mock:
            return MockAIProvider()

        provider = config.llm_provider.lower()
        if provider == "gemma":
            AIProviderFactory._require_gemma_config(config)
            return GemmaAdapter(
                api_key=config.llm_api_key,
                base_url=config.llm_base_url,
                model=config.llm_model,
            )
        if provider in ("gemini", "google"):
            return GeminiAdapter(api_key=config.llm_api_key, model=config.llm_model)
        if provider == "groq":
            return GroqAdapter(api_key=config.llm_api_key, model=config.llm_model)
        AIProviderFactory._require_gemma_config(config)
        return GemmaAdapter(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            model=config.llm_model,
        )

    @staticmethod
    def _require_gemma_config(config: SystemConfig) -> None:
        if not config.llm_base_url.strip() or not config.llm_model.strip():
            raise AIProviderError(
                "Gemma LLM requires llm_base_url and llm_model. "
                "Set LLM_BASE_URL and LLM_MODEL in .env or Admin → System Configuration."
            )
