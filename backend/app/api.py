from app.model import StoreAssetRequest
from lib.supabase.util import get_supabase_client
from lib.scripts.test_query import query_chunks
from lib.util.db_process import push_to_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
async def query_files(query_text: str) -> dict:
    print(f"Query received: {query_text}")
    match_threshold = 0.3
    match_count = 10
    client = get_supabase_client()
    results = client.query_files(
        query=query_text,
        match_threshold=match_threshold,
        match_count=match_count
    )

    print(f"Found {len(results)} results")
    return {
        "query": query_text,
        "threshold": match_threshold,
        "maxResults": match_count,
        "found": len(results),
        "results": results
    }
