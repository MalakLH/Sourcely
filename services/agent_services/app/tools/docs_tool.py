import asyncio
import logging

import httpx
from langchain_core.exceptions import LangChainException
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.tools.base import ToolName, ToolRequest, ToolResult, ToolStatus

logger = logging.getLogger(__name__)

DOCS_SERVICE_URL = settings.docs_service_url


async def retrieve_from_docs_service(
    query: str,
    top_k: int = 5,
) -> dict | None:
    """
    Call the docs-service /retrieve endpoint asynchronously.

    Args:
        query: Search query
        top_k: Number of results to retrieve

    Returns:
        Response dict from docs-service or None on error
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{DOCS_SERVICE_URL}/retrieve",
                json={
                    "query": query,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        logger.error(f"Error calling docs-service: {e}")
        return None


def generate_grounded_answer(query: str, retrieval_response: dict) -> tuple[str, list[str]]:
    """
    Generate an LLM-grounded answer from retrieved documentation chunks.

    Uses Ollama to synthesize an answer strictly based on retrieved context,
    with numbered Markdown citations.

    Args:
        query: Original user query
        retrieval_response: Response from docs-service /retrieve endpoint

    Returns:
        Tuple of (generated_answer, sources_list)
    """
    if not retrieval_response or not retrieval_response.get("results"):
        return "No relevant documentation found for your query.", []

    results = retrieval_response["results"]
    confidence = retrieval_response.get("confidence", "unknown")

    # Build context from retrieved chunks
    context_parts = []
    sources = []

    for idx, result in enumerate(results, 1):
        section_title = result.get("section_title", "Unknown Section")
        content = result.get("content", "")
        source_url = result.get("source_url", "")
        heading_path = result.get("heading_path", "")

        context_parts.append(
            f"[{idx}] {heading_path or section_title}\n{content}\nSource: {source_url}\n"
        )
        sources.append(source_url)

    context = "\n---\n".join(context_parts)

    # Create prompt for LLM
    prompt = f"""You are a helpful documentation assistant. 
    Answer the user's question based STRICTLY on the provided documentation context. 
    Do not add information beyond what's in the context.

If the context doesn't contain enough information to answer the question, 
say so clearly.

Include numbered citations [1], [2], etc. in your answer to reference 
specific documentation sections.

User Question: {query}

Documentation Context:
{context}

Instructions:
- Provide a clear, concise answer
- Use numbered citations [1], [2], etc. when referencing the documentation
- Stay grounded in the provided context only
- If information is missing or unclear, acknowledge it

Answer:"""

    try:
        # Initialize Ollama LLM with extended timeout
        llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.ollama_temperature,
            timeout=120.0,  # 120 second timeout
        )

        # Generate answer
        response = llm.invoke(prompt)
        generated_answer = response.content.strip()

        # Append confidence and sources
        answer_with_metadata = (
            f"{generated_answer}\n\n---\n**Confidence:** {confidence}\n**Sources:**\n"
        )
        for idx, source in enumerate(sources, 1):
            answer_with_metadata += f"[{idx}] {source}\n"

        return answer_with_metadata, sources

    except (LangChainException, OSError, TimeoutError, ValueError) as e:
        logger.error(f"Error generating LLM answer: {e}")
        # Fallback to simple concatenation
        return format_cited_answer_fallback(retrieval_response)


def format_cited_answer_fallback(retrieval_response: dict) -> tuple[str, list[str]]:
    """
    Fallback method to format retrieved chunks without LLM generation.

    Args:
        retrieval_response: Response from docs-service /retrieve endpoint

    Returns:
        Tuple of (formatted_content, sources_list)
    """
    if not retrieval_response or not retrieval_response.get("results"):
        return "No relevant documentation found.", []

    results = retrieval_response["results"]
    confidence = retrieval_response.get("confidence", "unknown")

    # Build answer with citations
    answer_parts = [
        f"Found {len(results)} relevant documentation sections (confidence: {confidence}):\n"
    ]

    sources = []

    for idx, result in enumerate(results, 1):
        section_title = result.get("section_title", "Unknown Section")
        content = result.get("content", "")
        source_url = result.get("source_url", "")
        heading_path = result.get("heading_path", "")
        similarity = result.get("similarity_score", 0.0)

        # Format citation
        citation = f"\n**[{idx}] {section_title}**"
        if heading_path:
            citation += f" ({heading_path})"
        citation += f" [similarity: {similarity:.3f}]\n"

        # Add content snippet (first 400 chars)
        snippet = content[:400] + "..." if len(content) > 400 else content
        citation += f"{snippet}\n"
        citation += f"Source: {source_url}\n"

        answer_parts.append(citation)
        sources.append(source_url)

    return "\n".join(answer_parts), sources


def run_docs_tool(request: ToolRequest) -> ToolResult:
    """
    Execute documentation retrieval and generate LLM-grounded answer.

    This tool:
    1. Calls the docs-service /retrieve endpoint
    2. Retrieves relevant documentation chunks from LanceDB
    3. Uses Ollama to generate an answer grounded in retrieved context
    4. Returns answer with numbered Markdown citations and source URLs

    Args:
        request: ToolRequest with query

    Returns:
        ToolResult with LLM-generated cited answer or error message
    """
    try:
        # Call docs-service asynchronously
        retrieval_response = asyncio.run(
            retrieve_from_docs_service(
                query=request.query,
                top_k=5,
            )
        )

        if not retrieval_response:
            return ToolResult(
                status=ToolStatus.ERROR,
                tool=ToolName.DOCS,
                content="Failed to connect to documentation service.",
                sources=[],
            )

        # Generate LLM-grounded answer with citations
        content, sources = generate_grounded_answer(request.query, retrieval_response)

        # Format sources as list of dicts for ToolResult schema
        formatted_sources = [{"url": url, "title": url} for url in sources if url]

        return ToolResult(
            status=ToolStatus.SUCCESS,
            tool=ToolName.DOCS,
            content=content,
            sources=formatted_sources,
            metadata={"confidence": retrieval_response.get("confidence", "unknown")},
        )

    except (httpx.HTTPError, LangChainException, OSError, RuntimeError, ValueError) as e:
        logger.error(f"Error in docs_tool: {e}")
        return ToolResult(
            status=ToolStatus.ERROR,
            tool=ToolName.DOCS,
            content=f"Documentation retrieval error: {str(e)}",
            sources=[],
        )
