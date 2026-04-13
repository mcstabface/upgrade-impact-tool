from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import API_V1_PREFIX


class Settings(BaseSettings):
    app_name: str = Field(default="Upgrade Impact Analysis Tool")
    app_version: str = Field(default="0.0.1")
    app_env: str = Field(default="local")
    app_port: int = Field(default=8000)
    api_v1_prefix: str = Field(default=API_V1_PREFIX)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()