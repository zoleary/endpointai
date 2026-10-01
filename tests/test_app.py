import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main, zsai

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setattr(zsai, "CLIENT_ID", "")
    monkeypatch.setattr(zsai, "CLIENT_SECRET", "")


def test_status_is_mock_without_credentials():
    assert client.get("/api/status").json()["mode"] == "mock"


@pytest.mark.parametrize("scene", list(main.SCENES))
def test_every_scene_has_mock_data(scene):
    body = client.get(f"/api/scene/{scene}").json()
    assert body["mode"] == "mock"
    for panel in body["panels"]:
        assert panel["data"], f"{scene}/{panel['label']} has no mock data"


def test_unknown_scene_is_rejected():
    assert client.get("/api/scene/../../v1/admin/api-keys").status_code == 404
    assert client.get("/api/scene/nope").status_code == 404


def test_event_filters_are_passed_through():
    body = client.get("/api/scene/events?ef_verdict=block&user=a@b.c").json()
    params = body["panels"][1]["params"]
    assert params["ef_verdict"] == "block" and params["user"] == "a@b.c"


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "Demo Lab" in r.text


def test_live_mode_uses_token_and_surfaces_errors(monkeypatch):
    monkeypatch.setattr(zsai, "CLIENT_ID", "id")
    monkeypatch.setattr(zsai, "CLIENT_SECRET", "secret")

    def fake_get(path, params=None):
        if path == "/v1/overview/risk":
            raise zsai.ZsaiError(403, "forbidden", "req-123")
        return {"events_total": 1}

    monkeypatch.setattr(zsai, "get", fake_get)
    body = client.get("/api/scene/overview").json()
    assert body["mode"] == "live"
    assert body["panels"][0]["data"] == {"events_total": 1}
    assert body["panels"][1]["error"]["request_id"] == "req-123"


def test_secret_never_in_responses(monkeypatch):
    monkeypatch.setattr(zsai, "CLIENT_SECRET", "sqrx_sk_SHOULD_NOT_LEAK")
    for path in ["/api/status", "/api/scene/overview"]:
        assert "SHOULD_NOT_LEAK" not in client.get(path).text


def test_mock_files_are_valid_json():
    for f in Path("app/mock").glob("*.json"):
        json.loads(f.read_text())
