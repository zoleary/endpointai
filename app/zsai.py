"""Zscaler Endpoint AI Security (zsai) API client: token cache, retry/backoff, error mapping.

Read-only by design: only whitelisted GET paths plus the POST /v1/policies/validate dry run.
"""
import json
import random
import re
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from .config import settings

# ------------------------------------------------------------------ whitelist
_GET_WHITELIST = [re.compile(p) for p in (
    r"/v1/overview/(kpis|timeseries|risk|sankey|heatmap|suggest)",
    r"/v1/devices",
    r"/v1/devices/(stats|facets)",
    r"/v1/devices/[\w-]+",
    r"/v1/ai_assistants(/(skills|mcp|classification|detail))?",
    r"/v1/agents/(summary|risk-graph|mcp-attack-flow|foreign-hooks)",
    r"/v1/agents/(skills|mcp-servers|mcp-capabilities|subagents|plugins|marketplaces|commands|hooks|instructions)",
    r"/v1/agents/detail/[\w-]+/[^/]+",
    r"/v1/models(/(page|detail|users))?",
    r"/v1/extensions(/(graph|workspaces|users))?",
    r"/v1/browsers(/(users|extensions))?",
    r"/v1/packages",
    r"/v1/applications",
    r"/v1/events(/(counts|facets|detail|pattern-summary|identity-summary))?",
    r"/v1/policies",
    r"/v1/policies/(effective|patterns)",
    r"/v1/policies/[\w-]+",
    r"/v1/readiness",
    r"/v1/drain",
)]
POST_WHITELIST = {"/v1/policies/validate"}
# Endpoints with no default cap: always send a limit.
_NEEDS_LIMIT = {"/v1/users", "/v1/groups", "/v1/device-groups"}


def is_allowed(method: str, path: str) -> bool:
    if ".." in path or "//" in path:
        return False
    if method == "GET":
        return any(p.fullmatch(path) for p in _GET_WHITELIST)
    if method == "POST":
        return path in POST_WHITELIST
    return False


class ZsaiError(Exception):
    def __init__(self, status: int, error: str, message: str = "", request_id: str | None = None):
        super().__init__(f"{status} {error}: {message}")
        self.status, self.error, self.message, self.request_id = status, error, message, request_id

    def to_dict(self) -> dict:
        return {"status": self.status, "error": self.error, "message": self.message, "request_id": self.request_id}


def error_from_response(r: httpx.Response) -> ZsaiError:
    try:
        body = r.json()
    except ValueError:
        body = {}
    if not isinstance(body, dict):
        body = {}
    err = body.get("error") or {400: "validation_failed", 401: "token_invalid", 403: "forbidden",
                                 404: "not_found", 409: "conflict", 429: "rate_limited"}.get(r.status_code, "http_error")
    if isinstance(err, dict):  # tolerate {"error": {"code":..., "message":...}}
        body = {**body, **err}
        err = err.get("code") or err.get("error") or "http_error"
    msg = body.get("message") or body.get("detail") or body.get("error_description") or (r.text[:300] if not body else "")
    rid = body.get("request_id") or r.headers.get("x-request-id")
    return ZsaiError(r.status_code, str(err), str(msg), rid)


def curl_for(method: str, path: str, params: dict | None = None, body: Any = None) -> str:
    """Teaching curl with $API/$TOKEN placeholders. Never includes the secret or token."""
    qs = ("?" + urlencode(params)) if params else ""
    if method == "GET":
        return f'curl -s "$API{path}{qs}" -H "Authorization: Bearer $TOKEN" | jq'
    return (f'curl -s -X {method} "$API{path}{qs}" -H "Authorization: Bearer $TOKEN" '
            f"-H 'Content-Type: application/json' -d '{json.dumps(body)}' | jq")


def _clean_params(path: str, params: dict | None) -> dict:
    p = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    if path in _NEEDS_LIMIT and "limit" not in p:
        p["limit"] = 50
    return p


