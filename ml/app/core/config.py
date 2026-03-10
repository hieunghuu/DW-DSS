from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 15432
    postgres_db: str = "walmart_dwh"
    postgres_user: str = "dwadmin"
    postgres_password: str = "hellofromtheotherside"

    # App
    api_env: str = "development"

    # ML
    model_dir: str = "/app/models"
    data_dir: str = "/app/data"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
