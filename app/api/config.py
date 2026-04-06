from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	matches_per_page: int = Field(default=3, ge=1)
	default_champion_version: str = Field(default="14.5", min_length=1)

	model_config = SettingsConfigDict(env_prefix="PSI_", extra="ignore")


settings = Settings()
