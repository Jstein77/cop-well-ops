from datetime import date

from app.routers.dashboard import inspection_overdue
from tests.conftest import NO_ROLES, READER


def test_dashboard_requires_auth(client):
    assert client.get("/dashboard").status_code == 401


def test_dashboard_requires_reader_role(client):
    assert client.get("/dashboard", headers=NO_ROLES).status_code == 403


def test_dashboard_shows_all_wells_and_totals(client):
    response = client.get("/dashboard", headers=READER)
    assert response.status_code == 200
    assert "12 wells shown" in response.text
    assert "Ptarmigan-7" in response.text
    assert "10,715" in response.text  # total oil bopd across seed data


def test_dashboard_filters_by_status(client):
    response = client.get("/dashboard", params={"status": "shut_in"}, headers=READER)
    assert "2 wells shown" in response.text
    assert "Muskox-12" in response.text
    assert "Caribou-3" not in response.text


def test_dashboard_filters_by_field_area(client):
    response = client.get("/dashboard", params={"field_area": "Icefall"}, headers=READER)
    assert "4 wells shown" in response.text
    assert "Grayling-2" in response.text


def test_dashboard_treats_injection_as_plain_value(client):
    response = client.get("/dashboard", params={"field_area": "' OR 1=1 --"}, headers=READER)
    assert response.status_code == 200
    assert "0 wells shown" in response.text


def test_dashboard_rejects_unknown_status(client):
    response = client.get("/dashboard", params={"status": "exploded"}, headers=READER)
    assert response.status_code == 422


def test_dashboard_flags_overdue_inspections(client):
    response = client.get("/dashboard", headers=READER)
    assert 'data-overdue="Sandpiper-5"' in response.text


def test_inspection_overdue_boundary():
    today = date(2026, 10, 1)
    assert inspection_overdue("2026-07-01", today)
    assert not inspection_overdue("2026-07-03", today)
