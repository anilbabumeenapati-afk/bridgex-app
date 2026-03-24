from fastapi import FastAPI
from app.api.router import api_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from app.db.models import Base
import app.db.models
from app.db.session import engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import os

app = FastAPI()

@app.get("/")
def root():
    print("🔥 ROOT HIT")
    return {"status": "OK"}

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = f"output/{filename}"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/files", StaticFiles(directory="output"), name="files")

# ✅ CREATE TABLES
@app.on_event("startup")
def init_db():
    try:
        print("🔧 Initializing DB...")
        Base.metadata.create_all(bind=engine)
        print("✅ DB Ready")
    except Exception as e:
        print("❌ DB ERROR:", str(e))

app.include_router(api_router, prefix="/api/v1")

if os.path.exists("output"):
    app.mount("/files", StaticFiles(directory="output"), name="files")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("🔥🔥🔥 GLOBAL ERROR:", str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )
