from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
import os

from app.api.router import api_router
from app.db.models import Base
import app.db.models
from app.db.session import engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://bridgex-app-git-main-anilbabuaflcrs-projects.vercel.app",
        "https://regadapat.vercel.app"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "OK"}

@app.get("/api/v1/download/{filename}")
def download_file(filename: str):
    file_path = f"output/{filename}"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

if os.path.exists("output"):
    app.mount("/files", StaticFiles(directory="output"), name="files")

@app.on_event("startup")
def init_db():
    try:
        print("🔧 Initializing DB...")
        Base.metadata.create_all(bind=engine)
        print("✅ DB Ready")
    except Exception as e:
        print("❌ DB ERROR:", str(e))

app.include_router(api_router, prefix="/api/v1")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("🔥🔥🔥 GLOBAL ERROR:", str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )