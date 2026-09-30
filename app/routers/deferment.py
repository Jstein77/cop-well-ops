import sqlite3
from datetime import date, timedelta

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

DueWithinDays = Query(7, ge=0, le=90)


def build_report(conn: sqlite3.Connection, due_within_days: int) -> dict:
    as_of = date.today()
    deferments = repository.list_deferments(conn)
    integrity = repository.list_integrity_due(conn, as_of, as_of + timedelta(days=due_within_days))
    return {
        "as_of": as_of,
        "due_within_days": due_within_days,
        "total_lost_bopd": sum(d["lost_bopd"] for d in deferments),
        "deferments": deferments,
        "integrity": integrity,
    }


@router.get("/api/deferment", response_model=DefermentReport)
def deferment_report(
    due_within_days: int = DueWithinDays,
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    report = build_report(conn, due_within_days)
    logger.info(
        "deferment.report",
        extra={
            "user": user.email,
            "due_within_days": due_within_days,
            "deferment_count": len(report["deferments"]),
            "integrity_count": len(report["integrity"]),
        },
    )
    return report


@router.get("/deferment", response_class=HTMLResponse)
def deferment_page(
    request: Request,
    due_within_days: int = DueWithinDays,
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    report = build_report(conn, due_within_days)
    logger.info(
        "pages.deferment",
        extra={
            "user": user.email,
            "due_within_days": due_within_days,
            "deferment_count": len(report["deferments"]),
            "integrity_count": len(report["integrity"]),
        },
    )
    return templates.TemplateResponse(request, "deferment.html", {"user": user, **report})
