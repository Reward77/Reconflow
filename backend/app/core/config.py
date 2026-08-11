from pydantic_settings import BaseSettings

from pathlib import Path

class Settings(BaseSettings):

    APP_NAME: str = "ReconFlow API"

    DATABASE_URL: str = "sqlite:///./reconflow.db"

    SECRET_KEY: str = "dev-secret-key"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_ROOT = BASE_DIR / "storage" / "uploads"

MAX_UPLOAD_SIZE = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls"
}