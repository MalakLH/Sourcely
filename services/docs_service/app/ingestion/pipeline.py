import logging
import time
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.ingestion.chunker import HeadingAwareChunker, generate_chunk_id
from app.ingestion.embedder import VectorStore
from app.models.schemas import DocumentChunk, IngestionResponse

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """
    End-to-end pipeline for ingesting documentation into the vector store.

    Processes HTML/Markdown files, chunks them, embeds them, and stores in LanceDB.
    """

    def __init__(self):
        self.chunker = HeadingAwareChunker(
            max_chunk_tokens=settings.max_chunk_tokens,
            min_chunk_tokens=settings.min_chunk_tokens,
            overlap_percent=settings.chunk_overlap_percent,
        )
        self.vector_store = VectorStore()

    def ingest_file(
        self,
        file_path: Path,
        source_url: str,
        doc_version: str = "latest",
    ) -> list[DocumentChunk]:
        """
        Ingest a single documentation file.

        Args:
            file_path: Path to the documentation file
            source_url: URL where the documentation is hosted
            doc_version: Version identifier for the documentation

        Returns:
            List of DocumentChunk objects created
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Processing file: {file_path}")

        # Read file content
        content = file_path.read_text(encoding="utf-8")

        # Determine file type and chunk accordingly
        file_extension = file_path.suffix.lower()

        if file_extension in [".html", ".htm"]:
            chunks = self.chunker.chunk_html_document(content, source_url)
        elif file_extension in [".md", ".markdown"]:
            chunks = self.chunker.chunk_markdown_document(content, source_url)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return []

        # Convert to DocumentChunk objects with metadata
        document_chunks = []
        for chunk in chunks:
            chunk_id = generate_chunk_id(chunk.content, source_url, chunk.chunk_index)

            document_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk.content,
                    source_url=source_url,
                    section_title=chunk.section_title,
                    doc_version=doc_version,
                    heading_path=chunk.heading_path,
                    chunk_index=chunk.chunk_index,
                    token_count=chunk.token_count,
                    created_at=datetime.utcnow(),
                )
            )

        logger.info(f"Created {len(document_chunks)} chunks from {file_path.name}")
        return document_chunks

    def ingest_directory(
        self,
        directory_path: Path,
        base_url: str,
        doc_version: str = "latest",
        recursive: bool = True,
        force_reindex: bool = False,
    ) -> IngestionResponse:
        """
        Ingest all documentation files from a directory.

        Args:
            directory_path: Path to directory containing documentation
            base_url: Base URL for the documentation site
            doc_version: Version identifier
            recursive: Whether to process subdirectories
            force_reindex: Whether to clear existing data first

        Returns:
            IngestionResponse with statistics
        """
        start_time = time.time()

        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        logger.info(f"Starting ingestion from: {directory_path}")

        # Clear existing data if force_reindex
        if force_reindex:
            logger.info("Force reindex enabled, clearing existing data...")
            self.vector_store.clear_table()

        # Find all documentation files
        patterns = ["*.html", "*.htm", "*.md", "*.markdown"]
        files = []

        for pattern in patterns:
            if recursive:
                files.extend(directory_path.rglob(pattern))
            else:
                files.extend(directory_path.glob(pattern))

        logger.info(f"Found {len(files)} documentation files")

        # Process each file
        all_chunks = []
        documents_processed = 0

        for file_path in files:
            try:
                # Generate source URL from file path using real URL mappings
                from app.ingestion.url_mappings import get_real_url

                relative_path = file_path.relative_to(directory_path)
                source_url = get_real_url(str(relative_path))

                # Ingest file
                chunks = self.ingest_file(file_path, source_url, doc_version)
                all_chunks.extend(chunks)
                documents_processed += 1

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        # Add all chunks to vector store
        if all_chunks:
            self.vector_store.add_chunks(all_chunks)

        elapsed_time = time.time() - start_time

        response = IngestionResponse(
            status="success",
            chunks_created=len(all_chunks),
            documents_processed=documents_processed,
            elapsed_seconds=round(elapsed_time, 2),
        )

        logger.info(
            f"Ingestion complete: {response.chunks_created} chunks "
            f"from {response.documents_processed} documents "
            f"in {response.elapsed_seconds}s"
        )

        return response

    def ingest_kubernetes_docs(
        self,
        docs_path: Path | None = None,
        doc_version: str = "latest",
        force_reindex: bool = False,
    ) -> IngestionResponse:
        """
        Convenience method to ingest Kubernetes documentation.

        Args:
            docs_path: Path to Kubernetes docs (defaults to settings.docs_raw_path)
            doc_version: Version identifier
            force_reindex: Whether to clear existing data first

        Returns:
            IngestionResponse with statistics
        """
        if docs_path is None:
            docs_path = Path(settings.docs_raw_path) / "kubernetes"

        base_url = "https://kubernetes.io/docs"

        return self.ingest_directory(
            directory_path=docs_path,
            base_url=base_url,
            doc_version=doc_version,
            recursive=True,
            force_reindex=force_reindex,
        )


def create_sample_k8s_docs() -> None:
    """
    Create sample Kubernetes documentation for testing.

    This creates minimal sample docs if no real K8s docs are available.
    """
    sample_docs_path = Path(settings.docs_raw_path) / "kubernetes"
    sample_docs_path.mkdir(parents=True, exist_ok=True)

    # Sample Kubernetes Pod documentation
    pod_doc = """# Pods

