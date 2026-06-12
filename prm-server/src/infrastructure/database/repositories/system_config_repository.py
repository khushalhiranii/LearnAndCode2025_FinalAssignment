from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.system_config import SystemConfig
from src.domain.ports.repositories import ISystemConfigRepository
from src.infrastructure.database.models.system_config_model import SystemConfigModel


class SQLAlchemySystemConfigRepository(ISystemConfigRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_config(self) -> SystemConfig:
        result = await self._session.execute(select(SystemConfigModel))
        rows = result.scalars().all()
        config_dict = {row.config_key: row.config_value for row in rows}
        return SystemConfig(
            llm_provider=config_dict.get("llm_provider", config_dict.get("ai_provider", "gemma")),
            llm_api_key=config_dict.get("llm_api_key", ""),
            llm_base_url=config_dict.get(
                "llm_base_url", "http://164.52.211.238/api/generate"
            ),
            llm_model=config_dict.get("llm_model", "gemma3:12b-it-q8_0"),
            scheduler_interval_minutes=int(config_dict.get("scheduler_interval_minutes", "240")),
            max_weekly_hours=int(config_dict.get("max_weekly_hours", "40")),
        )

    async def get_max_weekly_hours(self) -> int:
        config = await self.get_config()
        return config.max_weekly_hours

    async def update_config(self, config: SystemConfig) -> SystemConfig:
        for key, value in [
            ("llm_provider", config.llm_provider),
            ("llm_api_key", config.llm_api_key),
            ("llm_base_url", config.llm_base_url),
            ("llm_model", config.llm_model),
            ("scheduler_interval_minutes", str(config.scheduler_interval_minutes)),
            ("max_weekly_hours", str(config.max_weekly_hours)),
        ]:
            result = await self._session.execute(
                select(SystemConfigModel).where(SystemConfigModel.config_key == key)
            )
            row = result.scalar_one_or_none()
            if row:
                row.config_value = value
            else:
                self._session.add(SystemConfigModel(config_key=key, config_value=value))
        await self._session.flush()
        return config
