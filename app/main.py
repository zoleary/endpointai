"""Read-only Endpoint AI Security demo: FastAPI proxy + single-page UI."""
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from . import zsai
from .config import settings

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="Zscaler Endpoint AI Security Demo")
client = zsai.make_client()


def _call(method: str, path: str, params: dict, body=None) -> JSONResponse:
    curl = zsai.curl_for(method, path, params, body)
    t0 = time.perf_counter()
    try:
        data = client.request(method, path, params, body)
    except zsai.ZsaiError as e:
        return JSONResponse({"ok": False, **e.to_dict(), "curl": curl,
                             "ms": round((time.perf_counter() - t0) * 1000, 1)}, status_code=e.status)
    return JSONResponse({"ok": True, "data": data, "curl": curl, "ms": round((time.perf_counter() - t0) * 1000, 1)})


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/status")
def status():
    return {"mode": settings.mode, "region": settings.region, "api": settings.api_host, "id": settings.id_host,
            "client_id_set": bool(settings.client_id), "secret_set": bool(settings.client_secret),
            "read_only": True}


@app.post("/api/zsai/v1/policies/validate")
async def validate(request: Request):
    try:
        body = await request.json()
    except ValueError:
        body = None
    return _call("POST", "/v1/policies/validate", {}, body)


@app.get("/api/zsai/{path:path}")
def proxy_get(path: str, request: Request):
    return _call("GET", "/" + path, dict(request.query_params))


@app.api_route("/api/zsai/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"])
def proxy_write(path: str, request: Request):
    e = zsai.ZsaiError(403, "forbidden", f"{request.method} /{path} is blocked: this demo is read-only", "demo-readonly")
    return JSONResponse({"ok": False, **e.to_dict(), "curl": ""}, status_code=403)
