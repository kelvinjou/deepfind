import os
import sys
import re
from collections import Counter
from dataclasses import dataclass
from pydantic import FilePath
import fitz  # PyMuPDF
from lib.util.preprocessing.semantic_chunking import semantic_chunk_text

# This utility file is for processing PDF files.
# The goal is to take in a PDF file and return text chunks with page metadata.
# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class PDFChunk:
    """Represents a chunk of PDF text with page metadata."""
    content: str
    chunk_index: int
    page_start: int  # 1-indexed page number where chunk starts
    page_end: int    # 1-indexed page number where chunk ends


def _sanitize_text(text: str) -> str:
    """
    Remove problematic Unicode characters that cause database errors.

    Removes null bytes (\x00, \u0000) and other control characters
    that PostgreSQL cannot store in text columns.
    """
    # Remove null bytes
    text = text.replace('\x00', '')
    # Remove other problematic control characters (except newline, tab, carriage return)
    text = ''.join(char for char in text if char == '\n' or char ==
                   '\t' or char == '\r' or not (0 <= ord(char) < 32))
    return text


def _strip_headers_footers(pages: list[tuple[int, str]], min_occurrences: int = 2) -> list[tuple[int, str]]:
    """
    Remove repeated headers/footers from page text.

    Identifies lines that appear on multiple pages (likely headers/footers)
    and removes them. Also strips common patterns like page numbers and timestamps.

    Args:
        pages: List of (page_number, page_text) tuples
        min_occurrences: Minimum times a line must appear to be considered a header/footer

    Returns:
        Cleaned list of (page_number, page_text) tuples
    """
    if len(pages) < 2:
        return pages

    # Split each page into lines and count occurrences across pages
    page_lines = []
    line_counter = Counter()

    for page_num, page_text in pages:
        lines = [line.strip()
                 for line in page_text.split('\n') if line.strip()]
        page_lines.append((page_num, lines))
        # Count unique lines per page (avoid counting duplicates within same page)
        unique_lines = set(lines)
        for line in unique_lines:
            line_counter[line] += 1

    # Find lines that appear on multiple pages (likely headers/footers)
    repeated_lines = {line for line,
                      count in line_counter.items() if count >= min_occurrences}

    # Patterns to remove (timestamps, page numbers, URLs)
    patterns_to_remove = [
        # Timestamps like "1/8/26, 1:39 PM"
        r'^\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*(AM|PM)?$',
        r'^\d+/\d+$',  # Page numbers like "1/6"
        r'^Page\s+\d+\s*(of\s+\d+)?$',  # "Page 1" or "Page 1 of 6"
        r'^https?://\S+$',  # URLs on their own line
    ]
    compiled_patterns = [re.compile(p, re.IGNORECASE)
                         for p in patterns_to_remove]

    def should_remove_line(line: str) -> bool:
        """Check if a line should be removed."""
        # Remove if it's a repeated header/footer
        if line in repeated_lines:
            return True
        # Remove if it matches a noise pattern
        for pattern in compiled_patterns:
            if pattern.match(line):
                return True
        return False

    # Filter out headers/footers from each page
    cleaned_pages = []
    for page_num, lines in page_lines:
        cleaned_lines = [
            line for line in lines if not should_remove_line(line)]
        cleaned_text = '\n'.join(cleaned_lines)
        if cleaned_text.strip():
            cleaned_pages.append((page_num, cleaned_text))

    return cleaned_pages


def _extract_text_by_page(file_path: FilePath) -> list[tuple[int, str]]:
    """
    Extract text from each page of a PDF.

    Returns:
        List of tuples (page_number, page_text) where page_number is 1-indexed.
    """
    doc = fitz.open(str(file_path))
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        # Sanitize text to remove null bytes and other problematic characters
        text = _sanitize_text(text)
        if text.strip():  # Only include pages with text
            pages.append((page_num + 1, text))  # 1-indexed page numbers

    doc.close()
    return pages


def _extract_full_text(file_path: FilePath, strip_headers: bool = True) -> tuple[str, list[tuple[int, int]]]:
    """
    Extract all text from a PDF and track page boundaries.

    Args:
        file_path: Path to the PDF file
        strip_headers: Whether to strip repeated headers/footers (default True)

    Returns:
        Tuple of (full_text, page_boundaries) where page_boundaries is a list of
        (page_number, char_offset) tuples indicating where each page starts.
    """
    pages = _extract_text_by_page(file_path)

    # Strip headers/footers if enabled
    if strip_headers:
        pages = _strip_headers_footers(pages)

    full_text = ""
    page_boundaries = []  # (page_number, char_offset)

    for page_num, page_text in pages:
        page_boundaries.append((page_num, len(full_text)))
        full_text += page_text + "\n"

    return full_text, page_boundaries


