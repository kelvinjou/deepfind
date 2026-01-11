from app.model import (
    StoreAssetRequest,
    MoveFilesRequest,
    ConvertFilesRequest,
    RenameFilesRequest,
    TagFilesRequest,
    GetFilesWithTagRequest,
    SearchByPatternRequest,
    SearchByTagsRequest,
    FilterByDateRequest,
    FilterBySizeRequest,
    FilterByTypeRequest,
    CopyFilesRequest,
    CopyDirectoryRequest,
    RecentFilesRequest,
)
from app.tooling import don_tools
from lib.scripts.test_query import query_chunks
from lib.util.db_process import push_to_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from typing import List, Optional
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

def _parse_folders_param(folders: Optional[str]) -> List[str]:
    if not folders:
        return []
    try:
        parsed = json.loads(folders)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(path) for path in parsed if path]


def _filter_results_by_folders(results: List[dict], folders: List[str]) -> List[dict]:
    if not folders:
        return results
    normalized_folders = [os.path.normpath(os.path.abspath(path)) for path in folders]

    def in_folder(file_path: str) -> bool:
        normalized_path = os.path.normpath(os.path.abspath(file_path))
        return any(
            normalized_path == folder
            or normalized_path.startswith(folder + os.sep)
            for folder in normalized_folders
        )

    return [row for row in results if row.get("file_path") and in_folder(row["file_path"])]


def _file_paths_to_results(file_paths: List[str]) -> List[dict]:
    return [
        {"file_path": path, "file_name": os.path.basename(path)}
        for path in file_paths
    ]


def _extract_recent_count(query_text: str, default: int = 10) -> int:
    match = re.search(r"\b(\d+)\b", query_text)
    if not match:
        return default
    try:
        return max(1, int(match.group(1)))
    except ValueError:
        return default


def _looks_like_recent_query(query_text: str) -> bool:
    lowered = query_text.lower()
    return any(word in lowered for word in ["most recent", "recent", "latest", "newest"])


def _extract_tag_intent(query_text: str) -> Optional[dict]:
    lowered = query_text.lower()
    if "tag" not in lowered:
        return None

    color_map = {
        "gray": 1,
        "grey": 1,
        "green": 2,
        "purple": 3,
        "blue": 4,
        "yellow": 5,
        "red": 6,
        "orange": 7,
    }

    match = re.search(
        r"(add|apply|set)\s+(?P<color>\w+)?\s*tag[s]?\s+to\s+(?P<target>.+)",
        lowered,
    )
    if match:
        color_name = (match.group("color") or "").strip()
        target_start = match.start("target")
        target = query_text[target_start:].strip()
        tag = color_name or "tagged"
        color = color_map.get(color_name, 0)
        return {"tag": tag, "color": color, "target": target}

    match = re.search(
        r"tag\s+(?P<target>.+?)\s+as\s+(?P<tag>\w+)",
        lowered,
    )
    if match:
        target_start = match.start("target")
        target_end = match.end("target")
        target = query_text[target_start:target_end].strip()
        tag = match.group("tag").strip()
        color = color_map.get(tag, 0)
        return {"tag": tag, "color": color, "target": target}

    return None


def _get_recent_files(folders: List[str], count: int) -> List[str]:
    if not folders:
        return []
    all_files = []
    for folder in folders:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(file_path)
                    all_files.append((file_path, mtime))
                except OSError:
                    continue
    all_files.sort(key=lambda item: item[1], reverse=True)
    return [item[0] for item in all_files[:count]]


@app.get("/query")
async def query_files(query_text: str, folders: Optional[str] = None) -> dict:
    print(f"Query received: {query_text}")
    match_threshold = 0.3
    match_count = 10
    folder_list = _parse_folders_param(folders)

    if _looks_like_recent_query(query_text):
        count = _extract_recent_count(query_text, default=match_count)
        recent_files = _get_recent_files(folder_list, count)
        results = _file_paths_to_results(recent_files)
        print(f"Found {len(results)} recent files")
        return {
            "query": query_text,
            "threshold": match_threshold,
            "maxResults": count,
            "found": len(results),
            "results": results,
            "action": "recent_files",
        }

    tag_intent = _extract_tag_intent(query_text)
    if tag_intent:
        search_results = query_chunks(
            tag_intent["target"],
            match_threshold=match_threshold,
            match_count=match_count,
        )
        search_results = _filter_results_by_folders(search_results, folder_list)
        seen = set()
        file_paths = []
        for row in search_results:
            path = row.get("file_path")
            if path and path not in seen:
                seen.add(path)
                file_paths.append(path)
        if file_paths:
            don_tools.tag_files(file_paths, tag_intent["tag"], tag_intent["color"])
        results = _file_paths_to_results(file_paths)
        print(f"Tagged {len(results)} files")
        return {
            "query": query_text,
            "threshold": match_threshold,
            "maxResults": match_count,
            "found": len(results),
            "results": results,
            "action": "tag_files",
            "tag": tag_intent["tag"],
            "color": tag_intent["color"],
        }

    results = query_chunks(
        query_text,
        match_threshold=match_threshold,
        match_count=match_count,
    )
    results = _filter_results_by_folders(results, folder_list)
    print(f"Found {len(results)} results")
    return {
        "query": query_text,
        "threshold": match_threshold,
        "maxResults": match_count,
        "found": len(results),
        "results": results,
        "action": "search_files",
    }


# File Management Endpoints

