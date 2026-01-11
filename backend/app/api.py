from app.model import (
    StoreAssetRequest,
    DeleteFolderRequest,
)
from lib.supabase.util import get_supabase_client
from lib.util.db_process import push_to_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path
from collections import defaultdict
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
    archived_folders: Optional[str] = None,
) -> dict:
    """Query files using semantic search.

    Args:
        query_text: The search query text
        match_count: Maximum number of results to return
        archived_folders: JSON-encoded array of folder paths to exclude from search
        folders: JSON-encoded array of folder paths to filter results to

    Returns:
        Dictionary with query results and metadata
    """
    print(f"Query received: {query_text}")
    match_threshold = 0.3
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