## Overview

Pods are the smallest deployable units of computing that you can create and manage in Kubernetes.

A Pod is a group of one or more containers, with shared storage and network resources, 
and a specification for how to run the containers.

## Pod Lifecycle

Pods follow a defined lifecycle, starting in the Pending phase, moving through Running 
if at least one of its primary containers starts OK, and then through either the 
Succeeded or Failed phases depending on whether any container in the Pod terminated in failure.

### Pod Phase

The phase of a Pod is a simple, high-level summary of where the Pod is in its lifecycle. 
Here are the possible values for phase:

- **Pending**: The Pod has been accepted by the Kubernetes cluster, but one or more 
of the containers has not been set up and made ready to run.
- **Running**: The Pod has been bound to a node, and all of the containers have 
been created. At least one container is still running, or is in the process 
of starting or restarting.
- **Succeeded**: All containers in the Pod have terminated in success, 
and will not be restarted.
- **Failed**: All containers in the Pod have terminated, and at least one container 
has terminated in failure.
- **Unknown**: For some reason the state of the Pod could not be obtained.

## Pod Templates

Pod templates are specifications for creating Pods, and are included in workload resources 
such as Deployments, Jobs, and DaemonSets.

Each controller for a workload resource uses the Pod template inside the workload object 
to make actual Pods.
"""

    pod_doc_path = sample_docs_path / "pods.md"
    pod_doc_path.write_text(pod_doc)
    logger.info(f"Created sample doc: {pod_doc_path}")

    # Sample Kubernetes Service documentation
    service_doc = """# Services

## Overview

An abstract way to expose an application running on a set of Pods as a network service.

With Kubernetes you don't need to modify your application to use an unfamiliar 
service discovery mechanism. Kubernetes gives Pods their own IP addresses and a single 
DNS name for a set of Pods, and can load-balance across them.

## Service Types

Kubernetes ServiceTypes allow you to specify what kind of Service you want.

### ClusterIP

Exposes the Service on a cluster-internal IP. Choosing this value makes the 
Service only reachable from within the cluster. This is the default ServiceType.

### NodePort

Exposes the Service on each Node's IP at a static port (the NodePort). 
A ClusterIP Service, to which the NodePort Service routes, is automatically created.

### LoadBalancer

Exposes the Service externally using a cloud provider's load balancer. 
NodePort and ClusterIP Services, to which the external load balancer routes, 
are automatically created.

### ExternalName

Maps the Service to the contents of the externalName field (e.g. foo.bar.example.com), 
by returning a CNAME record with its value.

## Service Discovery

Kubernetes supports 2 primary modes of finding a Service - environment variables and DNS.
"""

    service_doc_path = sample_docs_path / "services.md"
    service_doc_path.write_text(service_doc)
    logger.info(f"Created sample doc: {service_doc_path}")

    # Sample Kubernetes Deployment documentation
    deployment_doc = """# Deployments

## Overview

A Deployment provides declarative updates for Pods and ReplicaSets.

You describe a desired state in a Deployment, and the Deployment 
Controller changes the actual state to the desired state at a controlled rate.

## Use Cases

The following are typical use cases for Deployments:

- **Create a Deployment** to rollout a ReplicaSet. The ReplicaSet creates Pods in the background.
- **Declare the new state of the Pods** by updating the PodTemplateSpec of the Deployment.
- **Rollback to an earlier Deployment revision** if the current state of the Deployment 
is not stable.
- **Scale up the Deployment** to facilitate more load.
- **Pause the Deployment** to apply multiple fixes to its PodTemplateSpec.

## Creating a Deployment

The following is an example of a Deployment. It creates a ReplicaSet to bring up three nginx Pods.

Deployments can be created using kubectl commands or YAML manifests. 
The manifest approach is recommended for production use.

## Updating a Deployment

A Deployment's rollout is triggered if and only if the Deployment's Pod 
template (that is, .spec.template) is changed. Other updates, such as 
scaling the Deployment, do not trigger a rollout.
"""

    deployment_doc_path = sample_docs_path / "deployments.md"
    deployment_doc_path.write_text(deployment_doc)
    logger.info(f"Created sample doc: {deployment_doc_path}")

    logger.info(f"Sample K8s documentation created in: {sample_docs_path}")
