"""Read-only client for the Zscaler Endpoint AI Security (zsai) API.

- Mints a token from the identity host with HTTP basic auth and caches it until
  shortly before it expires. Re-mints once on 401 token_expired.
- Backs off with jitter on 429.
- Only issues GET requests. The secret is never logged or returned.
"""
import os
import random
import time

import httpx

ID_HOST = os.getenv("ZSAI_ID_HOST", "https://id.zsai.sqrx.io").rstrip("/")
API_HOST = os.getenv("ZSAI_API_HOST", "https://use2.api.zsai.sqrx.io").rstrip("/")
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
TIMEOUT = float(os.getenv("ZSAI_TIMEOUT", "20"))


class ZsaiError(Exception):
    def __init__(self, status, error, request_id=None, detail=None):
        super().__init__(f"{status} {error}")
        self.status = status
        self.error = error
        self.request_id = request_id
        self.detail = detail

    def as_dict(self):
        return {"status": self.status, "error": self.error,
                "request_id": self.request_id, "detail": self.detail}


def live_enabled() -> bool:
    return bool(CLIENT_ID and CLIENT_SECRET) and os.getenv("ZSAI_MODE", "auto") != "mock"


_token = {"value": None, "expires_at": 0.0}


def _mint_token(client: httpx.Client) -> str:
    r = client.post(f"{ID_HOST}/v1/auth/token", auth=(CLIENT_ID, CLIENT_SECRET))
    body = _json(r)
    if r.status_code != 200 or "access_token" not in body:
        raise ZsaiError(r.status_code, body.get("error", "token_failed"), body.get("request_id"))
    _token["value"] = body["access_token"]
    # Refresh 60s early so a request never goes out with a dying token.
    _token["expires_at"] = time.time() + int(body.get("expires_in", 900)) - 60
    return _token["value"]


def _get_token(client: httpx.Client, force: bool = False) -> str:
    if force or not _token["value"] or time.time() >= _token["expires_at"]:
        return _mint_token(client)
    return _token["value"]


def _json(r: httpx.Response) -> dict:
    try:
        data = r.json()
        return data if isinstance(data, dict) else {"data": data}
    except ValueError:
        return {"error": "non_json_response", "detail": r.text[:200]}


def get(path: str, params: dict | None = None) -> dict | list:
    """GET a regional API path, e.g. get('/v1/overview/kpis', {'days': 7})."""
    with httpx.Client(timeout=TIMEOUT) as client:
        retried_auth = False
        for attempt in range(4):
            token = _get_token(client)
            r = client.get(f"{API_HOST}{path}", params=params or {},
                           headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 200:
                return r.json()
            body = _json(r)
            err = body.get("error", "http_error")
            if r.status_code == 401 and err in ("token_expired", "token_invalid") and not retried_auth:
                _get_token(client, force=True)
                retried_auth = True
                continue
            if r.status_code == 429 and attempt < 3:
                time.sleep((2 ** attempt) + random.random())
                continue
            raise ZsaiError(r.status_code, err, body.get("request_id"), body.get("detail"))
    raise ZsaiError(429, "rate_limited")
