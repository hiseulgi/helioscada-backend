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

    # Database Configuration
    # Example for async pg: postgresql+asyncpg://user:pass@host:port/dbname
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/helioscada"
    )

    # MQTT Configuration
    MQTT_BROKER: str = Field(default="localhost")
    MQTT_PORT: int = Field(default=1883)
    MQTT_TOPIC_TELEMETRY: str = Field(
        default="laboratorium/scada/pv_kit/telemetry"
    )
    MQTT_TOPIC_STATUS_RELAY: str = Field(
        default="laboratorium/scada/pv_kit/status/relay"
    )


settings = Settings()
