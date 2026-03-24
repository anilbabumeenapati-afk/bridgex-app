from fastapi import FastAPI
from app.api.router import api_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from app.db.models import Base
import app.db.models
from app.db.session import engine
from fastapi.staticfiles import StaticFiles

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
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/files", StaticFiles(directory="output"), name="files")

# ✅ CREATE TABLES
#Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")
app.mount("/files", StaticFiles(directory="output"), name="files")
