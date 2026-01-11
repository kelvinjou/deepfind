from lib.constants import SUPPORTED_MIME_TYPES
from lib.util.preprocessing.image import generateImageCaption
from lib.util.preprocessing.pdf import extract_pdf_text
from lib.util.preprocessing.audio import transcribe_audio
from lib.supabase.util import get_supabase_client
from lib.util.folder_extraction import get_valid_file_from_folder, getFileProperties, read_text_file_content
from lib.util.embedding import get_embeddings
from lib.util.preprocessing.semantic_chunking import semantic_chunk_text
import sys
from pathlib import Path
from pydantic import FilePath

# Audio MIME types
AUDIO_MIME_TYPES = {
    'audio/mpeg',
    'audio/wav',
    'audio/x-wav',
    'audio/ogg',
    'audio/flac',
    'audio/mp4',
    'audio/x-m4a',
}

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def process_image_file(file_path: str, file_props, client):
    """Process an image file: generate caption, generate embedding, and insert to DB."""
    caption = generateImageCaption(file_path)
    embedding = get_embeddings([caption])

    # Since image captions are very small, we use a single chunk
    chunks_data = [
        {
            "chunk_index": 0,
            "content": caption,
            "chunk_metadata": {
                # "char_start": 0,
                # "char_end": len(caption)
            }
        }
    ]

    metadata = {
        "char_count": len(caption),
        "format": "image"
    }

    file_id = client.process_file(
        file_path=file_props.path,
        file_name=file_props.file_name,
        mime_type=file_props.mime_type,
        file_hash=file_props.file_hash,
        last_modified_at=file_props.last_modified,
        chunks=chunks_data,
        embeddings=embedding,
        file_size=file_props.file_size,
        metadata=metadata
    )
    return file_id


def process_audio_file(file_path: str, file_props, client):
    """Process an audio file: transcribe, chunk, generate embeddings, and insert to DB."""
    chunks_data = transcribe_audio(file_path)

    # Extract content for embedding generation
    contents = [chunk["content"] for chunk in chunks_data]
    embeddings = get_embeddings(contents)

    # Add embeddings to chunks
    for i, chunk in enumerate(chunks_data):
        # Embeddings are already in the right shape
        pass

    metadata = {
        "format": "audio",
        "chunk_count": len(chunks_data)
    }

    file_id = client.process_file(
        file_path=file_props.path,
        file_name=file_props.file_name,
        mime_type=file_props.mime_type,
        file_hash=file_props.file_hash,
        last_modified_at=file_props.last_modified,
        chunks=chunks_data,
        embeddings=embeddings,
        file_size=file_props.file_size,
        metadata=metadata
    )
    return file_id


def process_text_file(file_path: str, file_props, client):
    """Process a text file: read, chunk semantically, generate embeddings, and insert to DB."""
    contents = read_text_file_content(file_path)
    chunks = semantic_chunk_text(contents)
    embeddings = get_embeddings(chunks)

    chunks_data = [
        {
            "chunk_index": i,
            "content": chunk.get("text") if isinstance(chunk, dict) else chunk,
            "chunk_metadata": {
                "char_start": chunk.get("start", 0) if isinstance(chunk, dict) else 0,
                "char_end": chunk.get("end", len(chunk.get("text", chunk))) if isinstance(chunk, dict) else len(chunk)
            }
        }
        for i, chunk in enumerate(chunks)
    ]

    metadata = {
        "char_count": len(contents),
        "format": "plain"
    }

    file_id = client.process_file(
        file_path=file_props.path,
        file_name=file_props.file_name,
        mime_type=file_props.mime_type,
        file_hash=file_props.file_hash,
        last_modified_at=file_props.last_modified,
        chunks=chunks_data,
        embeddings=embeddings,
        file_size=file_props.file_size,
        metadata=metadata
    )
    return file_id


def process_pdf_file(file_path: str, file_props, client):
    """Process a PDF file: extract text with page metadata, generate embeddings, and insert to DB."""
    chunks = extract_pdf_text(Path(file_path))
    # Already has chunk_index and chunk_metadata (page info)
    chunks_data = chunks

    # Extract content strings for embeddings
    chunk_texts = [chunk["content"] for chunk in chunks]
    embeddings = get_embeddings(chunk_texts)
    contents = " ".join(chunk_texts)

    metadata = {
        "char_count": len(contents),
        "total_pages": max(chunk["chunk_metadata"].get("page_end", 1) for chunk in chunks) if chunks else 0,
        "format": "pdf"
    }

    file_id = client.process_file(
        file_path=file_props.path,
        file_name=file_props.file_name,
        mime_type=file_props.mime_type,
        file_hash=file_props.file_hash,
        last_modified_at=file_props.last_modified,
        chunks=chunks_data,
        embeddings=embeddings,
        file_size=file_props.file_size,
        metadata=metadata
    )
    return file_id

#
# insertions into db


def push_to_db(folder_path: str) -> dict:
    """Process files from folder and return summary with failed files.

    Returns:
        dict: Contains processed count, failed files list with error messages, and status
    """
    client = get_supabase_client()
    failed_files = []
    processed_count = 0

    filtered_files = get_valid_file_from_folder(
        # THIS IS CURRENTLY HARD-CODED, CHANGE THIS LATER
        folder_path,
        SUPPORTED_MIME_TYPES
    )

    print(f"\n📁 Found {len(filtered_files)} files to process")

    if not filtered_files:
        print("⚠️  No files found")
        return {
            "status": "success",
            "processed_count": 0,
            "failed_files": [],
            "message": "No files found to process"
        }

    for file_path in filtered_files:
        try:
            # Get file properties
            file_props = getFileProperties(file_path)

            # Check if file already exists (by hash)
            if client.file_exists(file_hash=file_props.file_hash):
                print(f"Skipping {file_path} - already exists in database")
                continue

            # Process based on file type
            if file_props.mime_type == 'application/pdf':
                file_id = process_pdf_file(file_path, file_props, client)
            elif file_props.mime_type in ('image/jpeg', 'image/png'):
                file_id = process_image_file(file_path, file_props, client)
            elif file_props.mime_type in AUDIO_MIME_TYPES:
                file_id = process_audio_file(file_path, file_props, client)
            else:
                file_id = process_text_file(file_path, file_props, client)

            print(f"✓ Successfully processed {file_path} (ID: {file_id})")
            processed_count += 1
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Failed to process {file_path}: {error_msg}")
            failed_files.append({
                "file_path": file_path,
                "error": error_msg
            })

    return {
        "status": "success" if not failed_files else "partial",
        "processed_count": processed_count,
        "failed_files": failed_files,
        "total_attempted": len(filtered_files)
    }


if __name__ == "__main__":
    push_to_db("test_files/image/")
