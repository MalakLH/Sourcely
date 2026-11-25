from datetime import datetime

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a single chunk of documentation."""

    chunk_id: str
    content: str
    source_url: str
    section_title: str
    doc_version: str = "latest"
    heading_path: str  # e.g., "Overview > Concepts > Pods"
    chunk_index: int
    token_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RetrievalQuery(BaseModel):
    """Request schema for document retrieval."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class RetrievalResult(BaseModel):
    """Single retrieved document with metadata."""

    content: str
    source_url: str
    section_title: str
    heading_path: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    chunk_id: str
    doc_version: str


class RetrievalResponse(BaseModel):
    """Response schema for document retrieval."""

    query: str
    results: list[RetrievalResult]
    retrieved_count: int
    confidence: str  # "high", "medium", "low"


class IngestionRequest(BaseModel):
    """Request schema for document ingestion."""

    source_path: str
    doc_version: str = "latest"
    force_reindex: bool = False


class IngestionResponse(BaseModel):
    """Response schema for document ingestion."""

    status: str
    chunks_created: int
    documents_processed: int
    elapsed_seconds: float
