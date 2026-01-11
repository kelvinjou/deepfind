"""
Database seeding script for testing.

This script processes files from the test_files directory and inserts them
into the database with embeddings for testing the query_file_chunks function.

Usage:
    python -m scripts.seed_database [--clear] [--folder PATH]

Options:
    --clear     Clear all existing data before seeding
    --folder    Path to folder to process (default: test_files/test_suite(all_types))
"""

import sys
import argparse
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.semantic_chunking import semantic_chunk_text
from util.embedding import get_embeddings
from util.folder_extraction import get_valid_file_from_folder, getFileProperties, read_text_file_content
from util.pdf import extract_pdf_text
from util.audio import transcribe_audio
from lib.supabase.util import get_supabase_client


# Supported MIME types and their processors
SUPPORTED_MIME_TYPES = {
    # Text
    'text/plain',
    # PDF
    'application/pdf',
    # Audio
    'audio/mpeg',      # .mp3
    'audio/wav',       # .wav
    'audio/x-wav',     # .wav (alternate)
    'audio/ogg',       # .ogg
    'audio/flac',      # .flac
    'audio/mp4',       # .m4a
    'audio/x-m4a',     # .m4a (alternate)
}


def process_text_file(file_path: str) -> list[dict]:
    """Process a plain text file into chunks."""
    content = read_text_file_content(file_path)
    chunks = semantic_chunk_text(content, overlap_sentences=2)

    return [
        {
            "chunk_index": i,
            "content": chunk,
            "chunk_metadata": {
                "char_start": 0,  # Could calculate actual positions if needed
                "char_end": len(chunk),
            }
        }
        for i, chunk in enumerate(chunks)
    ]


def process_pdf_file(file_path: str) -> list[dict]:
    """Process a PDF file into chunks with page metadata."""
    return extract_pdf_text(file_path)


def process_audio_file(file_path: str) -> list[dict]:
    """Process an audio file into transcript chunks with timestamp metadata."""
    return transcribe_audio(file_path)


# Audio MIME types
AUDIO_MIME_TYPES = {
    'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/ogg',
    'audio/flac', 'audio/mp4', 'audio/x-m4a'
}


def process_file(file_path: str, mime_type: str) -> list[dict]:
    """
    Process a file based on its MIME type.

    Returns list of chunk dicts with content, chunk_index, chunk_metadata.
    """
    if mime_type == 'text/plain':
        return process_text_file(file_path)
    elif mime_type == 'application/pdf':
        return process_pdf_file(file_path)
    elif mime_type in AUDIO_MIME_TYPES:
        return process_audio_file(file_path)
    else:
        print(f"  Unsupported MIME type: {mime_type}")
        return []


def seed_database(folder_path: str, clear_existing: bool = False):
    """
    Seed the database with files from the specified folder.

    Args:
        folder_path: Path to folder containing test files
        clear_existing: If True, delete all existing data first
    """
    client = get_supabase_client()

    # Optionally clear existing data
    if clear_existing:
        print("Clearing existing data...")
        deleted = client.delete_all_files()
        print(f"  Deleted {deleted} files\n")

    # Get valid files from folder
    file_paths = get_valid_file_from_folder(folder_path, SUPPORTED_MIME_TYPES)

    print(f"\nFound {len(file_paths)} files to process\n")

    if not file_paths:
        print("No files found. Check the folder path and MIME types.")
        return

    success_count = 0
    skip_count = 0
    fail_count = 0

    for file_path in sorted(file_paths):
        file_name = Path(file_path).name
        print(f"Processing: {file_name}")

        try:
            # Get file properties
            file_props = getFileProperties(file_path)

            # Check if file already exists
            if client.file_exists(file_hash=file_props.file_hash):
                print(f"  Skipped (already exists)\n")
                skip_count += 1
                continue

            # Process file into chunks
            chunks = process_file(file_path, file_props.mime_type)

            if not chunks:
                print(f"  Skipped (no content extracted)\n")
                skip_count += 1
                continue

            print(f"  Extracted {len(chunks)} chunks")

            # Generate embeddings for all chunks
            chunk_contents = [c["content"] for c in chunks]
            embeddings = get_embeddings(chunk_contents)
            print(f"  Generated {len(embeddings)} embeddings")

            # Prepare metadata
            metadata = {
                "source": "seed_script",
                "chunk_count": len(chunks),
            }

            # Insert into database
            file_id = client.process_file(
                file_path=file_props.path,
                file_name=file_props.file_name,
                mime_type=file_props.mime_type,
                file_hash=file_props.file_hash,
                last_modified_at=file_props.last_modified,
                chunks=chunks,
                embeddings=embeddings,
                file_size=file_props.file_size,
                metadata=metadata,
            )

            print(f"  Inserted with ID: {file_id}\n")
            success_count += 1

        except Exception as e:
            print(f"  ERROR: {e}\n")
            fail_count += 1

    # Summary
    print("=" * 50)
    print("Seeding complete!")
    print(f"  Successful: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Failed: {fail_count}")


def main():
    parser = argparse.ArgumentParser(description="Seed the database with test files")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all existing data before seeding"
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="test_files/test_suite(all_types)",
        help="Path to folder to process"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Database Seeding Script")
    print("=" * 50)
    print(f"Folder: {args.folder}")
    print(f"Clear existing: {args.clear}")
    print("=" * 50 + "\n")

    seed_database(args.folder, args.clear)


if __name__ == "__main__":
    main()
