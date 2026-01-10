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
