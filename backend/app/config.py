from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/vn_breadth"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:password@localhost:5432/vn_breadth"
    DATA_DIR: Path = Path("./data")
    API_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
