import sqlite3
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


def production_totals(conn: sqlite3.Connection) -> dict[str, Any]:
    return fetch_one(
        conn,
        "SELECT SUM(oil_bopd) AS oil_bopd, SUM(target_oil_bopd) AS target_oil_bopd FROM wells",
    )


def list_deferments(conn: sqlite3.Connection, planned: bool | None = None) -> list[dict[str, Any]]:
    """Every well producing below target, largest loss first.

    Wells without a logged deferment have NULL cause and count as unplanned.
    """
    return fetch_all(
        conn,
        "SELECT wells.id, wells.name, wells.pad, wells.status,"
        " wells.target_oil_bopd - wells.oil_bopd AS lost_bopd,"
        " deferments.cause, COALESCE(deferments.planned, 0) AS planned, deferments.owner,"
        " deferments.next_action, deferments.expected_restart"
        " FROM wells LEFT JOIN deferments ON deferments.well_id = wells.id"
        " WHERE wells.target_oil_bopd > wells.oil_bopd"
        " AND (? IS NULL OR COALESCE(deferments.planned, 0) = ?)"
        " ORDER BY lost_bopd DESC",
        (planned, planned),
    )


def list_integrity_due(conn: sqlite3.Connection, due_by: str) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT integrity_checks.*, wells.name AS well_name FROM integrity_checks"
        " JOIN wells ON wells.id = integrity_checks.well_id"
        " WHERE integrity_checks.due_date <= ?"
        " ORDER BY integrity_checks.due_date",
        (due_by,),
    )
