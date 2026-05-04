from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/ml_platform.db"
    upload_dir: str = "./data/uploads"
    upload_max_bytes: int = 2 * 1024 * 1024 * 1024
    models_dir: str = "./data/models"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
