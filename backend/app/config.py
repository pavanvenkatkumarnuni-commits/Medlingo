import os
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    client_origin: str = "http://localhost:5173"
    database_url: str = "sqlite:///./data/medlingo.db"
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10
    ai_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    tesseract_cmd: str = "tesseract"
    class Config:
        env_file = ".env"
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)
