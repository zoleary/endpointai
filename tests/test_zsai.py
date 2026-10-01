import httpx
import pytest

from app import zsai


@pytest.fixture
def transport(monkeypatch):
    calls = []
    state = {"token_n": 0, "expire_first": True}

    def handler(req: httpx.Request):
        calls.append((req.method, req.url.path))
        if req.url.path == "/v1/auth/token":
            assert req.headers["authorization"].startswith("Basic ")
            state["token_n"] += 1
            return httpx.Response(200, json={"access_token": f"t{state['token_n']}", "expires_in": 900})
        if state["expire_first"]:
            state["expire_first"] = False
            return httpx.Response(401, json={"error": "token_expired", "request_id": "r1"})
        if req.headers["authorization"] == "Bearer t2":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404, json={"error": "not_found", "request_id": "r2"})

    real = httpx.Client
    monkeypatch.setattr(zsai.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setattr(zsai, "CLIENT_ID", "id")
    monkeypatch.setattr(zsai, "CLIENT_SECRET", "secret")
    zsai._token.update(value=None, expires_at=0)
    return calls


def test_remints_once_on_token_expired(transport):
    assert zsai.get("/v1/overview/kpis") == {"ok": True}
    assert [p for _, p in transport].count("/v1/auth/token") == 2
    assert all(m in ("GET", "POST") for m, _ in transport)
    assert all(m == "GET" for m, p in transport if p != "/v1/auth/token")


def test_token_is_cached(transport):
    zsai.get("/v1/overview/kpis")
    zsai.get("/v1/overview/kpis")
    assert [p for _, p in transport].count("/v1/auth/token") == 2  # no extra mint on 2nd call
