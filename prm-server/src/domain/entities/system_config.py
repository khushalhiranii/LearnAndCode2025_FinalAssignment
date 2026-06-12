import dataclasses


@dataclasses.dataclass
class SystemConfig:
    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    scheduler_interval_minutes: int
    max_weekly_hours: int

    @property
    def scheduler_interval_hours(self) -> int:
        return max(1, self.scheduler_interval_minutes // 60)
