from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@db:5432/crypto"
    deribit_base_url: str = "https://www.deribit.com/api/v2"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"