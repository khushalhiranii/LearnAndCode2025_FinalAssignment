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

    # LLM defaults — used when system_config DB values are empty (set in .env)
    llm_provider: str = "gemma"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    # Email — console (dev) | gmail (GCP) | smtp
    email_provider: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@prm.local"
    smtp_use_tls: bool = True
    gmail_sender: str = ""
    gmail_service_account_file: str = ""

    # Admin bootstrap defaults — used only by seed script
    admin_default_username: str = "admin"
    admin_default_password: str = "Admin@1234"
    admin_default_email: str = "admin@prm.local"
    admin_default_full_name: str = "System Administrator"


# Module-level singleton — loaded once at startup
settings = Settings()
