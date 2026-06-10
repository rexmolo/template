from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    expose_api_docs: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_docs_enabled(self) -> bool:
        return self.env != "production" or self.expose_api_docs
