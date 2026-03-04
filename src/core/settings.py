from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "sqlite+aiosqlite:///nexus.db"
    redis_url: str = "redis://localhost:6379"

    # Ollama / AI
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"
    ollama_fallback_model: str = "qwen2.5:7b"
    ollama_timeout: int = 120

    # News
    newsapi_key: str = ""
    gnews_key: str = ""

    # Contact enrichment
    proxycurl_key: str = ""
    clearbit_key: str = ""
    hunter_key: str = ""

    # Technographics
    builtwith_key: str = ""
    theirstack_key: str = ""

    # Social
    twitter_bearer: str = ""
    linkedin_key: str = ""

    # CRM
    sf_client_id: str = ""
    sf_client_secret: str = ""
    sf_instance_url: str = ""
    hubspot_api_key: str = ""

    # Notifications
    slack_bot_token: str = ""
    slack_app_token: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""

    # OpenClaw
    openclaw_port: int = 3001


settings = Settings()
