import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("NX_URL", "")
    monkeypatch.setenv("WEBHOOK_SECRET", "test-secret")
    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_health_mock(client):
    assert client.get("/api/health").json() == {"status": "ok", "mock": True}


def test_cameras(client):
    cams = client.get("/api/cameras").json()
    assert len(cams) == 4
    cam_id = cams[0]["id"]
    assert client.get(f"/api/cameras/{cam_id}").json()["name"] == cams[0]["name"]
    assert client.get("/api/cameras/no-existe").status_code == 404
    thumb = client.get(f"/api/cameras/{cam_id}/thumbnail")
    assert thumb.headers["content-type"] == "image/png"


def test_stream_config(client):
    cfg = client.get("/api/cameras/abc/stream").json()
    assert cfg["mock"] is True
    assert cfg["systemId"] == "mock-system"
    assert cfg["cameraId"] == "abc"


def test_objects_filter(client):
    cam_id = client.get("/api/cameras").json()[1]["id"]
    objs = client.get("/api/analytics/objects", params={"deviceId": cam_id, "limit": 5}).json()
    assert len(objs) == 5
    assert all(o["deviceId"] == cam_id for o in objs)


def test_generic_event_appears_in_log(client):
    r = client.post("/api/events/generic", json={"caption": "Persona en zona", "cameraIds": ["x"]})
    assert r.status_code == 202
    events = client.get("/api/events").json()
    assert events[0]["caption"] == "Persona en zona"
    assert events[0]["deviceId"] == "x"


def test_webhook_secret(client):
    assert client.post("/api/webhooks/nx?secret=mal", json={}).status_code == 403
    assert client.post("/api/webhooks/nx?secret=test-secret", json={"event": "x"}).status_code == 204
    assert client.get("/api/webhooks/nx").json()[0]["payload"] == {"event": "x"}


def test_course_modules(client):
    mods = client.get("/api/course/modules").json()
    assert len(mods) == 10 and mods[0]["order"] == 1
    assert client.get(f"/api/course/modules/{mods[2]['slug']}").json()["lab"] == "camaras"
