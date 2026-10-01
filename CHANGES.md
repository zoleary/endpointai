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
| 2026-10-01 | Replaced single baseline policy with 5 policies (secrets, dangerous commands, exfiltration, supply chain, add-on deny list) | worked (offline) | 16 rule patterns tested with should-match / should-not-match commands (34 tests pass). Not yet validated in the tenant |
| 2026-10-01 | `scripts/create-policies.sh` (dry run, `--apply` asks per policy) | not tested | Needs Mac + API key; `--apply` needs an admin key |
| 2026-10-01 | `docs/TEST_PLAN.md`: 6 discovery + 24 enforcement + 5 reporting tests | not tested | Run and fill in the Results log |
| 2026-10-01 | Lab adds fake `keys/id_rsa`, `.aws/credentials`, `.kube/config` inside `~/zsai-demo` | worked | Real `~/.ssh` and `~/.aws` are never touched |
| 2026-10-01 | Read real policy format from snapshot | worked | `op: regex`; fields `prompt` / `tool_input.command` / `tool_input_text` / `tool_output`; rules nested as `rules.rules`; rule has `ruleType`, `events`, `verdict`, `reason`, `agent_message` |
| 2026-10-01 | Rewrote policies 01–04 in tenant format; Lab 01 now uses built-in patterns by `pattern_id` | not tested | `create-policies.sh` fills in built-in regexes from the latest snapshot. 38 offline tests pass |
| 2026-10-01 | `scripts/probe-validate.sh` | worked | Validator accepts only `{"rules": [...]}` (option D); full policy object is rejected |
| 2026-10-01 | `create-policies.sh` validates with `{rules: [...]}`; create falls back to a flat shape if the first is rejected | not tested | — |
| 2026-10-01 | `create-policies.sh` dry run | worked | All 4 policies `{"valid":true,"errors":[]}` |
| 2026-10-01 | `create-policies.sh --apply` | worked | Created Lab 01 (id 1256), Lab 02 (1257), Lab 03 (1258), Lab 04 (1259). First body shape accepted, no fallback needed |
| 2026-10-01 | Talk track published as a Google Doc with copy-paste command boxes | worked | "Zscaler AI Endpoint Security Demo Talk Track" in Google Drive; line breaks in boxes verified via plain-text export |
| 2026-10-01 | Test plan published as a Google Doc (copy-paste boxes, Result columns, setup steps S3–S6 and S8 marked Pass) | worked | "Zscaler AI Endpoint Security Lab Test Plan" in Google Drive |
