from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    APP_NAME: str = "FastAPI App"
    DRAGONFLY_URL: str = "redis://localhost:6379/0"

    PRINTER_POLLING_INTERVAL: int = 5
    MAX_CONCURRENT_TASKS: int = 5
    SELENIUM_POOL_SIZE: int = 4     

    @computed_field
    @property
    def POSTGRES_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def POSTGRES_SYNC_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()