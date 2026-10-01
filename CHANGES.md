# Change log

| Date | Change | Result | Notes |
|---|---|---|---|
| 2026-09-30 | Token test with zsh `read -s -p` | failed | zsh `read` has no `-p`, so the secret was empty and the API returned `invalid_client` |
| 2026-09-30 | Token from `use2` regional host | failed | Not a token endpoint (returns non-JSON). Tokens come from `https://id.zsai.sqrx.io` |
| 2026-09-30 | `pbpaste` inside a pasted command block | failed | Clipboard held the pasted commands (234 characters) instead of the secret |
| 2026-09-30 | `setsec` alias, then copy secret, then type `setsec` | worked | Length 56, token `expires_in: 900` |
| 2026-09-30 | `GET /v1/overview/kpis` with Bearer token | worked | 4,898 events, 3 hosts, 4 users, 163 sessions |
| 2026-09-30 | Push demo code from earlier session to GitHub | failed | 403 error: Claude GitHub App has no access to `zoleary/endpointai` |
| 2026-10-01 | Built dashboard (FastAPI + single HTML page, 8 scenes, live/mock) | worked | 17 pytest tests pass. Playwright screenshot shows no JS errors (mock mode) |
| 2026-10-01 | Dockerfile + docker-compose.yml | not tested | No Docker daemon in the build environment. Test on the Mac with `docker compose up -d --build` |
| 2026-10-01 | Endpoint kit (`setup-lab.sh`, poisoned MCP server, risky skill, hook) | worked (setup only) | Setup script and MCP server self-tested. Zscaler detections not yet tested |
| 2026-10-01 | Policy template `policies/lab-baseline.json` | not tested | `match.field` names are placeholders; validate against `/v1/policies/patterns` |
| 2026-10-01 | Talk track + console settings (`docs/TALK_TRACK.md`) | not tested | Run the full demo once and record results here |
