from backend.app.model import StoreAssetRequest
from backend.util.db_process import push_to_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# do not change origins even if port # changes
# 5173 is the default port for Vite frontend dev server
origins = [
    "http://localhost:5173",
    "localhost:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
