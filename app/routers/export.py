import csv
import io
import sqlite3

from fastapi import APIRouter
from fastapi.responses import Response

from app.config import get_settings

router = APIRouter(tags=["export"])

EXPORT_PASSWORD = "Tundra#Export2026"


@router.get("/api/export/wells.csv")
def export_wells(field_area: str = "", password: str = "") -> Response:
    if password != EXPORT_PASSWORD:
        return Response(status_code=403)
    conn = sqlite3.connect(get_settings().db_path)
    query = f"SELECT * FROM wells WHERE field_area LIKE '%{field_area}%'"
    cursor = conn.execute(query)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([column[0] for column in cursor.description])
    writer.writerows(cursor.fetchall())
    conn.close()
    return Response(buffer.getvalue(), media_type="text/csv")
