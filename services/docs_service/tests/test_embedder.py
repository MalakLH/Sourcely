import pytest
from datetime import datetime

from app.ingestion.embedder import VectorStore
from app.models.schemas import DocumentChunk


@pytest.fixture
def vector_store(tmp_path):
    """Create a temporary vector store for testing."""
    db_path = str(tmp_path / "test_vectordb")
    return VectorStore(db_path=db_path, table_name="test_docs")


@pytest.fixture
def sample_chunks():
    """Create sample document chunks for testing."""
    return [
        DocumentChunk(
            chunk_id="chunk1",
            content="Kubernetes Pods are the smallest deployable units.",
            source_url="https://kubernetes.io/docs/concepts/pods",
            section_title="Pods Overview",
            doc_version="v1.28",
            heading_path="Concepts > Pods",
            chunk_index=0,
            token_count=10,
            created_at=datetime.utcnow(),
        ),
        DocumentChunk(
            chunk_id="chunk2",
            content="Services expose applications running on Pods.",
            source_url="https://kubernetes.io/docs/concepts/services",
            section_title="Services Overview",
            doc_version="v1.28",
            heading_path="Concepts > Services",
            chunk_index=0,
            token_count=8,
            created_at=datetime.utcnow(),
        ),
    ]


def test_embed_text(vector_store):
    """Test embedding a single text."""
    text = "This is a test document."
    embedding = vector_store.embed_text(text)

    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)


def test_add_and_search_chunks(vector_store, sample_chunks):
    """Test adding chunks and searching."""
    # Add chunks
    count = vector_store.add_chunks(sample_chunks)
    assert count == len(sample_chunks)

    # Search for Pods
    results = vector_store.search("What are Pods?", top_k=2)

    assert len(results) > 0
    assert any("Pods" in r.content for r in results)
    assert all(hasattr(r, "similarity_score") for r in results)


def test_table_stats(vector_store, sample_chunks):
    """Test getting table statistics."""
    # Initially empty
    stats = vector_store.get_table_stats()
    assert stats["count"] == 0

    # Add chunks
    vector_store.add_chunks(sample_chunks)

    # Check stats
    stats = vector_store.get_table_stats()
    assert stats["exists"]
    assert stats["count"] == len(sample_chunks)


def test_delete_by_source(vector_store, sample_chunks):
    """Test deleting chunks by source URL."""
    # Add chunks
    vector_store.add_chunks(sample_chunks)

    # Delete one source
    deleted = vector_store.delete_by_source(sample_chunks[0].source_url)
    assert deleted >= 1

    # Verify remaining count
    stats = vector_store.get_table_stats()
    assert stats["count"] < len(sample_chunks)


def test_clear_table(vector_store, sample_chunks):
    """Test clearing all data."""
    # Add chunks
    vector_store.add_chunks(sample_chunks)
    assert vector_store.get_table_stats()["count"] > 0

    # Clear
    vector_store.clear_table()
    assert vector_store.get_table_stats()["count"] == 0
