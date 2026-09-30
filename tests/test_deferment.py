from datetime import date

import pytest

from app.routers import deferment
from tests.conftest import NO_ROLES, READER


class FixedDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 9, 30)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(deferment, "date", FixedDate)


def test_report_ranks_wells_by_lost_bopd(client):
    report = client.get("/api/deferment", headers=READER).json()
    ranked = [(d["well_name"], d["lost_bopd"]) for d in report["deferments"]]
    assert ranked == [
        ("Muskox-12", 1650),
        ("Snowgoose-9", 1400),
        ("Kestrel-8", 1250),
        ("Sandpiper-5", 1100),
        ("Wolverine-4", 340),
        ("Marten-10", 245),
        ("Ptarmigan-7", 60),
    ]
    assert report["total_lost_bopd"] == 6045
    assert report["as_of"] == "2026-09-30"


def test_report_includes_cause_owner_action_and_restart(client):
    top = client.get("/api/deferment", headers=READER).json()["deferments"][0]
    assert top["cause"] == "ESP failure"
    assert top["planned"] is False
    assert top["owner"] == "R. Okafor"
    assert top["next_action"] == "Pump change with workover rig"
    assert top["expected_restart"] == "2026-10-02"


def test_report_allows_unknown_restart(client):
    deferments = client.get("/api/deferment", headers=READER).json()["deferments"]
    sandpiper = next(d for d in deferments if d["well_name"] == "Sandpiper-5")
    assert sandpiper["expected_restart"] is None


def test_report_lists_overdue_and_due_integrity_items(client):
    items = client.get("/api/deferment", headers=READER).json()["integrity"]
    assert [(i["well_name"], i["state"], i["days_overdue"]) for i in items] == [
        ("Muskox-12", "overdue", 42),
        ("Lynx-1", "overdue", 30),
        ("Sandpiper-5", "overdue", 10),
        ("Marten-10", "due", -4),
    ]


def test_report_due_window_is_configurable(client):
    items = client.get(
        "/api/deferment", params={"due_within_days": 0}, headers=READER
    ).json()["integrity"]
    assert {i["state"] for i in items} == {"overdue"}
    assert len(items) == 3


@pytest.mark.parametrize("value", ["-1", "91", "abc", "7; DROP TABLE wells"])
def test_report_rejects_invalid_due_window(client, value):
    response = client.get("/api/deferment", params={"due_within_days": value}, headers=READER)
    assert response.status_code == 422


def test_report_requires_auth(client):
    assert client.get("/api/deferment").status_code == 401


def test_report_requires_reader_role(client):
    assert client.get("/api/deferment", headers=NO_ROLES).status_code == 403


def test_page_renders_ranked_deferments_and_integrity(client):
    response = client.get("/deferment", headers=READER)
    assert response.status_code == 200
    text = response.text
    assert "Morning deferment report" in text
    assert "6,045" in text
    assert text.index("Muskox-12") < text.index("Snowgoose-9") < text.index("Ptarmigan-7")
    assert "Pump change with workover rig" in text
    assert "Not set" in text
    assert "Overdue 42d" in text
    assert "Due in 4d" in text


def test_page_requires_auth(client):
    assert client.get("/deferment").status_code == 401


def test_page_requires_reader_role(client):
    assert client.get("/deferment", headers=NO_ROLES).status_code == 403


def test_page_rejects_invalid_due_window(client):
    response = client.get("/deferment", params={"due_within_days": "-1"}, headers=READER)
    assert response.status_code == 422
