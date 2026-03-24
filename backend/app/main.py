from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api import search, upload, imagery, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Satellite Image Visual Search API",
    description="Visual Search, Retrieval & Detection in Satellite Imageries",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api/upload")
app.include_router(imagery.router, prefix="/api/imagery")
app.include_router(search.router, prefix="/api/search")


@app.get("/")
async def root():
    return {"message": "Satellite Image Visual Search API", "status": "running"}
