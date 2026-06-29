"""Agri-DSS FastAPI uygulaması."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import health, regions

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="Batı Antalya Tarımsal Karar Destek Sistemi — Backend API (Faz 0).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(regions.router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "name": settings.project_name,
        "docs": "/docs",
        "contract": f"{settings.api_v1_prefix}/data",
        "health": "/health",
    }
