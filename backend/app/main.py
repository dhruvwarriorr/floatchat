from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.config import get_settings


def create_app() -> FastAPI:
    application = FastAPI(
        title="FloatChat-Lite API",
        version="0.1.0",
        description="Typed, evidence-first API for supported Indian Ocean ARGO questions.",
    )
    settings = get_settings()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(health_router)
    application.include_router(chat_router)

    static_dir = settings.static_dir
    if static_dir.is_dir():
        application.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return application


app = create_app()
