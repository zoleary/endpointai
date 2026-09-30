# Change log

Result values: **worked** / **not tested** / **failed**.

| Date | Change | Result | Notes |
|---|---|---|---|
| 2026-09-30 | Started Zscaler **AI Guard** demo (prompt/response scanning chat app) | not tested (superseded) | Built and passing 16 tests in mock mode, then the direction changed. Saved on local branch `archive/aiguard-demo` (not pushed). `docs/zsai-api-reference.md` was not in the repo. |
| 2026-09-30 | **Direction change: AI Guard → Endpoint AI Security (zsai)** | worked | The parent session confirmed the product is Endpoint AI Security. AI Guard code is not included in this branch. |
| 2026-09-30 | `app/zsai.py`: API client with token cache (~15 min, re-mint on 401 `token_expired`), retry + jittered backoff on 429/5xx, error mapping `{status, error, message, request_id}` | worked (unit-tested with fake HTTP) | Not yet run against a real tenant. |
| 2026-09-30 | Read-only whitelist: known GET paths + `POST /v1/policies/validate` only; all writes → 403 | worked | Tested in pytest and the browser. |
| 2026-09-30 | Mock mode with sample data in `app/mock_data/` (agents, unscanned MCP server, tool-poisoning MCP server, blocked `rm -rf` and `~/.aws/credentials` events, prompt injection → LLM01 / AML.T0051) | worked | Default when `CLIENT_ID`/`CLIENT_SECRET` are unset. |
| 2026-09-30 | UI: Overview, AI inventory (Not scanned badge), Threat events (cursor paging, filters, detail drawer, OWASP/ATLAS summary), Devices (filters), Policies (rules, effective by email, validate playground), API explorer (curl per call, `$TOKEN` placeholder) | worked (mock) | Playwright smoke test clicked through every tab with no JS errors. |
| 2026-09-30 | pytest suite: 53 tests | worked | `.venv/bin/python -m pytest -q` |
| 2026-09-30 | `run.sh`, `Dockerfile`, `.env.example`, README with 5-minute demo script | worked (run.sh) / not tested (Docker) | run.sh tested; Docker not built here. |
| 2026-09-30 | **Live mode against a real tenant** | not tested yet | Needs your CLIENT_ID/CLIENT_SECRET. Docs host was blocked from the build env, so live response shapes may differ from mock; the UI renders them generically. |
