import logging

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from app.core.config import settings
from app.tools.base import ToolName

logger = logging.getLogger(__name__)


class IntentClassification(BaseModel):
    """Structured intent classification from LLM."""

    tool: str = Field(
        description="The tool to use: 'docs_search', 'web_guide', 'sandbox_run', or 'code_scan'"
    )
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    reasoning: str | None = Field(
        None, description="Brief explanation of why this tool was selected"
    )


def route_request_with_llm(query: str, has_code: bool = False) -> tuple[ToolName, float]:
    """
    Use Ollama with structured output to classify user intent and route to the appropriate tool.

    This function attempts LLM-based intent classification first, then falls back to
    deterministic keyword matching if the LLM response is malformed or unavailable.

    Args:
        query: User query string
        has_code: Whether code snippet is provided

    Returns:
        Tuple of (selected_tool, confidence_score)
    """
    # Explicit code takes priority: it needs the sandbox
    if has_code:
        logger.info("Code detected - routing to SANDBOX")
        return ToolName.SANDBOX, 1.0

    try:
        # Initialize Ollama with structured output
        llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.0,
            timeout=10.0,
        )

        # Structured LLM call with guided generation
        llm_with_structure = llm.with_structured_output(IntentClassification)

        # Create classification prompt
        prompt = f"""You are an intelligent routing agent. Analyze the user's query and classify their intent into one of these tools:

1. **docs_search**: For questions about documentation, APIs, concepts, "how does X work", configuration, tutorials already in our knowledge base (Kubernetes, Python, Docker, FastAPI, LangChain).

2. **web_guide**: For queries requiring current information, finding external resources, GitHub repositories, latest tutorials, blog posts, online articles, or anything NOT in our local docs.

3. **sandbox_run**: For executing code, testing code snippets, running Python scripts, debugging runtime behavior.

4. **code_scan**: For security analysis, vulnerability scanning, code review, checking for bugs, analyzing code quality.

**User Query:** {query}

Classify the intent and provide your confidence (0.0-1.0).
"""

        # Invoke LLM with timeout
        result = llm_with_structure.invoke(prompt)

        # Map LLM tool names to ToolName enum
        tool_mapping = {
            "docs_search": ToolName.DOCS,
            "web_guide": ToolName.WEB,
            "sandbox_run": ToolName.SANDBOX,
            "code_scan": ToolName.SANDBOX,  # Scanner uses sandbox service
        }

        selected_tool = tool_mapping.get(result.tool, ToolName.DOCS)
        confidence = result.confidence

        logger.info(
            f"LLM routing: tool={result.tool} -> {selected_tool.value}, "
            f"confidence={confidence:.2f}, reasoning={result.reasoning}"
        )

        return selected_tool, confidence

    except Exception as e:
        logger.warning(f"LLM routing failed, using keyword fallback: {e}")
        # Fallback to deterministic keyword matching
        return route_request_keyword_fallback(query, has_code)


def route_request_keyword_fallback(query: str, has_code: bool = False) -> tuple[ToolName, float]:
    """
    Deterministic keyword-based routing fallback when LLM classification fails.

    This ensures the system remains functional even if Ollama is unavailable
    or returns malformed responses.

    Args:
        query: User query string
        has_code: Whether code snippet is provided

    Returns:
        Tuple of (selected_tool, confidence_score)
    """
    # Explicit code takes priority
    if has_code:
        return ToolName.SANDBOX, 1.0

    query_lower = query.lower()

    # Sandbox/Scanner keywords
    sandbox_keywords = [
        "run this code",
        "run code",
        "execute code",
        "test this code",
        "scan this code",
        "vulnerability",
        "security scan",
        "check for bugs",
        "analyze code",
        "code quality",
    ]

    # Web guide keywords
    web_keywords = [
        "find tutorials",
        "search the web",
        "github repository",
        "github repo",
        "latest articles",
        "online resources",
        "blog post",
        "find examples",
        "search for",
        "look up",
    ]

    # Documentation keywords (implicit - anything asking "how", "what", "explain")
    docs_keywords = [
        "how does",
        "what is",
        "explain",
        "documentation",
        "kubernetes",
        "python",
        "docker",
        "fastapi",
        "api reference",
    ]

    # Priority: Sandbox > Web > Docs
    if any(keyword in query_lower for keyword in sandbox_keywords):
        logger.info("Keyword fallback: routing to SANDBOX")
        return ToolName.SANDBOX, 0.8

    if any(keyword in query_lower for keyword in web_keywords):
        logger.info("Keyword fallback: routing to WEB")
        return ToolName.WEB, 0.8

    if any(keyword in query_lower for keyword in docs_keywords):
        logger.info("Keyword fallback: routing to DOCS")
        return ToolName.DOCS, 0.8

    # Default to docs for general queries
    logger.info("Keyword fallback: default routing to DOCS")
    return ToolName.DOCS, 0.5


def route_request(query: str, has_code: bool = False) -> ToolName:
    """
    Main routing function - routes user queries to the appropriate tool.

    This function attempts LLM-based classification first, then falls back
    to keyword matching. Returns only the ToolName for backward compatibility.

    Args:
        query: User query string
        has_code: Whether code snippet is provided

    Returns:
        ToolName enum value (DOCS, WEB, or SANDBOX)
    """
    tool, confidence = route_request_with_llm(query, has_code)
    return tool
