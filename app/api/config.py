from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	matches_per_page: int = Field(default=3, ge=1)
	default_champion_version: str = Field(default="14.5", min_length=1)
	otel_enabled: bool = Field(default=True)
	otel_service_name: str = Field(default="psi-api", min_length=1)
	otel_service_version: str = Field(default="0.1.0", min_length=1)
	otel_environment: str = Field(default="dev", min_length=1)
	otel_exporter_otlp_endpoint: str = Field(default="http://otel-collector:4317", min_length=1)
	otel_exporter_otlp_insecure: bool = Field(default=True)
	otel_traces_sampler_arg: float = Field(default=1.0, ge=0.0, le=1.0)

	model_config = SettingsConfigDict(env_prefix="PSI_", extra="ignore")


settings = Settings()