# ------------------------------------------------------------------ live client
class LiveClient:
    mode = "live"
    max_retries = 3

    def __init__(self, http: httpx.Client | None = None):
        self._http = http or httpx.Client(timeout=settings.timeout)
        self._token: str | None = None
        self._token_exp = 0.0
        self._lock = threading.Lock()
        self.token_mints = 0

    def _token_value(self, force: bool = False) -> str:
        with self._lock:
            if not force and self._token and time.time() < self._token_exp - 30:
                return self._token
            if not (settings.client_id and settings.client_secret):
                raise ZsaiError(401, "invalid_client", "CLIENT_ID / CLIENT_SECRET not set")
            try:
                r = self._http.post(f"{settings.id_host}/v1/auth/token",
                                    auth=(settings.client_id, settings.client_secret))
            except httpx.HTTPError as e:
                raise ZsaiError(502, "connection_error", f"token request failed: {type(e).__name__}") from e
            if r.status_code >= 400:
                raise error_from_response(r)
            data = r.json()
            self._token = data["access_token"]
            self._token_exp = time.time() + float(data.get("expires_in", 900))
            self.token_mints += 1
            return self._token

    def request(self, method: str, path: str, params: dict | None = None, body: Any = None) -> Any:
        if not is_allowed(method, path):
            raise ZsaiError(403, "forbidden", f"{method} {path} is not allowed in this read-only demo")
        params = _clean_params(path, params)
        reminted = False
        for attempt in range(self.max_retries + 1):
            headers = {"Authorization": f"Bearer {self._token_value()}"}
            try:
                r = self._http.request(method, f"{settings.api_host}{path}", params=params, json=body, headers=headers)
            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    self._sleep(attempt)
                    continue
                raise ZsaiError(502, "connection_error", type(e).__name__) from e
            if r.status_code < 400:
                return r.json()
            err = error_from_response(r)
            if r.status_code == 401 and err.error in ("token_expired", "token_invalid", "no_session") and not reminted:
                reminted = True
                self._token_value(force=True)
                continue
            if (r.status_code == 429 or r.status_code >= 500) and attempt < self.max_retries:
                self._sleep(attempt, r.headers.get("retry-after"))
                continue
            raise err
        raise ZsaiError(502, "retries_exhausted", path)

    @staticmethod
    def _sleep(attempt: int, retry_after: str | None = None) -> None:
        try:
            base = float(retry_after) if retry_after else 0.5 * (2 ** attempt)
        except ValueError:
            base = 0.5 * (2 ** attempt)
        time.sleep(min(base, 8) + random.uniform(0, 0.3))  # backoff with jitter


# ------------------------------------------------------------------ mock client
MOCK_DIR = Path(__file__).parent / "mock_data"


def _load(name: str) -> Any:
    return json.loads((MOCK_DIR / f"{name}.json").read_text())


def _csv(v: str | None) -> set[str]:
    return {x.strip().lower() for x in (v or "").split(",") if x.strip()}


