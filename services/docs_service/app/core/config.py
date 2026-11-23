from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# In Docker, we're at /app, so ROOT_DIR should point to /app
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Sourcely Docs Expert"
    app_env: str = "development"
    app_port: int = 8001
    log_level: str = "INFO"

    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # LanceDB settings - data directory inside container
    lancedb_path: str = "/app/data/vectordb"
    docs_table_name: str = "kubernetes_docs"

    # Chunking settings
    chunk_overlap_percent: float = 0.125  # 12.5% overlap
    max_chunk_tokens: int = 512
    min_chunk_tokens: int = 50

    # Retrieval settings
    default_top_k: int = 5
    similarity_threshold: float = 0.3

    # Documentation source
    docs_raw_path: str = str(ROOT_DIR / "services" / "docs_service" / "data" / "raw")

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
