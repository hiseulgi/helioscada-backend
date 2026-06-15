from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "HELIOSCADA Backend"
    API_V1_STR: str = "/api/v1"

    # API Binding and CORS
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_CORS: str = "*"

    # Database Configuration (PostgreSQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "helioscada"
    DATABASE_URL: str | None = None

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # MQTT Configuration
    MQTT_BROKER: str = Field(default="localhost")
    MQTT_PORT: int = Field(default=1883)
    MQTT_TOPIC_TELEMETRY: str = Field(
        default="laboratorium/scada/pv_kit/telemetry"
    )
    MQTT_TOPIC_STATUS_RELAY: str = Field(
        default="laboratorium/scada/pv_kit/status/relay"
    )

    # Bridge API URL
    API_URL: str = Field(default="http://localhost:8000/api/v1")


settings = Settings()
