from src.application.dtos.system_config_dtos import SystemConfigResponse, UpdateSystemConfigRequest
from src.domain.ports.repositories import ISystemConfigRepository


class SystemConfigUseCase:
    def __init__(self, config_repo: ISystemConfigRepository) -> None:
        self._config_repo = config_repo

    async def get_config(self) -> SystemConfigResponse:
        config = await self._config_repo.get_config()
        return _to_response(config)

    async def update_config(self, request: UpdateSystemConfigRequest) -> SystemConfigResponse:
        config = await self._config_repo.get_config()

        if request.llm_provider is not None:
            config.llm_provider = request.llm_provider
        if request.llm_api_key is not None:
            config.llm_api_key = request.llm_api_key
        if request.llm_base_url is not None:
            config.llm_base_url = request.llm_base_url
        if request.llm_model is not None:
            config.llm_model = request.llm_model
        if request.scheduler_interval_minutes is not None:
            config.scheduler_interval_minutes = request.scheduler_interval_minutes
        elif request.scheduler_interval_hours is not None:
            config.scheduler_interval_minutes = request.scheduler_interval_hours * 60
        if request.max_weekly_hours is not None:
            config.max_weekly_hours = request.max_weekly_hours

        updated = await self._config_repo.update_config(config)
        return _to_response(updated)


def _to_response(config) -> SystemConfigResponse:
    return SystemConfigResponse(
        llm_provider=config.llm_provider,
        llm_api_key=config.llm_api_key,
        llm_base_url=config.llm_base_url,
        llm_model=config.llm_model,
        scheduler_interval_minutes=config.scheduler_interval_minutes,
        max_weekly_hours=config.max_weekly_hours,
    )
