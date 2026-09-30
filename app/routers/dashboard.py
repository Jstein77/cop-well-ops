import sqlite3
from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from app import repository
from app.auth import User, require_reader
from app.db import get_db
from app.logging_config import get_logger
from app.templating import templates

router = APIRouter(tags=["dashboard"])
logger = get_logger(__name__)

COMPLIANCE_WINDOW_DAYS = 30
DefermentType = Literal["planned", "unplanned"]


def days_until(due: str, today: date) -> int:
    return (date.fromisoformat(due) - today).days


@router.get("/dashboard", response_class=HTMLResponse)
def morning_report(
    request: Request,
    deferment_type: DefermentType | Literal[""] | None = Query(None, alias="type"),
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    # The filter chips send "" for "All".
    selected = deferment_type or None
    today = date.today()

    all_deferments = repository.list_deferments(conn)
    worklist = (
        all_deferments
        if selected is None
        else repository.list_deferments(conn, planned=selected == "planned")
    )
    totals = repository.production_totals(conn)
    due_by = (today + timedelta(days=COMPLIANCE_WINDOW_DAYS)).isoformat()
    compliance = repository.list_integrity_due(conn, due_by)
    for check in compliance:
        check["days_until"] = days_until(check["due_date"], today)

    deferred = sum(d["lost_bopd"] for d in all_deferments)
    planned = sum(d["lost_bopd"] for d in all_deferments if d["planned"])

    logger.info(
        "dashboard.morning_report",
        extra={"user": user.email, "type": selected, "count": len(worklist)},
    )
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "today": today.isoformat(),
            "oil": totals["oil_bopd"],
            "forecast": totals["target_oil_bopd"],
            "deferred": deferred,
            "deferring_count": len(all_deferments),
            "planned": planned,
            "unplanned": deferred - planned,
            "worklist": worklist,
            "compliance": compliance,
            "overdue_count": sum(c["days_until"] < 0 for c in compliance),
            "window_days": COMPLIANCE_WINDOW_DAYS,
            "selected_type": selected,
        },
    )
