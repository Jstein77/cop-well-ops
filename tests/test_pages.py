from tests.conftest import NO_ROLES, READER


def test_well_register_lists_wells_by_pad(client):
    response = client.get("/", headers=READER)
    assert response.status_code == 200
    assert "12 wells across 4 pads" in response.text
    assert "Ptarmigan-7" in response.text
    assert "reader@example.com" in response.text


def test_well_register_requires_auth(client):
    assert client.get("/").status_code == 401


def test_well_register_requires_reader_role(client):
    assert client.get("/", headers=NO_ROLES).status_code == 403


def test_well_detail_shows_status_note_and_shift_log(client):
    response = client.get("/wells/3", headers=READER)
    assert response.status_code == 200
    assert "Muskox-12" in response.text
    assert "ESP tripped on high motor temperature" in response.text
    assert "Rig crew confirmed for pump change" in response.text


def test_well_detail_requires_auth(client):
    assert client.get("/wells/3").status_code == 401


def test_well_detail_requires_reader_role(client):
    assert client.get("/wells/3", headers=NO_ROLES).status_code == 403


def test_well_detail_missing_well_returns_404(client):
    assert client.get("/wells/999", headers=READER).status_code == 404


def test_well_detail_rejects_non_numeric_id(client):
    assert client.get("/wells/abc", headers=READER).status_code == 422


def test_api_docs_are_disabled(client):
    assert client.get("/docs").status_code == 404
