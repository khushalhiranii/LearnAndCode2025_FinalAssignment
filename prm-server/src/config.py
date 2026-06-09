from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://prm_user:prm_pass@localhost:5432/prm_db"

    # JWT
    jwt_secret_key: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_minutes: int = 15
    jwt_refresh_token_ttl_days: int = 7

    # Application
    environment: str = "development"
    log_level: str = "INFO"

    # Admin bootstrap defaults — used only by seed script
    admin_default_username: str = "admin"
    admin_default_password: str = "Admin@1234"
    admin_default_email: str = "admin@prm.local"
    admin_default_full_name: str = "System Administrator"


# Module-level singleton — loaded once at startup
settings = Settings()
