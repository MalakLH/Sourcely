import pytest

from app.ingestion.chunker import HeadingAwareChunker, generate_chunk_id


@pytest.fixture
def chunker():
    return HeadingAwareChunker(max_chunk_tokens=512, min_chunk_tokens=50, overlap_percent=0.125)


def test_chunk_markdown_simple(chunker):
    """Test chunking simple Markdown with headings."""
    markdown = """# Main Title

This is the introduction.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""
    chunks = chunker.chunk_markdown_document(markdown, "https://example.com/doc")

    assert len(chunks) >= 3
    assert any("Main Title" in chunk.content for chunk in chunks)
    assert any("Section 1" in chunk.content for chunk in chunks)


def test_chunk_html_simple(chunker):
    """Test chunking simple HTML with headings."""
    html = """
    <h1>Main Title</h1>
    <p>Introduction paragraph.</p>
    <h2>Section 1</h2>
    <p>Section 1 content.</p>
    <h3>Subsection 1.1</h3>
    <p>Subsection content.</p>
    """
    chunks = chunker.chunk_html_document(html, "https://example.com/doc")

    assert len(chunks) >= 2
    assert any("Main Title" in chunk.content for chunk in chunks)


def test_heading_path_building(chunker):
    """Test hierarchical heading path construction."""
    markdown = """# Level 1

Content 1

## Level 2

Content 2

### Level 3

Content 3
"""
    chunks = chunker.chunk_markdown_document(markdown, "https://example.com/doc")

    # Check that heading paths are hierarchical
    level_3_chunks = [c for c in chunks if "Level 3" in c.content]
    if level_3_chunks:
        assert ">" in level_3_chunks[0].heading_path


def test_chunk_id_generation():
    """Test chunk ID generation is deterministic."""
    chunk_id_1 = generate_chunk_id("test content", "https://example.com", 0)
    chunk_id_2 = generate_chunk_id("test content", "https://example.com", 0)
    chunk_id_3 = generate_chunk_id("different content", "https://example.com", 0)

    assert chunk_id_1 == chunk_id_2
    assert chunk_id_1 != chunk_id_3
    assert len(chunk_id_1) == 16


def test_token_counting(chunker):
    """Test token counting."""
    text = "This is a test sentence with multiple words."
    count = chunker.count_tokens(text)

    assert count > 0
    assert isinstance(count, int)


def test_chunk_large_section_with_overlap(chunker):
    """Test that large sections are split with overlap."""
    # Create a large section that exceeds max_chunk_tokens
    large_content = " ".join([f"Sentence {i}." for i in range(200)])
    markdown = f"# Large Section\n\n{large_content}"

    chunks = chunker.chunk_markdown_document(markdown, "https://example.com/doc")

    # Should create multiple chunks
    assert len(chunks) > 1

    # Check that chunks have token counts
    for chunk in chunks:
        assert chunk.token_count > 0
        assert chunk.token_count <= chunker.max_chunk_tokens
