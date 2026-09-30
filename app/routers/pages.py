import sqlite3
from itertools import groupby

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app import repository
from app.auth import User, require_reader
from app.db import get_db
from app.logging_config import get_logger
from app.templating import templates

router = APIRouter(tags=["pages"])
logger = get_logger(__name__)


@router.get("/", response_class=HTMLResponse)
def well_register(
    request: Request,
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    wells = sorted(repository.list_wells(conn), key=lambda w: (w["pad"], w["name"]))
    pads = [(pad, list(rows)) for pad, rows in groupby(wells, key=lambda w: w["pad"])]
    logger.info("pages.well_register", extra={"user": user.email, "count": len(wells)})
    return templates.TemplateResponse(
        request, "wells.html", {"user": user, "pads": pads, "well_count": len(wells)}
    )


@router.get("/wells/{well_id}", response_class=HTMLResponse)
def well_detail(
    request: Request,
    well_id: int,
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    well = repository.get_well(conn, well_id)
    if well is None:
        raise HTTPException(status_code=404, detail="Well not found")
    log = repository.list_shift_log(conn, well_id=well_id)
    logger.info("pages.well_detail", extra={"user": user.email, "well_id": well_id})
    return templates.TemplateResponse(
        request, "well_detail.html", {"user": user, "well": well, "log": log}
    )


@router.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok"}
