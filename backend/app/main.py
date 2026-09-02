import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.seed import seed_diseases_reference
from app.routers import dashboard, reports, scans
from app.services.inference_service import InferenceService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()

    logger.info("Seeding diseases_reference (idempotent)...")
    seed_diseases_reference()

    logger.info("Loading ML models (this happens once at startup, not per-request)...")
    app.state.inference_service = InferenceService(settings)
    app.state.model_loaded = True
    app.state.model_status = app.state.inference_service.classifier.model_status
    logger.info("Startup complete. model_status=%s", app.state.model_status)

    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AgriVision API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")

    app.include_router(scans.router)
    app.include_router(reports.router)
    app.include_router(dashboard.router)

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "model_loaded": getattr(app.state, "model_loaded", False),
            "model_status": getattr(app.state, "model_status", None),
        }

    return app


app = create_app()
