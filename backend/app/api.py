from app.model import (
    StoreAssetRequest,
    DeleteFolderRequest,
    AgentRequest,
    SummarizeFileRequest,
)
from lib.constants import DEFAULT_MATCH_THRESHOLD
from lib.supabase.util import get_supabase_client
from lib.util.db_process import push_to_db
from app.tooling.generation import generate_text_stream
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional, Generator
from pathlib import Path
from collections import defaultdict
import json
import re


app = FastAPI()
# do not change origins even if port # changes
# 5173 is the default port for Vite frontend dev server
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "localhost:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome"}


@app.post("/dir/")
async def post_directory_path(payload: StoreAssetRequest) -> dict:
    """Process files from one or more directories and return processing results.

    Returns:
        dict: Contains status, processed count, failed files list, and folder paths
    """
    folder_paths = payload.folderPath
    results = []

    for folder_path in folder_paths:
        result = push_to_db(folder_path)
        results.append({
            "folderPath": folder_path,
            "status": result["status"],
            "processedCount": result["processed_count"],
            "totalAttempted": result.get("total_attempted", 0),
            "failedFiles": result["failed_files"]
        })

    # Return results for all processed folders
    return {
        "folderPaths": folder_paths,
        "results": results,
        "totalFolders": len(folder_paths)
    }


@app.get("/query")
async def query_files(
    query_text: str,
    match_count: int = 10,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    archived_folders: Optional[str] = None,
) -> dict:
    """Query files using semantic search.

    Args:
        query_text: The search query text
        match_count: Maximum number of results to return
        threshold: Minimum similarity score (0-1), defaults to DEFAULT_MATCH_THRESHOLD
        archived_folders: JSON-encoded array of folder paths to exclude from search

    Returns:
        Dictionary with query results and metadata
    """
    print(f"Query received: {query_text}")
    match_threshold = threshold
    client = get_supabase_client()

    # Parse archived folders JSON array if provided
    archived_folder_list = []
    if archived_folders:
        try:
            archived_folder_list = json.loads(archived_folders)
            print(
                f"Excluding {len(archived_folder_list)} archived folders from search")
        except json.JSONDecodeError:
            print("Failed to parse archived_folders JSON, ignoring filter")

    # Standard semantic search
    results = client.query_files(
        query=query_text,
        match_threshold=match_threshold,
        match_count=match_count,
        archived_folders=archived_folder_list
    )

    print(f"Found {len(results)} results")
    return {
        "query": query_text,
        "threshold": match_threshold,
        "maxResults": match_count,
        "found": len(results),
        "results": results
    }


@app.delete("/folder/")
async def delete_folder(payload: DeleteFolderRequest) -> dict:
    """Permanently delete all files and chunks from a folder in the database.

    Args:
        payload: Request containing the folder path to delete

    Returns:
        dict: Contains status and count of deleted files
    """
    folder_path = payload.folderPath
    print(f"Deleting all files from folder: {folder_path}")

    client = get_supabase_client()
    deleted_count = client.delete_files_by_folder(folder_path)

    print(f"Deleted {deleted_count} files from {folder_path}")
    return {
        "status": "success",
        "folderPath": folder_path,
        "deletedCount": deleted_count
    }


@app.get("/folders/", tags=["folders"])
async def get_folders_with_files() -> dict:
    """Fetch all files grouped by their parent directory (root folder).

    Returns:
        dict: Contains a list of folder groups, each with folder name, path, and files
    """
    client = get_supabase_client()
    files = client.get_all_files()

    # Group files by their parent directory path
    folder_groups = defaultdict(lambda: {"files": []})

    for file in files:
        file_path = file.get("file_path")
        if not file_path:
            continue

        # Get parent directory path and folder name
        parent_path = str(Path(file_path).parent)
        folder_name = Path(parent_path).name or parent_path

        # Use parent path as key to avoid name collisions
        folder_groups[parent_path]["name"] = folder_name
        folder_groups[parent_path]["path"] = parent_path
        folder_groups[parent_path]["files"].append(file)

    # Convert to list and sort by folder name
    folders = sorted(
        [{"name": group["name"], "path": key, "fileCount": len(group["files"]), "files": group["files"]}
         for key, group in folder_groups.items()],
        key=lambda x: x["name"]
    )

    return {
        "totalFolders": len(folders),
        "totalFiles": len(files),
        "folders": folders
    }


