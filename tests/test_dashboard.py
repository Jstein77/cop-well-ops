import re
from datetime import date

from app.routers.dashboard import days_until
from tests.conftest import NO_ROLES, READER


def worklist_wells(html: str) -> list[str]:
    return re.findall(r'data-well="([^"]+)"', html)


def test_morning_report_requires_auth(client):
    assert client.get("/dashboard").status_code == 401


def test_morning_report_requires_reader_role(client):
    assert client.get("/dashboard", headers=NO_ROLES).status_code == 403


def test_morning_report_shows_rate_and_deferment_split(client):
    response = client.get("/dashboard", headers=READER)
    assert response.status_code == 200
    assert "10,715" in response.text  # oil rate
    assert "16,750" in response.text  # forecast
    assert "6,140" in response.text  # deferred
    assert "2,650" in response.text  # planned
    assert "3,490" in response.text  # unplanned, including wells with no logged cause


def test_worklist_ranks_wells_by_lost_barrels(client):
    wells = worklist_wells(client.get("/dashboard", headers=READER).text)
    assert wells == [
        "Muskox-12", "Snowgoose-9", "Kestrel-8", "Sandpiper-5", "Wolverine-4",
        "Marten-10", "Ptarmigan-7", "Raven-11", "Lynx-1",
    ]  # fmt: skip


def test_worklist_shows_cause_owner_and_restart(client):
    html = client.get("/dashboard", headers=READER).text
    row = html.split('data-well="Muskox-12"')[1].split("</tr>")[0]
    assert "ESP failure" in row
    assert "R. Okafor" in row
    assert "Pump change with workover rig" in row
    assert "2026-10-02" in row


def test_wells_without_a_logged_cause_are_flagged(client):
    html = client.get("/dashboard", headers=READER).text
    row = html.split('data-well="Raven-11"')[1].split("</tr>")[0]
    assert "Not logged" in row


def test_worklist_filters_planned(client):
    response = client.get("/dashboard", params={"type": "planned"}, headers=READER)
    assert worklist_wells(response.text) == ["Snowgoose-9", "Kestrel-8"]


def test_worklist_filters_unplanned(client):
    response = client.get("/dashboard", params={"type": "unplanned"}, headers=READER)
    wells = worklist_wells(response.text)
    assert "Snowgoose-9" not in wells
    assert {"Muskox-12", "Raven-11", "Lynx-1"} <= set(wells)


def test_worklist_accepts_all_option(client):
    response = client.get("/dashboard", params={"type": ""}, headers=READER)
    assert len(worklist_wells(response.text)) == 9


def test_morning_report_rejects_unknown_type(client):
    response = client.get("/dashboard", params={"type": "' OR 1=1 --"}, headers=READER)
    assert response.status_code == 422


def test_compliance_lists_overdue_checks(client):
    html = client.get("/dashboard", headers=READER).text
    compliance = html.split('class="due-list"')[1].split("</ul>")[0]
    assert 'data-due="Lynx-1"' in compliance
    assert "days overdue" in compliance


def test_days_until():
    today = date(2026, 9, 30)
    assert days_until("2026-10-04", today) == 4
    assert days_until("2026-09-20", today) == -10
