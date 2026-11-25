from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.core.config import settings
from app.ingestion.embedder import initialize_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and cleanup on shutdown."""
    # Initialize embedding model on startup
    initialize_embedding_model()

    # Auto-ingest documentation if corpus is small
    try:
        from app.ingestion.embedder import VectorStore

        vector_store = VectorStore()

        # Check if we need to ingest
        if vector_store.table_exists():
            stats = vector_store.get_table_stats()
            chunk_count = stats.get("count", 0)

            if chunk_count < 20:
                logger.info(f"Low chunk count ({chunk_count}), triggering auto-ingestion...")
                from pathlib import Path

                from app.core.config import settings
                from app.ingestion.doc_sources import create_all_sample_docs
                from app.ingestion.pipeline import DocumentIngestionPipeline

                base_dir = Path(settings.docs_raw_path)
                docs_paths = create_all_sample_docs(base_dir)

                pipeline = DocumentIngestionPipeline()

                # Ingest all docs
                base_urls = {
                    "kubernetes": "https://kubernetes.io/docs",
                    "python": "https://docs.python.org/3",
                    "docker": "https://docs.docker.com",
                }

                total_chunks = 0
                for doc_source, doc_path in docs_paths.items():
                    try:
                        base_url = base_urls.get(doc_source, f"https://{doc_source}.io/docs")
                        response = pipeline.ingest_directory(
                            directory_path=doc_path,
                            base_url=base_url,
                            doc_version="latest",
                            recursive=True,
                            force_reindex=False,
                        )
                        total_chunks += response.chunks_created
                        logger.info(f"Auto-ingested {doc_source}: {response.chunks_created} chunks")
                    except Exception as e:
                        logger.error(f"Error auto-ingesting {doc_source}: {e}")

                logger.info(f"Auto-ingestion complete: {total_chunks} total chunks")
        else:
            logger.info("Vector store table does not exist, will be created on first ingestion")
    except Exception as e:
        logger.error(f"Error during auto-ingestion check: {e}")

    yield
    # Cleanup on shutdown if needed


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
