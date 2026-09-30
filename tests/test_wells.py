from tests.conftest import NO_ROLES, READER


def test_health_is_public(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_home_page_renders_for_signed_in_user(client):
    response = client.get("/", headers=READER)
    assert response.status_code == 200
    assert "reader@example.com" in response.text


def test_list_wells_requires_auth(client):
    assert client.get("/api/wells").status_code == 401


def test_list_wells_requires_reader_role(client):
    assert client.get("/api/wells", headers=NO_ROLES).status_code == 403


def test_list_wells_returns_seed_data(client):
    wells = client.get("/api/wells", headers=READER).json()
    assert len(wells) == 12
    assert {"Ptarmigan-7", "Caribou-3"} <= {w["name"] for w in wells}


def test_list_wells_filters_by_status(client):
    wells = client.get("/api/wells", params={"status": "shut_in"}, headers=READER).json()
    assert wells
    assert all(w["status"] == "shut_in" for w in wells)


def test_list_wells_rejects_unknown_status(client):
    response = client.get("/api/wells", params={"status": "' OR 1=1 --"}, headers=READER)
    assert response.status_code == 422


def test_get_well(client):
    well = client.get("/api/wells/1", headers=READER).json()
    assert well["id"] == 1


def test_get_missing_well_returns_404(client):
    assert client.get("/api/wells/999", headers=READER).status_code == 404