class MockClient:
    """Serves sample JSON from app/mock_data so the demo works offline."""
    mode = "mock"

    def __init__(self):
        self.overview, self.inventory = _load("overview"), _load("inventory")
        self.devices, self.events, self.policies = _load("devices"), _load("events"), _load("policies")

    def request(self, method: str, path: str, params: dict | None = None, body: Any = None) -> Any:
        if not is_allowed(method, path):
            raise ZsaiError(403, "forbidden", f"{method} {path} is not allowed in this read-only demo", "mock-req-403")
        p = _clean_params(path, params)
        if method == "POST":
            return self._validate(body)
        seg = path.split("/")[2:]  # ['overview','kpis']
        head = seg[0]
        if head == "overview":
            return self._get(self.overview, seg[1])
        if head == "devices":
            if len(seg) == 1:
                return self._devices(p)
            if seg[1] in ("stats", "facets"):
                return self.devices[seg[1]]
            return self._find(self.devices["items"], "id", seg[1])
        if head == "events":
            sub = seg[1] if len(seg) > 1 else ""
            if sub == "":
                return self._events(p)
            if sub == "detail":
                return self._find(self.events["items"], "id", p.get("id", ""))
            if sub == "pattern-summary":
                return self._pattern_summary()
            if sub == "counts":
                return self._counts()
            if sub == "facets":
                return self._facets()
            return self._get(self.events, sub)
        if head == "policies":
            if len(seg) == 1:
                return {"items": self.policies["items"], "total": len(self.policies["items"])}
            if seg[1] == "effective":
                return self._effective(p)
            if seg[1] == "patterns":
                return self.policies["patterns"]
            return self._find(self.policies["items"], "id", seg[1])
        if head == "agents" and len(seg) >= 4 and seg[1] == "detail":
            kind, key = seg[2], "/".join(seg[3:])
            item = self._find(self.inventory.get(kind, {}).get("items", []), "asset_key", key)
            return {**item, "kind": kind}
        key = "/".join(seg)
        return self._page(self._get(self.inventory, key), p)

    # helpers
    @staticmethod
    def _get(src: dict, key: str) -> Any:
        if key not in src:
            raise ZsaiError(404, "not_found", key, "mock-req-404")
        return src[key]

    @staticmethod
    def _find(items: list, field: str, value: str) -> dict:
        for it in items:
            if str(it.get(field)) == str(value):
                return it
        raise ZsaiError(404, "not_found", f"{field}={value}", "mock-req-404")

    @staticmethod
    def _page(data: Any, p: dict) -> Any:
        if not (isinstance(data, dict) and isinstance(data.get("items"), list)):
            return data
        items = data["items"]
        if p.get("q"):
            q = p["q"].lower()
            items = [i for i in items if q in json.dumps(i).lower()]
        limit, offset = int(p.get("limit", 50)), int(p.get("offset", 0))
        return {**data, "items": items[offset:offset + limit], "total": len(items), "limit": limit, "offset": offset}

    def _devices(self, p: dict) -> dict:
        items = self.devices["items"]
        for f in ("status", "health", "os"):
            if p.get(f):
                items = [d for d in items if str(d.get(f, "")).lower() == str(p[f]).lower()]
        for f in ("email", "host"):
            if p.get(f):
                items = [d for d in items if str(p[f]).lower() in str(d.get(f if f == "email" else "hostname", "")).lower()]
        limit = min(int(p.get("limit", 50)), 200)
        return self._page({"items": items}, {**p, "limit": limit})

    def _filtered_events(self, p: dict) -> list:
        items = self.events["items"]
        for dim in ("verdict", "severity", "owasp", "atlas", "tool", "client", "source", "event"):
            want = _csv(p.get(f"ef_{dim}"))
            if want:
                items = [e for e in items if want & {str(v).lower() for v in _as_list(e.get(dim))}]
        for f in ("user", "host"):
            if p.get(f):
                items = [e for e in items if str(p[f]).lower() in str(e.get(f, "")).lower()]
        if p.get("q"):
            items = [e for e in items if p["q"].lower() in json.dumps(e).lower()]
        return items

    def _events(self, p: dict) -> dict:
        items = self._filtered_events(p)
        limit = int(p.get("limit", 25))
        start = int(p.get("cursor") or 0)
        page = items[start:start + limit]
        nxt = str(start + limit) if start + limit < len(items) else ""
        trimmed = []
        for e in page:
            if e.get("partial"):
                e = {k: v for k, v in e.items() if k not in ("tool_input", "prompt_excerpt")}
            trimmed.append(e)
        return {"items": trimmed, "next_cursor": nxt}

    def _pattern_summary(self) -> dict:
        owasp, atlas = {}, {}
        for e in self.events["items"]:
            for o in _as_list(e.get("owasp")):
                owasp[o] = owasp.get(o, 0) + 1
            for a in _as_list(e.get("atlas")):
                atlas[a] = atlas.get(a, 0) + 1
        names = self.events["pattern_names"]
        return {
            "owasp": sorted([{"id": k, "name": names.get(k, k), "count": v} for k, v in owasp.items()], key=lambda x: -x["count"]),
            "atlas": sorted([{"id": k, "name": names.get(k, k), "count": v} for k, v in atlas.items()], key=lambda x: -x["count"]),
        }

    def _counts(self) -> dict:
        out: dict[str, int] = {"total": len(self.events["items"])}
        for e in self.events["items"]:
            out[e["verdict"]] = out.get(e["verdict"], 0) + 1
        return out

    def _facets(self) -> dict:
        facets: dict[str, dict[str, int]] = {}
        for e in self.events["items"]:
            for dim in ("verdict", "severity", "owasp", "atlas", "client", "tool", "user", "host"):
                for v in _as_list(e.get(dim)):
                    facets.setdefault(dim, {})[v] = facets.setdefault(dim, {}).get(v, 0) + 1
        return {d: [{"value": k, "count": c} for k, c in sorted(v.items(), key=lambda x: -x[1])] for d, v in facets.items()}

    def _effective(self, p: dict) -> dict:
        email = p.get("email") or p.get("group")
        if not email:
            raise ZsaiError(400, "validation_failed", "email or group is required", "mock-req-400")
        eff = self.policies["effective"]
        pol_ids = eff.get(email.lower(), eff["default"])
        pols = [x for x in self.policies["items"] if x["id"] in pol_ids]
        return {"email": email, "policies": [{"id": x["id"], "name": x["name"]} for x in pols],
                "rules": [r for x in pols for r in x.get("rules", [])]}

    @staticmethod
    def _validate(body: Any) -> dict:
        errors = []
        if not isinstance(body, dict):
            raise ZsaiError(400, "validation_failed", "body must be a JSON object", "mock-req-400")
        rules = body.get("rules")
        if not isinstance(rules, list) or not rules:
            errors.append({"path": "rules", "message": "rules must be a non-empty array"})
        for i, r in enumerate(rules or []):
            if not isinstance(r, dict):
                errors.append({"path": f"rules[{i}]", "message": "rule must be an object"})
                continue
            if r.get("verdict") not in ("block", "audit", "allow"):
                errors.append({"path": f"rules[{i}].verdict", "message": "must be block, audit or allow"})
            if "match" not in r:
                errors.append({"path": f"rules[{i}].match", "message": "required"})
            if not r.get("events"):
                errors.append({"path": f"rules[{i}].events", "message": "required, e.g. [\"PreToolUse\"]"})
        return {"valid": not errors, "errors": errors, "dry_run": True}


def _as_list(v: Any) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def make_client():
    return LiveClient() if settings.mode == "live" else MockClient()


def verdict_label(item: dict) -> str:
    """A missing verdict means NOT YET SCANNED, never 'clean'."""
    v = item.get("verdict") if isinstance(item, dict) else None
    return "not scanned" if v in (None, "") else str(v).lower()
