import json
import os
import re
from typing import ClassVar

import httpx
from app.schema.search_result import SearchResult


class OllamaSummarizerError(Exception):
    """Raised when the Ollama summarization request fails."""


class OllamaSummarizer:
    RESPONSE_SCHEMA: ClassVar[dict] = {
        "type": "object",
        "properties": {
            "explanation": {
                "type": "string",
            }
        },
        "required": ["explanation"],
        "additionalProperties": False,
    }

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")
        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            )
        ).rstrip("/")
        self.timeout = timeout
        self.transport = transport

    @staticmethod
    def _build_messages(
        query: str,
        result: SearchResult,
    ) -> list[dict[str, str]]:
        system_message = """
You write concise, factual relevance explanations for search results.

Your task is to explain why the specific result is useful for the user's query.

STRICT RULES:
- Return exactly one clear, informative sentence.
- Use no more than 25 words.
- Start with the result's name or subject, not the query.
- Explain the result's actual relevance to the query.
- Never describe what the user asked or what the query is about.
- Never describe your reasoning or repeat these instructions.
- Use only facts supported by the supplied title and snippet.
- Never invent features, content, capabilities, or claims.
- If the snippet is missing, use only what the title establishes.
- If relevance cannot be established from the available information, state that clearly.
- Do not use generic phrases such as "This result is useful because".

GOOD EXAMPLES:

Query: "How can I build a REST API using Python?"
Title: "FastAPI Documentation"
Snippet: "FastAPI is a modern web framework for building APIs with Python."
Explanation: "FastAPI's documentation explains how to build APIs with Python."

Query: "Where can I find Python documentation?"
Title: "Python Official Documentation"
Snippet: "No snippet available."
Explanation: "The Python Official Documentation is a relevant starting point for Python documentation."

BAD EXAMPLES:
- "The user asks how to build a REST API with Python."
- "The query is about finding Python documentation."
- "This result is useful because it is relevant to the query."

Return only the structured output requested by the response schema.
""".strip()

        user_data = {
            "query": query.strip(),
            "title": result.title,
            "snippet": result.snippet.strip() or "No snippet available.",
        }

        return [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": json.dumps(user_data, ensure_ascii=False),
            },
        ]

    @staticmethod
    def _normalize_explanation(text: str) -> str:
        text = " ".join(text.split())
        text = text.strip('"').strip("'")

        # Reject explanations that describe the query instead of the result.
        invalid_starts = (
            "the user asks",
            "the query asks",
            "the query is",
            "the user wants",
            "we are given",
            "we must",
            "key points",
        )

        if text.lower().startswith(invalid_starts):
            return ""

        # Keep only the first sentence.
        sentences = re.split(r"(?<=[.!?])\s+", text)
        text = sentences[0].strip()

        # Enforce the prompt's 25-word limit.
        words = text.split()

        if len(words) > 25:
            text = " ".join(words[:25]).rstrip(".,;:") + "."

        return text.strip()

    async def summarize(
        self,
        query: str,
        result: SearchResult,
    ) -> str:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": self._build_messages(query, result),
                        "stream": False,
                        "think": False,
                        "format": self.RESPONSE_SCHEMA,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 256,
                        },
                    },
                )

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            raise OllamaSummarizerError(
                "Ollama summarization request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise OllamaSummarizerError(
                f"Ollama returned HTTP {exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:
            raise OllamaSummarizerError("Could not connect to Ollama.") from exc

        except ValueError as exc:
            raise OllamaSummarizerError("Ollama returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise OllamaSummarizerError("Unexpected Ollama response format.")

        message = data.get("message")

        if not isinstance(message, dict):
            raise OllamaSummarizerError("Ollama response has no message.")

        content = message.get("content")

        if not isinstance(content, str) or not content.strip():
            raise OllamaSummarizerError("Ollama returned an empty explanation.")

        try:
            structured_output = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaSummarizerError(
                "Ollama did not return valid structured output."
            ) from exc

        explanation = structured_output.get("explanation")

        if not isinstance(explanation, str) or not explanation.strip():
            raise OllamaSummarizerError("Ollama returned an invalid explanation.")

        normalized = self._normalize_explanation(explanation)

        if not normalized:
            raise OllamaSummarizerError("Ollama returned an empty explanation.")

        return normalized
