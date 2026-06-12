from pydantic import BaseModel, Field, computed_field


class SystemConfigResponse(BaseModel):
    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    scheduler_interval_minutes: int
    max_weekly_hours: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def scheduler_interval_hours(self) -> int:
        return max(1, self.scheduler_interval_minutes // 60)


class UpdateSystemConfigRequest(BaseModel):
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    scheduler_interval_minutes: int | None = Field(None, ge=1)
    scheduler_interval_hours: int | None = Field(None, ge=1)
    max_weekly_hours: int | None = Field(None, ge=1)
