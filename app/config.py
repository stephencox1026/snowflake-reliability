"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    reliability_database_url: str = f"sqlite:///{ROOT / 'data' / 'warehouse.db'}"
    reliability_data_dir: Path = ROOT / "data"
    reliability_models_dir: Path = ROOT / "data" / "models"
    reliability_offline_mode: bool = True

    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_password: str | None = None
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str = "RELIABILITY_DB"
    snowflake_schema: str = "PUBLIC"
    snowflake_role: str = "SYSADMIN"

    @property
    def uses_sqlite(self) -> bool:
        return self.reliability_database_url.startswith("sqlite")

    def ensure_dirs(self) -> None:
        self.reliability_data_dir.mkdir(parents=True, exist_ok=True)
        self.reliability_models_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
