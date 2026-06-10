from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_SECRET_VALUES = {
    "",
    "change-me",
    "replace-me",
    "replace-me-with-a-long-random-secret",
}


class Settings(BaseSettings):
    env: str = "development"
    expose_api_docs: bool = False
    api_secret_key: str = "replace-me-with-a-long-random-secret"
    public_site_origin: str = "http://localhost:4321"
    app_origin: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_docs_enabled(self) -> bool:
        return self.env != "production" or self.expose_api_docs

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.env == "production" and self.api_secret_key in PLACEHOLDER_SECRET_VALUES:
            raise ValueError("API_SECRET_KEY must be a real secret in production")
        return self
