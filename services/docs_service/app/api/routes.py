import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.ingestion.doc_sources import create_all_sample_docs
from app.ingestion.embedder import VectorStore
from app.ingestion.pipeline import DocumentIngestionPipeline, create_sample_k8s_docs
from app.models.schemas import (
    IngestionRequest,
    IngestionResponse,
    RetrievalQuery,
    RetrievalResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def calculate_confidence(results: list) -> str:
    """
    Calculate confidence level based on similarity scores.

    Args:
        results: List of retrieval results with similarity_score

    Returns:
        Confidence level: "high", "medium", or "low"
    """
    if not results:
        return "low"

    avg_score = sum(r.similarity_score for r in results) / len(results)

    if avg_score >= 0.7:
        return "high"
    elif avg_score >= 0.5:
        return "medium"
    else:
        return "low"


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(query: RetrievalQuery) -> RetrievalResponse:
    """
    Retrieve relevant documentation chunks for a query.

    This endpoint:
    1. Embeds the query using the same model as document embedding
    2. Performs vector similarity search in LanceDB
    3. Returns top-k results with citation metadata
    4. Includes confidence scoring based on similarity scores

    Args:
        query: RetrievalQuery with query text and top_k

    Returns:
        RetrievalResponse with ranked results and confidence
    """
    try:
        vector_store = VectorStore()

        # Check if table exists
        if not vector_store.table_exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector store not initialized. Please ingest documents first.",
            )

        # Apply similarity threshold from query or use default
        similarity_threshold = query.similarity_threshold or settings.similarity_threshold

        # Perform search
        results = vector_store.search(
            query=query.query,
            top_k=query.top_k,
            similarity_threshold=similarity_threshold,
        )

        # Calculate confidence
        confidence = calculate_confidence(results)

        logger.info(
            f"Retrieved {len(results)} results for query: '{query.query[:50]}...' "
            f"with confidence: {confidence}"
        )

        return RetrievalResponse(
            query=query.query,
            results=results,
            retrieved_count=len(results),
            confidence=confidence,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {str(e)}",
        )


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_documents(request: IngestionRequest) -> IngestionResponse:
    """
    Ingest documentation from a directory into the vector store.

    This endpoint:
    1. Reads HTML/Markdown files from the specified directory
    2. Chunks them using heading-aware chunking with overlap
    3. Generates embeddings using sentence-transformers
    4. Stores in LanceDB for retrieval

    Args:
        request: IngestionRequest with source_path and options

    Returns:
        IngestionResponse with ingestion statistics
    """
    try:
        source_path = Path(request.source_path)

        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source path not found: {request.source_path}",
            )

        pipeline = DocumentIngestionPipeline()

        # Determine base URL from source path
        base_url = "https://kubernetes.io/docs"  # Default for K8s docs

        response = pipeline.ingest_directory(
            directory_path=source_path,
            base_url=base_url,
            doc_version=request.doc_version,
            recursive=True,
            force_reindex=request.force_reindex,
        )

        logger.info(f"Ingestion completed: {response.chunks_created} chunks created")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.post("/ingest/k8s", response_model=IngestionResponse)
async def ingest_kubernetes_docs(
    doc_version: str = "latest",
    force_reindex: bool = False,
) -> IngestionResponse:
    """
    Convenience endpoint to ingest Kubernetes documentation.

    If no K8s docs are available locally, creates sample docs for testing.

    Args:
        doc_version: Version identifier for the docs
        force_reindex: Whether to clear existing data first

    Returns:
        IngestionResponse with ingestion statistics
    """
    try:
        k8s_docs_path = Path(settings.docs_raw_path) / "kubernetes"

        # Create sample docs if directory doesn't exist or is empty
        if not k8s_docs_path.exists() or not any(k8s_docs_path.iterdir()):
            logger.info("Creating sample Kubernetes documentation...")
            create_sample_k8s_docs()

        pipeline = DocumentIngestionPipeline()
        response = pipeline.ingest_kubernetes_docs(
            docs_path=k8s_docs_path,
            doc_version=doc_version,
            force_reindex=force_reindex,
        )

        logger.info(f"K8s ingestion completed: {response.chunks_created} chunks created")

        return response

    except Exception as e:
        logger.error(f"Error during K8s ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"K8s ingestion failed: {str(e)}",
        )


