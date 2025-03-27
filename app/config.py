from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "pass1234"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "zip_db"
    POSTGRES_URL: str = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    MINIO_ROOT_USER: str = "minio"
    MINIO_ROOT_PASSWORD: str = "minio123"
    MINIO_HOST: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "minio-bucket"
    MINIO_ENDPOINT: str = "minio:9000"

    LOG_LEVEL: str = "INFO"


settings = Settings()

def get_db_url():
    return settings.POSTGRES_URL