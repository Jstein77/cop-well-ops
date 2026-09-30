import sqlite3
from datetime import date
from typing import Any

from app.db import fetch_all, fetch_one


def list_wells(conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status:
        return fetch_all(conn, "SELECT * FROM wells WHERE status = ? ORDER BY name", (status,))
    return fetch_all(conn, "SELECT * FROM wells ORDER BY name")


def get_well(conn: sqlite3.Connection, well_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM wells WHERE id = ?", (well_id,))


def list_shift_log(
    conn: sqlite3.Connection, well_id: int | None = None, limit: int = 20
) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT shift_log.*, wells.name AS well_name FROM shift_log"
        " JOIN wells ON wells.id = shift_log.well_id"
        " WHERE (? IS NULL OR shift_log.well_id = ?)"
        " ORDER BY logged_at DESC LIMIT ?",
        (well_id, well_id, limit),
    )


def list_deferments(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT deferments.well_id, wells.name AS well_name, wells.pad, wells.status,"
        " MAX(wells.target_oil_bopd - wells.oil_bopd, 0) AS lost_bopd,"
        " deferments.cause, deferments.planned, deferments.owner, deferments.next_action,"
        " deferments.expected_restart"
        " FROM deferments JOIN wells ON wells.id = deferments.well_id"
        " ORDER BY lost_bopd DESC, wells.name",
    )


def list_integrity_due(
    conn: sqlite3.Connection, as_of: date, due_by: date
) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT integrity_checks.id, integrity_checks.well_id, wells.name AS well_name,"
        " integrity_checks.check_type, integrity_checks.due_date, integrity_checks.owner,"
        " CASE WHEN integrity_checks.due_date < ? THEN 'overdue' ELSE 'due' END AS state,"
        " CAST(julianday(?) - julianday(integrity_checks.due_date) AS INTEGER) AS days_overdue"
        " FROM integrity_checks JOIN wells ON wells.id = integrity_checks.well_id"
        " WHERE integrity_checks.due_date <= ?"
        " ORDER BY integrity_checks.due_date, wells.name",
        (as_of.isoformat(), as_of.isoformat(), due_by.isoformat()),
    )