@app.post("/files/move", tags=["file-operations"])
async def move_files(payload: MoveFilesRequest) -> dict:
    """Move files to a specified directory.
    
    Args:
        payload: Contains filePaths (list of file paths) and targetDirectory
    """
    don_tools.move_files_to_directory(payload.filePaths, payload.targetDirectory)
    return {"status": "success", "message": f"Moved {len(payload.filePaths)} files to {payload.targetDirectory}"}


@app.post("/files/convert", tags=["file-operations"])
async def convert_files(payload: ConvertFilesRequest) -> dict:
    """Convert files to a different extension.
    
    Args:
        payload: Contains filePaths and targetExtension
    """
    don_tools.convert_file_types(payload.filePaths, payload.targetExtension)
    return {"status": "success", "message": f"Converted {len(payload.filePaths)} files to {payload.targetExtension}"}


@app.post("/files/rename", tags=["file-operations"])
async def rename_files(payload: RenameFilesRequest) -> dict:
    """Rename files with new names.
    
    Args:
        payload: Contains filePaths and newNames (must be same length)
    """
    if len(payload.filePaths) != len(payload.newNames):
        return {"status": "error", "message": "Number of files and new names must match"}
    don_tools.rename_files(payload.filePaths, payload.newNames)
    return {"status": "success", "message": f"Renamed {len(payload.filePaths)} files"}


@app.post("/files/tag", tags=["file-operations"])
async def tag_files(payload: TagFilesRequest) -> dict:
    """Tag files with macOS Finder tags.
    
    Args:
        payload: Contains filePaths, tag name, and optional color (0-7)
    """
    don_tools.tag_files(payload.filePaths, payload.tag, payload.color)
    return {"status": "success", "message": f"Tagged {len(payload.filePaths)} files with '{payload.tag}'"}


@app.post("/files/get-by-tag", tags=["file-operations"])
async def get_files_with_tag(payload: GetFilesWithTagRequest) -> dict:
    """Get all files in a directory that have a specific tag.
    
    Args:
        payload: Contains directory path and tag to search for
    """
    files = don_tools.get_files_with_tag(payload.directory, payload.tag)
    return {"status": "success", "files": files, "count": len(files)}


@app.post("/files/search-pattern", tags=["file-operations"])
async def search_by_pattern(payload: SearchByPatternRequest) -> dict:
    """Search for files matching a name pattern.
    
    Args:
        payload: Contains directory and pattern to match in filenames
    """
    files = don_tools.search_files_by_pattern(payload.directory, payload.pattern)
    return {"status": "success", "files": files, "count": len(files)}


@app.post("/files/search-tags", tags=["file-operations"])
async def search_by_tags(payload: SearchByTagsRequest) -> dict:
    """Search for files by metadata tags.
    
    Args:
        payload: Contains directory, tagKey and tagValue to search for
    """
    files = don_tools.search_files_by_tags(payload.directory, payload.tagKey, payload.tagValue)
    return {"status": "success", "files": files, "count": len(files)}


@app.post("/files/filter-by-date", tags=["file-operations"])
async def filter_by_date(payload: FilterByDateRequest) -> dict:
    """Filter files by modification date range.
    
    Args:
        payload: Contains directory, startDate and endDate (Unix timestamps)
    """
    files = don_tools.filter_files_by_date(payload.directory, payload.startDate, payload.endDate)
    return {"status": "success", "files": files, "count": len(files)}


@app.post("/files/filter-by-size", tags=["file-operations"])
async def filter_by_size(payload: FilterBySizeRequest) -> dict:
    """Filter files by size range.
    
    Args:
        payload: Contains directory, minSize and maxSize (in bytes)
    """
    files = don_tools.filter_files_by_size(payload.directory, payload.minSize, payload.maxSize)
    return {"status": "success", "files": files, "count": len(files)}


@app.post("/files/filter-by-type", tags=["file-operations"])
async def filter_by_type(payload: FilterByTypeRequest) -> dict:
    """Filter files by file extension.
    
    Args:
        payload: Contains directory and fileExtension (e.g., '.txt', '.pdf')
    """
    files = don_tools.filter_files_by_type(payload.directory, payload.fileExtension)
    return {"status": "success", "files": files, "count": len(files)}


@app.post("/files/copy", tags=["file-operations"])
async def copy_files(payload: CopyFilesRequest) -> dict:
    """Copy files to a target directory.
    
    Args:
        payload: Contains filePaths and targetDirectory
    """
    don_tools.make_copy_of_files(payload.filePaths, payload.targetDirectory)
    return {"status": "success", "message": f"Copied {len(payload.filePaths)} files to {payload.targetDirectory}"}


@app.post("/files/copy-directory", tags=["file-operations"])
async def copy_directory(payload: CopyDirectoryRequest) -> dict:
    """Copy an entire directory to a new location.
    
    Args:
        payload: Contains sourceDirectory and targetDirectory
    """
    don_tools.make_copy_of_directory(payload.sourceDirectory, payload.targetDirectory)
    return {"status": "success", "message": f"Copied directory {payload.sourceDirectory} to {payload.targetDirectory}"}


@app.post("/files/recent", tags=["file-operations"])
async def get_recent_files(payload: RecentFilesRequest) -> dict:
    """Get the most recently modified files in a directory.
    
    Args:
        payload: Contains directory and count (number of files to return)
    """
    files = don_tools.get_most_recently_modified_files(payload.directory, payload.count)
    return {"status": "success", "files": files, "count": len(files)}


# Create and mount the MCP server directly to your FastAPI app
mcp = FastApiMCP(
    app,
    name="MCP Server",
    description="Exposes API endpoints as MCP tools",
)
mcp.mount()
