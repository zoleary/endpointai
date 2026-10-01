"""Demo dashboard for Zscaler Endpoint AI Security.

Each "scene" matches a section of docs/TALK_TRACK.md and maps to a fixed list of
read-only API calls. The browser can only request scenes by name, so it can
never reach arbitrary API paths.
"""
import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse

from app import zsai

BASE = Path(__file__).parent
MOCK_DIR = BASE / "mock"

# scene -> list of (label, path, params)
SCENES = {
    "overview": [
        ("KPIs", "/v1/overview/kpis", {}),
        ("Risk", "/v1/overview/risk", {}),
    ],
    "devices": [
        ("Device stats", "/v1/devices/stats", {}),
        ("Devices", "/v1/devices", {"limit": 25}),
    ],
    "ai-apps": [
        ("AI assistants", "/v1/ai_assistants", {}),
        ("Models", "/v1/models", {}),
        ("Applications", "/v1/applications", {}),
        ("Browser extensions", "/v1/extensions", {}),
    ],
    "agent-supply-chain": [
        ("Agent summary", "/v1/agents/summary", {}),
        ("MCP servers", "/v1/agents/mcp-servers", {"limit": 25}),
        ("Skills", "/v1/agents/skills", {"limit": 25}),
        ("Plugins", "/v1/agents/plugins", {"limit": 25}),
        ("Hooks", "/v1/agents/hooks", {"limit": 25}),
    ],
    "events": [
        ("Event counts", "/v1/events/counts", {}),
        ("Recent events", "/v1/events", {"limit": 25}),
    ],
    "frameworks": [
        ("OWASP / MITRE ATLAS", "/v1/events/pattern-summary", {}),
    ],
    "policies": [
        ("Policies", "/v1/policies", {}),
        ("Setting profiles", "/v1/setting-profiles", {}),
    ],
    "attack-paths": [
        ("Risk graph", "/v1/agents/risk-graph", {}),
        ("MCP attack flow", "/v1/agents/mcp-attack-flow", {}),
    ],
}


app = FastAPI(title="Zscaler AI Endpoint Demo Lab")


def _mock(scene: str, label: str):
    f = MOCK_DIR / f"{scene}.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text()).get(label, {})


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/status")
def status():
    return {"mode": "live" if zsai.live_enabled() else "mock",
            "api_host": zsai.API_HOST, "scenes": list(SCENES)}


@app.get("/api/scene/{scene}")
def scene(scene: str, days: int = Query(30, ge=1, le=365),
          ef_verdict: str | None = None, ef_severity: str | None = None,
          ef_owasp: str | None = None, ef_atlas: str | None = None,
          ef_tool: str | None = None, ef_client: str | None = None,
          user: str | None = None, host: str | None = None):
    if scene not in SCENES:
        return JSONResponse({"error": "unknown_scene"}, status_code=404)
    filters = {k: v for k, v in {
        "ef_verdict": ef_verdict, "ef_severity": ef_severity, "ef_owasp": ef_owasp,
        "ef_atlas": ef_atlas, "ef_tool": ef_tool, "ef_client": ef_client,
        "user": user, "host": host}.items() if v}
    live = zsai.live_enabled()
    panels = []
    for label, path, params in SCENES[scene]:
        p = {"days": days, **params}
        if scene == "events":
            p.update(filters)
        panel = {"label": label, "call": f"GET {path}", "params": p}
        if not live:
            panel["data"] = _mock(scene, label)
        else:
            try:
                panel["data"] = zsai.get(path, p)
            except zsai.ZsaiError as e:
                panel["error"] = e.as_dict()
            except Exception as e:  # network errors etc.
                panel["error"] = {"error": type(e).__name__, "detail": str(e)[:200]}
        panels.append(panel)
    return {"scene": scene, "mode": "live" if live else "mock", "panels": panels}


@app.get("/api/effective-policy")
def effective_policy(email: str):
    if not zsai.live_enabled():
        return {"mode": "mock", "data": _mock("policies", "Effective policy")}
    try:
        return {"mode": "live", "data": zsai.get("/v1/policies/effective", {"email": email})}
    except zsai.ZsaiError as e:
        return JSONResponse({"error": e.as_dict()}, status_code=502)


@app.get("/api/event-detail")
def event_detail(id: str):
    if not zsai.live_enabled():
        return {"mode": "mock", "data": {"id": id, "note": "Event detail is only available in live mode"}}
    try:
        return {"mode": "live", "data": zsai.get("/v1/events/detail", {"id": id})}
    except zsai.ZsaiError as e:
        return JSONResponse({"error": e.as_dict()}, status_code=502)
