from tests.conftest import NO_ROLES, READER

AS_OF = {"as_of": "2026-09-30"}


def test_report_ranks_deferments_by_lost_bopd(client):
    report = client.get("/api/deferment-report", params=AS_OF, headers=READER).json()
    names = [d["well_name"] for d in report["deferments"]]
    assert names[:3] == ["Muskox-12", "Snowgoose-9", "Kestrel-8"]
    lost = [d["lost_bopd"] for d in report["deferments"]]
    assert lost == sorted(lost, reverse=True)
    assert report["total_lost_bopd"] == sum(lost)
    assert report["unplanned_lost_bopd"] == 1650 + 1100 + 340 + 245 + 60


def test_report_includes_cause_owner_action_and_restart(client):
    report = client.get("/api/deferment-report", params=AS_OF, headers=READER).json()
    muskox = report["deferments"][0]
    assert muskox["cause"] == "ESP failure"
    assert muskox["planned"] is False
    assert muskox["owner"] == "R. Okafor"
    assert muskox["next_action"] == "Pump change with workover rig"
    assert muskox["expected_restart"] == "2026-10-02"
    sandpiper = next(d for d in report["deferments"] if d["well_name"] == "Sandpiper-5")
    assert sandpiper["expected_restart"] is None


def test_report_lists_overdue_and_due_integrity_items(client):
    report = client.get("/api/deferment-report", params=AS_OF, headers=READER).json()
    items = [(i["well_name"], i["days_overdue"]) for i in report["integrity"]]
    assert items == [("Muskox-12", 42), ("Lynx-1", 30), ("Sandpiper-5", 10), ("Marten-10", -4)]


def test_report_within_days_widens_integrity_window(client):
    params = {**AS_OF, "within_days": 14}
    report = client.get("/api/deferment-report", params=params, headers=READER).json()
    names = {i["well_name"] for i in report["integrity"]}
    assert "Caribou-3" in names
    assert "Grayling-2" not in names


def test_report_requires_auth(client):
    assert client.get("/api/deferment-report").status_code == 401


def test_report_requires_reader_role(client):
    assert client.get("/api/deferment-report", headers=NO_ROLES).status_code == 403


def test_report_rejects_invalid_params(client):
    for params in ({"within_days": -1}, {"within_days": 91}, {"as_of": "yesterday"}):
        response = client.get("/api/deferment-report", params=params, headers=READER)
        assert response.status_code == 422, params


def test_deferment_page_renders_report(client):
    response = client.get("/deferments", params=AS_OF, headers=READER)
    assert response.status_code == 200
    assert "Morning deferment report" in response.text
    assert "Pump change with workover rig" in response.text
    assert "Not yet known" in response.text
    assert "42 days overdue" in response.text
    assert "Due in 4 days" in response.text


def test_deferment_page_requires_auth(client):
    assert client.get("/deferments").status_code == 401


def test_deferment_page_requires_reader_role(client):
    assert client.get("/deferments", headers=NO_ROLES).status_code == 403


def test_deferment_page_rejects_invalid_params(client):
    assert client.get("/deferments", params={"within_days": "x"}, headers=READER).status_code == 422
