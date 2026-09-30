import httpx
import pytest
from fastapi.testclient import TestClient

from app import zsai
from app.config import settings
from app.main import app

client = TestClient(app)


# ------------------------------------------------------------ live client (fake transport)
@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(settings, "client_id", "cid")
    monkeypatch.setattr(settings, "client_secret", "sqrx_sk_test")
    monkeypatch.setattr(zsai.LiveClient, "_sleep", staticmethod(lambda *a, **k: None))
    calls = {"token": 0, "api": 0, "script": []}

    def handler(req: httpx.Request):
        if req.url.path == "/v1/auth/token":
            calls["token"] += 1
            assert req.headers["authorization"].startswith("Basic ")
            return httpx.Response(200, json={"access_token": f"tok{calls['token']}", "expires_in": 900})
        calls["api"] += 1
        assert "sqrx_sk_test" not in str(req.url)
        if calls["script"]:
            return calls["script"].pop(0)
        return httpx.Response(200, json={"ok": True, "auth": req.headers["authorization"]})

    c = zsai.LiveClient(httpx.Client(transport=httpx.MockTransport(handler)))
    return c, calls


def test_token_cached(live):
    c, calls = live
    c.request("GET", "/v1/overview/kpis", {"days": 7})
    c.request("GET", "/v1/devices/stats")
    assert calls["token"] == 1 and calls["api"] == 2


def test_token_reminted_on_expired(live):
    c, calls = live
    calls["script"] = [httpx.Response(401, json={"error": "token_expired", "request_id": "r1"})]
    out = c.request("GET", "/v1/overview/kpis")
    assert calls["token"] == 2 and out["auth"] == "Bearer tok2"


def test_error_mapping_with_request_id(live):
    c, calls = live
    calls["script"] = [httpx.Response(400, json={"error": "validation_failed", "message": "bad days", "request_id": "req-123"})]
    with pytest.raises(zsai.ZsaiError) as ei:
        c.request("GET", "/v1/overview/kpis", {"days": "x"})
    assert ei.value.to_dict() == {"status": 400, "error": "validation_failed", "message": "bad days", "request_id": "req-123"}


def test_rate_limit_retries(live):
    c, calls = live
    calls["script"] = [httpx.Response(429, json={"error": "rate_limited"}), httpx.Response(429, json={"error": "rate_limited"})]
    assert c.request("GET", "/v1/devices")["ok"]
    assert calls["api"] == 3


def test_live_rejects_writes_without_network(live):
    c, calls = live
    with pytest.raises(zsai.ZsaiError) as ei:
        c.request("DELETE", "/v1/policies/pol_default")
    assert ei.value.error == "forbidden" and calls["api"] == 0 and calls["token"] == 0


# ------------------------------------------------------------ whitelist / proxy
@pytest.mark.parametrize("method,path,ok", [
    ("GET", "/v1/overview/kpis", True), ("GET", "/v1/events/detail", True), ("POST", "/v1/policies/validate", True),
    ("POST", "/v1/policies", False), ("PUT", "/v1/policies/pol_default", False), ("DELETE", "/v1/devices/dev_1000", False),
    ("POST", "/v1/devices/dev_1000/revoke", False), ("GET", "/v1/admin/api-keys", False), ("GET", "/v1/enroll-tokens/1/reveal", False),
    ("GET", "/v1/../admin/members", False),
])
def test_whitelist(method, path, ok):
    assert zsai.is_allowed(method, path) is ok


@pytest.mark.parametrize("method", ["post", "put", "delete", "patch"])
def test_proxy_blocks_writes(method):
    r = getattr(client, method)("/api/zsai/v1/policies/pol_default")
    assert r.status_code == 403 and r.json()["error"] == "forbidden" and r.json()["request_id"]


def test_proxy_blocks_non_whitelisted_get():
    r = client.get("/api/zsai/v1/enroll-tokens/1/reveal")
    assert r.status_code == 403 and r.json()["request_id"]


def test_curl_never_has_secret():
    r = client.get("/api/zsai/v1/overview/kpis?days=7").json()
    assert r["curl"] == 'curl -s "$API/v1/overview/kpis?days=7" -H "Authorization: Bearer $TOKEN" | jq'


