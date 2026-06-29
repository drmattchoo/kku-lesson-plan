from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    google_client_id: str = ""
    google_client_secret: str = ""
    allowed_email_domain: str = "kku.ac.th"

    llm_base_url: str = "https://gen.ai.kku.ac.th/api/v1"
    llm_api_key: str = ""
    llm_provider: str = "claude"
    llm_model_claude: str = "claude-sonnet-4.6"
    llm_model_gpt: str = "gpt-5.5"

    session_secret: str = "change-me-dev-only"

    @property
    def active_model(self) -> str:
        return self.llm_model_claude if self.llm_provider == "claude" else self.llm_model_gpt


settings = Settings()
