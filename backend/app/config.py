from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_csv_env(value: str) -> list:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    google_client_id: str = ""
    google_client_secret: str = ""
    allowed_email_domain: str = "kku.ac.th"
    # Comma-separated extra emails allowed to log in (e.g. external testers).
    # Example: EXTRA_ALLOWED_EMAILS=dev@gmail.com,tester@example.com
    extra_allowed_emails: str = ""

    llm_base_url: str = "https://gen.ai.kku.ac.th/api/v1"
    llm_api_key: str = ""
    llm_provider: str = "claude"
    llm_model_claude: str = "claude-sonnet-4.6"
    llm_model_gpt: str = "gpt-5.5"

    session_secret: str = "change-me-dev-only"
    # Cookie is NOT Secure by default — localhost dev runs over plain http, and a
    # Secure cookie is silently dropped by the browser over http. Staging/prod MUST
    # set this true (https-only host) or the post-login session cookie never sticks.
    session_https_only: bool = False

    # Public https URL of THIS app (e.g. "https://lesson-plan-staging.onrender.com"),
    # no trailing slash. Used to build the OAuth redirect_uri explicitly — never
    # derived from the incoming request, which sees plain http behind most PaaS
    # reverse proxies (Render, Railway, Fly) unless proxy headers are specially
    # trusted, producing an http callback URL that won't match what's registered in
    # the Google console. Empty (default) falls back to request-derived URLs, which
    # is correct for local dev (http://localhost:8000).
    base_url: str = ""

    # Comma-separated. "*" (default) disables host checking entirely — fine for
    # local dev/tests. Staging/prod should set this to the real host(s), e.g.
    # "lesson-plan-staging.onrender.com" (no scheme), to reject requests with a
    # forged Host header.
    allowed_hosts: str = "*"

    # Comma-separated origins (with scheme), e.g. "https://lesson-plan-staging.onrender.com".
    # Empty (default) disables CORS middleware entirely. Not needed when the frontend
    # is served from this same process/origin (the normal case, see main.py's
    # StaticFiles mount) — only set this if the frontend is ever hosted separately.
    cors_origins: str = ""

    @property
    def active_model(self) -> str:
        return self.llm_model_claude if self.llm_provider == "claude" else self.llm_model_gpt


settings = Settings()