@router.get("/stats")
async def get_stats():
    """
    Get statistics about the vector store.

    Returns information about the number of indexed documents
    and vector store status.
    """
    try:
        vector_store = VectorStore()
        stats = vector_store.get_table_stats()

        return {
            "service": settings.app_name,
            "vector_store": stats,
            "embedding_model": settings.embedding_model,
            "embedding_dimension": settings.embedding_dimension,
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.post("/ingest/all", response_model=IngestionResponse)
async def ingest_all_docs(
    force_reindex: bool = False,
) -> IngestionResponse:
    """
    Convenience endpoint to ingest all available documentation sources.

    Creates sample docs for:
    - Kubernetes
    - Python standard library
    - Docker

    Args:
        force_reindex: Whether to clear existing data first

    Returns:
        IngestionResponse with ingestion statistics
    """
    try:
        base_dir = Path(settings.docs_raw_path)

        # Create all sample documentation
        docs_paths = create_all_sample_docs(base_dir)
        logger.info(f"Created sample docs in: {list(docs_paths.keys())}")

        # Also create K8s docs if not already present
        k8s_dir = base_dir / "kubernetes"
        if not k8s_dir.exists() or not any(k8s_dir.iterdir()):
            create_sample_k8s_docs()
            docs_paths["kubernetes"] = k8s_dir

        # Ingest all documentation
        pipeline = DocumentIngestionPipeline()

        if force_reindex:
            pipeline.vector_store.clear_table()
            logger.info("Cleared existing vector store")

        total_chunks = 0
        total_docs = 0
        start_time = __import__("time").time()

        # Base URLs for different doc sources
        base_urls = {
            "kubernetes": "https://kubernetes.io/docs",
            "python": "https://docs.python.org/3",
            "docker": "https://docs.docker.com",
        }

        for doc_source, doc_path in docs_paths.items():
            try:
                base_url = base_urls.get(doc_source, f"https://{doc_source}.io/docs")

                response = pipeline.ingest_directory(
                    directory_path=doc_path,
                    base_url=base_url,
                    doc_version="latest",
                    recursive=True,
                    force_reindex=False,  # Already cleared above if needed
                )

                total_chunks += response.chunks_created
                total_docs += response.documents_processed

                logger.info(
                    f"Ingested {doc_source}: {response.chunks_created} chunks "
                    f"from {response.documents_processed} docs"
                )

            except Exception as e:
                logger.error(f"Error ingesting {doc_source}: {e}")
                continue

        elapsed_time = __import__("time").time() - start_time

        final_response = IngestionResponse(
            status="success",
            chunks_created=total_chunks,
            documents_processed=total_docs,
            elapsed_seconds=round(elapsed_time, 2),
        )

        logger.info(
            f"All docs ingestion completed: {total_chunks} chunks "
            f"from {total_docs} documents in {elapsed_time:.2f}s"
        )

        return final_response

    except Exception as e:
        logger.error(f"Error during all docs ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"All docs ingestion failed: {str(e)}",
        )


@router.delete("/clear")
async def clear_vector_store():
    """
    Clear all data from the vector store.

    Use with caution - this deletes all indexed documents.
    """
    try:
        vector_store = VectorStore()
        vector_store.clear_table()

        logger.info("Vector store cleared")

        return {
            "status": "success",
            "message": "Vector store cleared successfully",
        }

    except Exception as e:
        logger.error(f"Error clearing vector store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear vector store: {str(e)}",
        )