# ------------------------------------------------------------ page endpoints (mock mode)
PAGE_PATHS = [
    "/v1/overview/kpis?days=7", "/v1/overview/timeseries?days=7", "/v1/overview/risk?days=7", "/v1/devices/stats",
    "/v1/agents/summary", "/v1/ai_assistants", "/v1/agents/mcp-servers", "/v1/agents/skills", "/v1/agents/plugins",
    "/v1/agents/hooks", "/v1/models", "/v1/extensions?view=page", "/v1/agents/detail/mcp-servers/mcp:jira-helper",
    "/v1/events?limit=5", "/v1/events/pattern-summary", "/v1/events/counts", "/v1/events/facets", "/v1/events/detail?id=evt_9002",
    "/v1/devices?limit=5", "/v1/devices/dev_1000", "/v1/policies", "/v1/policies/pol_default",
    "/v1/policies/effective?email=frank.osei@acme.example",
]


@pytest.mark.parametrize("path", PAGE_PATHS)
def test_page_endpoints_return_data(path):
    r = client.get("/api/zsai" + path)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] and r.json()["data"]


def test_status():
    s = client.get("/api/status").json()
    assert s["mode"] == "mock" and s["read_only"] and "secret" not in str(s).replace("secret_set", "")


def test_events_cursor_paging_and_filters():
    first = client.get("/api/zsai/v1/events?limit=10").json()["data"]
    assert len(first["items"]) == 10 and first["next_cursor"]
    second = client.get(f"/api/zsai/v1/events?limit=10&cursor={first['next_cursor']}").json()["data"]
    assert {e["id"] for e in first["items"]}.isdisjoint(e["id"] for e in second["items"])
    denied = client.get("/api/zsai/v1/events?limit=100&ef_verdict=deny&ef_owasp=LLM01").json()["data"]["items"]
    assert denied and all(e["verdict"] == "deny" and "LLM01" in e["owasp"] for e in denied)


def test_prompt_injection_event_mapped():
    items = client.get("/api/zsai/v1/events?limit=100&ef_atlas=AML.T0051").json()["data"]["items"]
    assert any(e.get("category") == "prompt_injection" and "LLM01" in e["owasp"] for e in items)


def test_partial_event_needs_detail():
    items = client.get("/api/zsai/v1/events?limit=100").json()["data"]["items"]
    part = next(e for e in items if e.get("partial"))
    assert "tool_input" not in part and "prompt_excerpt" not in part
    full = client.get(f"/api/zsai/v1/events/detail?id={part['id']}").json()["data"]
    assert "tool_input" in full or "prompt_excerpt" in full


def test_device_filters():
    items = client.get("/api/zsai/v1/devices?status=offline&limit=200").json()["data"]["items"]
    assert items and all(d["status"] == "offline" for d in items)


def test_missing_verdict_is_not_scanned():
    items = client.get("/api/zsai/v1/agents/mcp-servers").json()["data"]["items"]
    unscanned = [i for i in items if "verdict" not in i]
    assert unscanned, "mock data should include an unscanned MCP server"
    assert zsai.verdict_label(unscanned[0]) == "not scanned"
    assert zsai.verdict_label({"verdict": "block"}) == "block"


def test_error_includes_request_id_in_mock():
    r = client.get("/api/zsai/v1/policies/nope")
    assert r.status_code == 404 and r.json()["error"] == "not_found" and r.json()["request_id"]


def test_policy_validate_dry_run():
    good = {"rules": [{"id": "a", "ruleType": "tool_guard", "match": {"field": "tool", "op": "eq", "value": "Bash"},
                       "events": ["PreToolUse"], "verdict": "block", "reason": "x"}]}
    assert client.post("/api/zsai/v1/policies/validate", json=good).json()["data"]["valid"] is True
    bad = client.post("/api/zsai/v1/policies/validate", json={"rules": [{"verdict": "deny"}]}).json()["data"]
    assert bad["valid"] is False and bad["errors"]


def test_index_served():
    assert "Endpoint AI Security" in client.get("/").text
