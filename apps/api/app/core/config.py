from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "apps/api/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RiverCDC"
    api_host: str = "0.0.0.0"
    api_port: int = 8007
    cors_origins: str = "http://localhost:3007"

    jwt_secret: str = "rivercdc-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    source_database_url: str = (
        "postgresql://rivercdc:rivercdc_dev_password@localhost:5436/rivercdc_source"
    )
    dest_database_url: str = (
        "postgresql://rivercdc:rivercdc_dev_password@localhost:5437/rivercdc_dest"
    )
    control_database_url: str = (
        "postgresql://rivercdc:rivercdc_dev_password@localhost:5437/rivercdc_control"
    )

    kafka_bootstrap: str = "localhost:19092"
    kafka_topic: str = "rivercdc.shop.orders"
    kafka_dlq_topic: str = "rivercdc.dlq"
    kafka_consumer_group: str = "rivercdc-consumer"

    replication_slot: str = "rivercdc_slot"
    cdc_poll_interval_ms: int = 500
    max_retries: int = 3

    redis_url: str = "redis://localhost:6382/0"
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