def _find_page_for_position(position: int, page_boundaries: list[tuple[int, int]]) -> int:
    """Find which page a character position falls on."""
    page_num = 1
    for boundary_page, boundary_offset in page_boundaries:
        if position >= boundary_offset:
            page_num = boundary_page
        else:
            break
    return page_num


def _find_chunk_pages(
    chunk_text: str,
    full_text: str,
    search_start: int,
    page_boundaries: list[tuple[int, int]]
) -> tuple[int, int, int]:
    """
    Find the page range for a chunk and its position in the full text.

    Returns:
        Tuple of (page_start, page_end, chunk_end_position)
    """
    # Find where this chunk appears in the full text
    chunk_start = full_text.find(chunk_text, search_start)
    if chunk_start == -1:
        # Fallback: try to find a prefix match (chunks may have been modified)
        chunk_start = search_start

    chunk_end = chunk_start + len(chunk_text)

    page_start = _find_page_for_position(chunk_start, page_boundaries)
    page_end = _find_page_for_position(chunk_end - 1, page_boundaries)

    return page_start, page_end, chunk_end


def _chunk_pdf_text(
    file_path: FilePath,
    similarity_threshold: float = 0.7,
    min_sentences_per_chunk: int = 4,
    max_sentences_per_chunk: int = 20,
) -> list[PDFChunk]:
    """
    Extract and semantically chunk text from a PDF.

    Uses semantic chunking to create coherent chunks, then maps each chunk
    back to its source page(s) in the PDF.
    """
    # Extract full text with page tracking
    full_text, page_boundaries = _extract_full_text(file_path)

    if not full_text.strip():
        return []

    # Use semantic chunking
    text_chunks = semantic_chunk_text(
        full_text,
        similarity_threshold=similarity_threshold,
        min_sentences_per_chunk=min_sentences_per_chunk,
        max_sentences_per_chunk=max_sentences_per_chunk,
        overlap_sentences=2
    )

    if not text_chunks:
        return []

    # Map chunks back to pages
    pdf_chunks = []
    search_position = 0

    for idx, chunk_text in enumerate(text_chunks):
        page_start, page_end, search_position = _find_chunk_pages(
            chunk_text, full_text, search_position, page_boundaries
        )

        pdf_chunks.append(PDFChunk(
            content=chunk_text,
            chunk_index=idx,
            page_start=page_start,
            page_end=page_end,
        ))

    return pdf_chunks


def _chunks_to_json(chunks: list[PDFChunk]) -> list[dict]:
    """
    Convert PDFChunks to the format expected by the database.

    Returns list of dicts with:
    - content: str (the text)
    - chunk_index: int
    - chunk_metadata: dict with page info
    """
    return [
        {
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "chunk_metadata": {
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
            },
        }
        for chunk in chunks
    ]


def get_pdf_metadata(file_path: FilePath) -> dict:
    """
    Extract metadata from a PDF file.

    Returns dict with:
    - total_pages: int
    - has_text: bool (whether any text was extracted)
    """
    doc = fitz.open(str(file_path))
    total_pages = len(doc)

    # Check if any page has text
    has_text = False
    for page_num in range(total_pages):
        if doc[page_num].get_text().strip():
            has_text = True
            break

    doc.close()

    return {
        "total_pages": total_pages,
        "has_text": has_text,
    }


def extract_pdf_text(file_path: FilePath) -> list[dict]:
    """
    Main entry point for PDF processing.

    Takes a PDF file path and returns chunks in database format.

    Args:
        file_path: Path to the PDF file

    Returns:
        List of dicts with content, chunk_index, and chunk_metadata (page info)
    """
    chunks = _chunk_pdf_text(file_path)
    return _chunks_to_json(chunks)


if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        print("Usage: python pdf.py <path_to_pdf>")
        sys.exit(1)

    test_file = FilePath(sys.argv[1])

    # Extract chunks and save as JSON to file
    result = extract_pdf_text(test_file)
    with open("pdf_chunks_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
