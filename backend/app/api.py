from app.model import (
    StoreAssetRequest,
    DeleteFolderRequest,
    ExecuteActionRequest,
)
from app.tooling import don_tools
from lib.constants import DEFAULT_MATCH_THRESHOLD
from lib.supabase.util import get_supabase_client
from lib.util.db_process import push_to_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path
from collections import defaultdict
import json
import os
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

    move_intent = _extract_transfer_intent(query_text, "move")
    copy_intent = _extract_transfer_intent(query_text, "copy")
    transfer_intent = move_intent or copy_intent
    if transfer_intent:
        file_paths, unresolved = _resolve_file_paths(
            transfer_intent["file_paths"], client
        )
        files = [
            {"file_name": os.path.basename(path), "file_path": path}
            for path in file_paths
        ]
        confirm_required = len(file_paths) > 0
        pending_actions = None
        if confirm_required:
            pending_actions = {
                "move_files": {
                    "action": "move_files",
                    "params": {
                        "file_paths": file_paths,
                        "target_directory": transfer_intent["target_directory"],
                    },
                },
                "copy_files": {
                    "action": "copy_files",
                    "params": {
                        "file_paths": file_paths,
                        "target_directory": transfer_intent["target_directory"],
                    },
                },
            }
        return {
            "query": query_text,
            "threshold": match_threshold,
            "maxResults": match_count,
            "found": len(files),
            "results": files,
            "action": "move_files" if move_intent else "copy_files",
            "confirm_required": confirm_required,
            "pending_actions": pending_actions,
            "unresolved_files": unresolved,
        }

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
        "results": results,
        "action": "search_files",
        "confirm_required": False,
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


@app.post("/actions/execute")
async def execute_action(payload: ExecuteActionRequest) -> dict:
    action = payload.action
    params = payload.params or {}

    if action == "move_files":
        file_paths = params.get("file_paths", [])
        target_directory = params.get("target_directory")
        if not file_paths or not target_directory:
            return {
                "status": "error",
                "message": "file_paths and target_directory are required",
                "action": action,
            }
        don_tools.move_files_to_directory(file_paths, target_directory)
        return {
            "status": "success",
            "action": action,
            "movedCount": len(file_paths),
            "targetDirectory": target_directory,
        }

    if action == "copy_files":
        file_paths = params.get("file_paths", [])
        target_directory = params.get("target_directory")
        if not file_paths or not target_directory:
            return {
                "status": "error",
                "message": "file_paths and target_directory are required",
                "action": action,
            }
        don_tools.make_copy_of_files(file_paths, target_directory)
        return {
            "status": "success",
            "action": action,
            "copiedCount": len(file_paths),
            "targetDirectory": target_directory,
        }

    return {"status": "error", "message": "Unknown action", "action": action}


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


def _extract_transfer_intent(query_text: str, action_word: str) -> dict | None:
    lowered = query_text.lower()
    if action_word not in lowered:
        return None

    marker = " to "
    if marker not in lowered:
        return None

    before, after = query_text.rsplit(marker, 1)
    before = before.strip()
    after = after.strip().strip('"').strip("'")
    if not re.match(rf"^{action_word}\b", before, flags=re.IGNORECASE):
        return None

    before = re.sub(
        rf"^{action_word}[\s,]+(files?\s+)?",
        "",
        before,
        flags=re.IGNORECASE,
    )
    raw_paths = [part.strip().strip('"').strip("'") for part in before.split(",")]
    file_paths = [path for path in raw_paths if path]
    if not file_paths or not after:
        return None

    return {
        "file_paths": file_paths,
        "target_directory": after,
    }


def _resolve_file_paths(raw_paths: list[str], client) -> tuple[list[str], list[str]]:
    resolved = []
    unresolved = []
    filenames = []

    for path in raw_paths:
        if os.path.isabs(path):
            resolved.append(path)
        else:
            filenames.append(os.path.basename(path))

    name_to_paths = defaultdict(list)
    if filenames:
        files = client.get_all_files()
        for item in files:
            name = item.get("file_name")
            path = item.get("file_path")
            if name and path:
                name_to_paths[name].append(path)

        for name in filenames:
            matches = name_to_paths.get(name, [])
            if matches:
                resolved.extend(matches)
            else:
                unresolved.append(name)

    seen = set()
    unique_resolved = []
    for path in resolved:
        if path not in seen:
            seen.add(path)
            unique_resolved.append(path)

    return unique_resolved, unresolved
