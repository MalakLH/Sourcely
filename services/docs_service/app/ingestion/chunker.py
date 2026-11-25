import hashlib
import re
from dataclasses import dataclass

import tiktoken
from bs4 import BeautifulSoup, NavigableString, Tag


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""

    content: str
    heading_path: str
    section_title: str
    chunk_index: int
    token_count: int
    start_heading_level: int


class HeadingAwareChunker:
    """
    Chunks HTML/Markdown documentation by heading structure with overlap.

    Splits documents at H1, H2, H3 boundaries and maintains 10-15% token overlap
    between consecutive chunks to preserve context.
    """

    def __init__(
        self,
        max_chunk_tokens: int = 512,
        min_chunk_tokens: int = 50,
        overlap_percent: float = 0.125,
    ):
        self.max_chunk_tokens = max_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens
        self.overlap_percent = overlap_percent
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def extract_headings_from_html(self, html_content: str) -> list[tuple[int, str, str]]:
        """
        Extract heading hierarchy from HTML.

        Returns:
            List of (level, title, content) tuples where content includes
            everything until the next heading of equal or higher level.
        """
        soup = BeautifulSoup(html_content, "lxml")

        # Find all headings (h1-h3)
        headings = []
        heading_tags = soup.find_all(["h1", "h2", "h3"])

        for _i, heading_tag in enumerate(heading_tags):
            level = int(heading_tag.name[1])  # Extract number from h1, h2, h3
            title = heading_tag.get_text(strip=True)

            # Collect content until next heading of same or higher level
            content_parts = []
            current = heading_tag.next_sibling

            while current:
                # Stop if we hit a heading of equal or higher level
                if isinstance(current, Tag) and current.name in ["h1", "h2", "h3"]:
                    current_level = int(current.name[1])
                    if current_level <= level:
                        break

                # Collect text content
                if isinstance(current, NavigableString):
                    text = str(current).strip()
                    if text:
                        content_parts.append(text)
                elif isinstance(current, Tag):
                    # Skip nested headings h4-h6 but include their content
                    if current.name not in ["h1", "h2", "h3"]:
                        text = current.get_text(strip=True)
                        if text:
                            content_parts.append(text)

                current = current.next_sibling

            content = "\n".join(content_parts)
            headings.append((level, title, content))

        return headings

    def extract_headings_from_markdown(self, markdown_content: str) -> list[tuple[int, str, str]]:
        """
        Extract heading hierarchy from Markdown.

        Returns:
            List of (level, title, content) tuples.
        """
        lines = markdown_content.split("\n")
        headings = []
        current_heading = None
        current_content = []

        heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$")

        for line in lines:
            match = heading_pattern.match(line)

            if match:
                # Save previous heading if exists
                if current_heading:
                    level, title = current_heading
                    content = "\n".join(current_content).strip()
                    headings.append((level, title, content))

                # Start new heading
                level = len(match.group(1))
                title = match.group(2).strip()
                current_heading = (level, title)
                current_content = []
            else:
                # Accumulate content
                if current_heading:
                    current_content.append(line)

        # Save last heading
        if current_heading:
            level, title = current_heading
            content = "\n".join(current_content).strip()
            headings.append((level, title, content))

        return headings

    def build_heading_path(self, headings: list[tuple[int, str, str]], current_index: int) -> str:
        """
        Build hierarchical heading path (e.g., 'Overview > Concepts > Pods').
        """
        if current_index < 0 or current_index >= len(headings):
            return ""

        current_level, current_title, _ = headings[current_index]
        path_parts = [current_title]

        # Walk backwards to find parent headings
        for i in range(current_index - 1, -1, -1):
            level, title, _ = headings[i]
            if level < current_level:
                path_parts.insert(0, title)
                current_level = level
            if level == 1:
                break

        return " > ".join(path_parts)

    def chunk_with_overlap(
        self, headings: list[tuple[int, str, str]], source_url: str
    ) -> list[Chunk]:
        """
        Create chunks from heading sections with token-based overlap.

        Args:
            headings: List of (level, title, content) tuples
            source_url: Source URL for the document

        Returns:
            List of Chunk objects with overlap
        """
        chunks = []
        chunk_counter = 0

        for idx, (level, title, content) in enumerate(headings):
            if not content.strip():
                continue

            heading_path = self.build_heading_path(headings, idx)
            full_text = f"{title}\n\n{content}"

            token_count = self.count_tokens(full_text)

            # If section fits in one chunk
            if token_count <= self.max_chunk_tokens:
                    chunks.append(
                        Chunk(
                            content=full_text,
                            heading_path=heading_path,
                            section_title=title,
                            chunk_index=chunk_counter,
                            token_count=token_count,
                            start_heading_level=level,
                        )
                    )
                    chunk_counter += 1
            else:
                # Split large section into multiple chunks with overlap
                sentences = self._split_into_sentences(full_text)
                current_chunk_text = []
                current_tokens = 0

                overlap_tokens = int(self.max_chunk_tokens * self.overlap_percent)
                overlap_buffer = []

                for sentence in sentences:
                    sentence_tokens = self.count_tokens(sentence)

                    # Check if adding this sentence exceeds limit
                    if current_tokens + sentence_tokens > self.max_chunk_tokens:
                        # Save current chunk if it meets minimum
                        if current_tokens >= self.min_chunk_tokens:
                            chunk_text = " ".join(current_chunk_text)
                            chunks.append(
                                Chunk(
                                    content=chunk_text,
                                    heading_path=heading_path,
                                    section_title=title,
                                    chunk_index=chunk_counter,
                                    token_count=current_tokens,
                                    start_heading_level=level,
                                )
                            )
                            chunk_counter += 1

                            # Build overlap from end of current chunk
                            overlap_buffer = self._get_overlap_text(
                                current_chunk_text, overlap_tokens
                            )

                        # Start new chunk with overlap
                        current_chunk_text = overlap_buffer + [sentence]
                        current_tokens = self.count_tokens(" ".join(current_chunk_text))
                    else:
                        current_chunk_text.append(sentence)
                        current_tokens += sentence_tokens

                # Save final chunk
                if current_tokens >= self.min_chunk_tokens:
                    chunk_text = " ".join(current_chunk_text)
                    chunks.append(
                        Chunk(
                            content=chunk_text,
                            heading_path=heading_path,
                            section_title=title,
                            chunk_index=chunk_counter,
                            token_count=current_tokens,
                            start_heading_level=level,
                        )
                    )
                    chunk_counter += 1

        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences for chunking."""
        # Simple sentence splitter (can be enhanced with spaCy/NLTK)
        sentence_pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
        sentences = sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_text(self, sentences: list[str], target_tokens: int) -> list[str]:
        """Get the last N sentences that fit within target_tokens."""
        overlap = []
        total_tokens = 0

        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if total_tokens + sentence_tokens <= target_tokens:
                overlap.insert(0, sentence)
                total_tokens += sentence_tokens
            else:
                break

        return overlap

    def chunk_html_document(self, html_content: str, source_url: str) -> list[Chunk]:
        """
        Main method to chunk HTML documentation.

        Args:
            html_content: Raw HTML content
            source_url: Source URL of the document

        Returns:
            List of Chunk objects
        """
        headings = self.extract_headings_from_html(html_content)
        return self.chunk_with_overlap(headings, source_url)

    def chunk_markdown_document(self, markdown_content: str, source_url: str) -> list[Chunk]:
        """
        Main method to chunk Markdown documentation.

        Args:
            markdown_content: Raw Markdown content
            source_url: Source URL of the document

        Returns:
            List of Chunk objects
        """
        headings = self.extract_headings_from_markdown(markdown_content)
        return self.chunk_with_overlap(headings, source_url)


def generate_chunk_id(content: str, source_url: str, chunk_index: int) -> str:
    """Generate a unique, deterministic chunk ID."""
    data = f"{source_url}::{chunk_index}::{content[:100]}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]
