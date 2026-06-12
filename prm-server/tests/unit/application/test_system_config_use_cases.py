"""Unit tests for system config use case."""

import pytest

from src.application.admin.system_config_use_case import SystemConfigUseCase
from src.application.dtos.system_config_dtos import UpdateSystemConfigRequest
from src.domain.entities.system_config import SystemConfig


class InMemorySystemConfigRepository:
    def __init__(self) -> None:
        self._config = SystemConfig(
            llm_provider="gemma",
            llm_api_key="",
            llm_base_url="http://164.52.211.238/api/generate",
            llm_model="gemma3:12b-it-q8_0",
            scheduler_interval_minutes=240,
            max_weekly_hours=40,
        )

    async def get_config(self) -> SystemConfig:
        return self._config

    async def update_config(self, config: SystemConfig) -> SystemConfig:
        self._config = config
        return config


@pytest.mark.asyncio
async def test_get_config_returns_defaults() -> None:
    repo = InMemorySystemConfigRepository()
    uc = SystemConfigUseCase(repo)
    result = await uc.get_config()
    assert result.llm_provider == "gemma"
    assert result.scheduler_interval_hours == 4


@pytest.mark.asyncio
async def test_update_scheduler_hours_converts_to_minutes() -> None:
    repo = InMemorySystemConfigRepository()
    uc = SystemConfigUseCase(repo)
    result = await uc.update_config(UpdateSystemConfigRequest(scheduler_interval_hours=2))
    assert result.scheduler_interval_minutes == 120
