import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app import repository
from app.auth import User, require_reader
from app.db import get_db
from app.logging_config import get_logger
from app.models import Well, WellStatus

router = APIRouter(prefix="/api/wells", tags=["wells"])
logger = get_logger(__name__)


@router.get("", response_model=list[Well])
def list_wells(
    status: WellStatus | None = None,
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    wells = repository.list_wells(conn, status)
    logger.info("wells.list", extra={"user": user.email, "status": status, "count": len(wells)})
    return wells


@router.get("/{well_id}", response_model=Well)
def get_well(
    well_id: int,
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    well = repository.get_well(conn, well_id)
    if well is None:
        raise HTTPException(status_code=404, detail="Well not found")
    logger.info("wells.get", extra={"user": user.email, "well_id": well_id})
    return well
