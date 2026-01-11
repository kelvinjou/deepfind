from app.model import StoreAssetRequest, DeleteFolderRequest
from lib.supabase.util import get_supabase_client
from lib.util.db_process import push_to_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

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

db_service = None


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome"}


@app.post("/dir/")
async def post_directory_path(payload: StoreAssetRequest) -> dict:
    """Process files from a directory and return processing results.

    Returns:
        dict: Contains status, processed count, failed files list, and folder path
    """
    result = push_to_db(payload.folderPath)

    return {
        "folderPath": payload.folderPath,
        "status": result["status"],
        "processedCount": result["processed_count"],
        "totalAttempted": result.get("total_attempted", 0),
        "failedFiles": result["failed_files"]
    }


@app.get("/query")
async def query_files(query_text: str, archived_folders: str = None) -> dict:
    """Query files using semantic search, excluding archived folders.

    Args:
        query_text: The search query text
        archived_folders: JSON-encoded array of folder paths to exclude from search

    Returns:
        Dictionary with query results and metadata
    """
    print(f"Query received: {query_text}")
    match_threshold = 0.3
    match_count = 10
    client = get_supabase_client()

    # Parse archived folders JSON array if provided
    # Expected format: '["path/to/folder1", "path/to/folder2"]'
    archived_folder_list = []
    if archived_folders:
        try:
            archived_folder_list = json.loads(archived_folders)
            print(
                f"Excluding {len(archived_folder_list)} archived folders from search")
        except json.JSONDecodeError:
            print("Failed to parse archived_folders JSON, ignoring filter")

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