def detect_summarize_intent(prompt: str) -> tuple[bool, str]:
    """Detect if the prompt is asking for a summary and extract the topic.

    Returns:
        tuple: (is_summarize_request, extracted_topic)
    """
    summarize_patterns = [
        r"summarize\s+(?:all\s+)?(?:documents?|files?|content)?\s*(?:on|about|related to|regarding)?\s*(.+)",
        r"give\s+(?:me\s+)?a?\s*summary\s+(?:of|on|about)\s+(.+)",
        r"what\s+(?:do|does)\s+(?:the\s+)?(?:documents?|files?)\s+say\s+about\s+(.+)",
        r"synthesize\s+(?:information|content|documents?)?\s*(?:on|about|related to)?\s*(.+)",
    ]

    prompt_lower = prompt.lower().strip()

    for pattern in summarize_patterns:
        match = re.search(pattern, prompt_lower, re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            return True, topic

    # Simple keyword check as fallback
    if any(keyword in prompt_lower for keyword in ["summarize", "summary", "synthesize"]):
        # Extract topic by removing the keyword
        topic = re.sub(r"(summarize|summary|synthesize)\s*(of|on|about|all|documents?|files?)?\s*", "", prompt_lower, flags=re.IGNORECASE).strip()
        return True, topic if topic else prompt

    return False, prompt


def create_sse_stream(generator: Generator[str, None, None]) -> Generator[str, None, None]:
    """Wrap a generator to produce SSE-formatted events."""
    for chunk in generator:
        yield f"data: {json.dumps({'content': chunk})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


@app.post("/agent/", tags=["agent"])
async def run_agent(payload: AgentRequest):
    """Run an agent task based on the prompt.

    Detects intent (summarize, search, etc.) and performs the appropriate action.
    Returns a streaming response for generation tasks.
    """
    prompt = payload.prompt
    match_count = payload.match_count

    print(f"Agent received prompt: {prompt}")

    # Detect intent
    is_summarize, topic = detect_summarize_intent(prompt)

    if is_summarize:
        print(f"Detected summarize intent for topic: {topic}")

        # Search for relevant documents
        client = get_supabase_client()
        results = client.query_files(
            query=topic,
            match_threshold=DEFAULT_MATCH_THRESHOLD,
            match_count=match_count,
            archived_folders=[]
        )

        if not results:
            def no_results_stream():
                yield f"data: {json.dumps({'content': f'No documents found related to: {topic}'})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"

            return StreamingResponse(
                no_results_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )

        # Build context from search results
        documents = []
        for result in results:
            file_name = result.get("file_name", "Unknown")
            content = result.get("content", "")
            if content:
                documents.append((file_name, content))

        print(f"Found {len(documents)} relevant document chunks")

        # Create synthesis prompt
        combined_text = "\n\n".join([f"Document: {name}\nContent: {content}" for name, content in documents])
        synthesis_prompt = (
            f"Based on the following document excerpts, provide a comprehensive summary about '{topic}'. "
            f"Cite the source documents when relevant.\n\n"
            f"{combined_text}\n\n"
            f"Summary:"
        )

        def stream_synthesis():
            # First send metadata about the search
            yield f"data: {json.dumps({'metadata': {'topic': topic, 'documentsFound': len(documents)}})}\n\n"

            # Stream the generated content
            for chunk in generate_text_stream(synthesis_prompt):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(
            stream_synthesis(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    # Default: just return a message that this isn't a recognized agent task
    return {
        "status": "not_agent_task",
        "message": "This prompt doesn't appear to be an agent task. Use the search endpoint for regular queries.",
        "prompt": prompt
    }


def get_file_type(file_name: str) -> str:
    """Determine file type from extension."""
    ext = file_name.lower().split('.')[-1] if '.' in file_name else ''

    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff', 'heic']:
        return 'image'
    elif ext == 'pdf':
        return 'pdf'
    elif ext in ['mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac', 'wma', 'aiff']:
        return 'audio'
    else:
        return 'text'


def extract_file_content(file_path: str, file_name: str) -> tuple[str, str]:
    """
    Extract content from a file based on its type.

    Returns:
        Tuple of (content, content_type_description)
    """
    file_type = get_file_type(file_name)

    if file_type == 'pdf':
        from lib.util.preprocessing.pdf import _extract_full_text
        full_text, _ = _extract_full_text(file_path)
        return full_text, "PDF document"

    elif file_type == 'image':
        from lib.util.preprocessing.image import generateImageCaption
        caption = generateImageCaption(file_path)
        return caption, "image (AI-generated caption)"

    elif file_type == 'audio':
        from lib.util.preprocessing.audio import _get_audio_transcript
        transcription = _get_audio_transcript(file_path)
        full_text = transcription.get('text', '')
        return full_text, "audio transcription"

    else:
        # Text file - read directly
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content, "text file"


@app.post("/summarize-file/", tags=["agent"])
async def summarize_file(payload: SummarizeFileRequest):
    """Summarize a single file's content with streaming response.

    Supports text files, PDFs, images (via caption), and audio (via transcription).

    Args:
        payload: Request containing file name and either content or file path

    Returns:
        StreamingResponse with SSE-formatted summary
    """
    file_name = payload.fileName
    file_path = payload.filePath
    content = payload.content
    content_type_desc = "text file"

    print(f"Summarizing file: {file_name}")

    # If we have a file path, extract content based on file type
    if file_path and not content:
        try:
            content, content_type_desc = extract_file_content(file_path, file_name)
        except Exception as e:
            print(f"Error extracting content from {file_path}: {e}")
            def error_stream():
                yield f"data: {json.dumps({'content': f'Error reading file: {str(e)}'})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            return StreamingResponse(
                error_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )

    if not content or not content.strip():
        def empty_content_stream():
            yield f"data: {json.dumps({'content': 'No content to summarize.'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(
            empty_content_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    # Create summarization prompt based on content type
    file_type = get_file_type(file_name)

    if file_type == 'image':
        summary_prompt = (
            f"Based on the following AI-generated caption of an image, provide a brief description "
            f"and any insights about what the image might contain.\n\n"
            f"Image file: {file_name}\n"
            f"Caption: {content}\n\n"
            f"Description:"
        )
    elif file_type == 'audio':
        summary_prompt = (
            f"Please provide a clear and concise summary of the following audio transcription.\n\n"
            f"Audio file: {file_name}\n\n"
            f"Transcription:\n{content}\n\n"
            f"Summary:"
        )
    elif file_type == 'pdf':
        summary_prompt = (
            f"Please provide a clear and concise summary of the following PDF document.\n\n"
            f"Document: {file_name}\n\n"
            f"Content:\n{content}\n\n"
            f"Summary:"
        )
    else:
        summary_prompt = (
            f"Please provide a clear and concise summary of the following file.\n\n"
            f"File: {file_name}\n\n"
            f"Content:\n{content}\n\n"
            f"Summary:"
        )

    def stream_summary():
        # Send metadata
        yield f"data: {json.dumps({'metadata': {'fileName': file_name, 'fileType': content_type_desc}})}\n\n"

        # Stream the generated summary
        for chunk in generate_text_stream(summary_prompt):
            yield f"data: {json.dumps({'content': chunk})}\n\n"

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        stream_summary(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
