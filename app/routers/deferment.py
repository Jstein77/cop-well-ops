import sqlite3
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from app import repository
from app.auth import User, require_reader
from app.db import get_db
from app.logging_config import get_logger
from app.models import DefermentReport
from app.templating import templates

router = APIRouter(tags=["deferment"])
logger = get_logger(__name__)


def build_report(
    conn: sqlite3.Connection, user: User, as_of: date | None, within_days: int
) -> dict[str, Any]:
    as_of = as_of or date.today()
    deferments = repository.list_deferments(conn)
    integrity = repository.list_integrity_due(conn, as_of, as_of + timedelta(days=within_days))
    logger.info(
        "deferment.report",
        extra={
            "user": user.email,
            "as_of": as_of.isoformat(),
            "within_days": within_days,
            "deferment_count": len(deferments),
            "integrity_count": len(integrity),
        },
    )
    return {
        "as_of": as_of,
        "within_days": within_days,
        "total_lost_bopd": sum(d["lost_bopd"] for d in deferments),
        "unplanned_lost_bopd": sum(d["lost_bopd"] for d in deferments if not d["planned"]),
        "deferments": deferments,
        "integrity": integrity,
    }


@router.get("/api/deferment-report", response_model=DefermentReport)
def deferment_report(
    as_of: date | None = None,
    within_days: int = Query(7, ge=0, le=90),
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    return build_report(conn, user, as_of, within_days)


@router.get("/deferments", response_class=HTMLResponse)
def deferment_page(
    request: Request,
    as_of: date | None = None,
    within_days: int = Query(7, ge=0, le=90),
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    report = build_report(conn, user, as_of, within_days)
    return templates.TemplateResponse(request, "deferment.html", {"user": user, **report})
