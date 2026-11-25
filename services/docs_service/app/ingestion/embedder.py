import logging

import lancedb
import pyarrow as pa
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.schemas import DocumentChunk, RetrievalResult

logger = logging.getLogger(__name__)

# Global embedding model (loaded once on startup)
_embedding_model: SentenceTransformer | None = None


def initialize_embedding_model() -> None:
    """Initialize the embedding model on application startup."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully")


def get_embedding_model() -> SentenceTransformer:
    """Get the initialized embedding model."""
    if _embedding_model is None:
        initialize_embedding_model()
    return _embedding_model


class VectorStore:
    """
    Manages LanceDB vector storage for document embeddings.

    Handles embedding generation, storage, and similarity search.
    """

    def __init__(self, db_path: str | None = None, table_name: str | None = None):
        self.db_path = db_path or settings.lancedb_path
        self.table_name = table_name or settings.docs_table_name
        self.db = lancedb.connect(self.db_path)
        self.embedding_model = get_embedding_model()

    def get_schema(self) -> pa.Schema:
        """Define LanceDB table schema."""
        return pa.schema(
            [
                pa.field("chunk_id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("source_url", pa.string()),
                pa.field("section_title", pa.string()),
                pa.field("doc_version", pa.string()),
                pa.field("heading_path", pa.string()),
                pa.field("chunk_index", pa.int64()),
                pa.field("token_count", pa.int64()),
                pa.field("created_at", pa.string()),
                pa.field(
                    "vector",
                    pa.list_(pa.float32(), settings.embedding_dimension),
                ),
            ]
        )

    def create_table(self, overwrite: bool = False) -> None:
        """Create the LanceDB table."""
        if overwrite and self.table_name in self.db.table_names():
            self.db.drop_table(self.table_name)
            logger.info(f"Dropped existing table: {self.table_name}")

        # Create empty table with schema
        empty_data = []
        self.db.create_table(
            self.table_name,
            data=empty_data,
            schema=self.get_schema(),
            mode="create" if not overwrite else "overwrite",
        )
        logger.info(f"Created table: {self.table_name}")
        
    def table_exists(self) -> bool:
        """Check if the table exists."""
        return self.table_name in self.db.table_names()

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            batch_size=32,
        )
        return embeddings.tolist()

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        # Extract texts for embedding
        texts = [chunk.content for chunk in chunks]
        logger.info(f"Generating embeddings for {len(texts)} chunks...")

        # Generate embeddings
        embeddings = self.embed_batch(texts)

        # Prepare data for insertion
        data = []
        for chunk, embedding in zip(chunks, embeddings, strict=False):
            data.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "source_url": chunk.source_url,
                    "section_title": chunk.section_title,
                    "doc_version": chunk.doc_version,
                    "heading_path": chunk.heading_path,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "created_at": chunk.created_at.isoformat(),
                    "vector": embedding,
                }
            )

        # Ensure table exists
        if not self.table_exists():
            self.create_table()

        # Add to LanceDB
        table = self.db.open_table(self.table_name)
        table.add(data)

        logger.info(f"Added {len(data)} chunks to {self.table_name}")
        return len(data)

    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float | None = None,
    ) -> list[RetrievalResult]:
        """
        Search for similar documents using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of RetrievalResult objects sorted by similarity
        """
        if not self.table_exists():
            logger.warning(f"Table {self.table_name} does not exist")
            return []

        # Generate query embedding
        query_embedding = self.embed_text(query)

        # Search LanceDB
        table = self.db.open_table(self.table_name)
        results = (
            table.search(query_embedding)
            .limit(top_k * 2)  # Fetch more for filtering
            .to_list()
        )

        # Convert to RetrievalResult objects
        retrieval_results = []
        for result in results:
            # Calculate similarity score (LanceDB returns distance, convert to similarity)
            distance = result.get("_distance", 0.0)
            # L2 distance to cosine similarity approximation
            similarity = 1.0 / (1.0 + distance)

            # Apply threshold if specified
            if similarity_threshold and similarity < similarity_threshold:
                continue

            retrieval_results.append(
                RetrievalResult(
                    content=result["content"],
                    source_url=result["source_url"],
                    section_title=result["section_title"],
                    heading_path=result["heading_path"],
                    similarity_score=round(similarity, 4),
                    chunk_id=result["chunk_id"],
                    doc_version=result["doc_version"],
                )
            )

            # Stop if we have enough results
            if len(retrieval_results) >= top_k:
                break

        return retrieval_results

    def get_table_stats(self) -> dict:
        """Get statistics about the vector store."""
        if not self.table_exists():
            return {"exists": False, "count": 0}

        table = self.db.open_table(self.table_name)
        count = table.count_rows()

        return {
            "exists": True,
            "count": count,
            "table_name": self.table_name,
            "db_path": self.db_path,
        }

    def delete_by_source(self, source_url: str) -> int:
        """
        Delete all chunks from a specific source URL.

        Args:
            source_url: Source URL to filter by

        Returns:
            Number of chunks deleted
        """
        if not self.table_exists():
            return 0

        table = self.db.open_table(self.table_name)
        initial_count = table.count_rows()

        # Delete rows matching source_url
        table.delete(f"source_url = '{source_url}'")

        final_count = table.count_rows()
        deleted = initial_count - final_count

        logger.info(f"Deleted {deleted} chunks from {source_url}")
        return deleted

    def clear_table(self) -> None:
        """Clear all data from the table."""
        if self.table_exists():
            self.db.drop_table(self.table_name)
            self.create_table()
            logger.info(f"Cleared table: {self.table_name}")
