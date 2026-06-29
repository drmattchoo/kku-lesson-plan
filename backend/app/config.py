from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    google_client_id: str = ""
    google_client_secret: str = ""
    allowed_email_domain: str = "kku.ac.th"

    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.5"

    session_secret: str = "change-me-dev-only"

    @property
    def active_model(self) -> str:
        return self.anthropic_model if self.llm_provider == "anthropic" else self.openai_model


settings = Settings()
