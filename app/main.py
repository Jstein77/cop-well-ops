from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import connect
from app.logging_config import configure_logging, get_logger, request_logging_middleware
from app.routers import dashboard, pages, wells
from app.seed import seed_if_empty

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    conn = connect(settings.db_path)
    try:
        seed_if_empty(conn)
    finally:
        conn.close()
    logger.info("app.started", extra={"env": settings.env})
    yield


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    app = FastAPI(title="Well Ops", lifespan=lifespan)
    app.middleware("http")(request_logging_middleware)
    app.mount("/static", StaticFiles(directory=Path(__file__).with_name("static")), name="static")
    app.include_router(pages.router)
    app.include_router(wells.router)
    app.include_router(dashboard.router)
    return app


app = create_app()
