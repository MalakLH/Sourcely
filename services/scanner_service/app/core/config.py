from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_name: str = "Sourcely Code Scanner"
    app_env: str = "development"
    app_port: int = 8002
    log_level: str = "INFO"

    # Ollama settings for LLM explanations
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:3b"
    ollama_temperature: float = 0.3

    # Scanner settings
    max_file_size_mb: int = 10
    scan_timeout_seconds: int = 60

    # Severity mapping
    severity_levels: list[str] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
