#!/usr/bin/env bash
# READ-ONLY. Saves your tenant's current config to ./snapshot/ so the demo can be tailored.
# Output contains policy JSON but no secrets. Review before sharing.
. "$(dirname "$0")/_auth.sh"
OUT="snapshot/$(date +%Y%m%d-%H%M%S)"; mkdir -p "$OUT"
get() { curl -s "$API$2" -H "$H" > "$OUT/$1.json"; printf '%-22s %s\n' "$1" "$(jq -c 'if type=="object" then (keys|.[0:6]) else "list(\(length))" end' "$OUT/$1.json" 2>/dev/null)"; }
get kpis              "/v1/overview/kpis?days=30"
get devices_stats     "/v1/devices/stats"
get policies          "/v1/policies"
get policy_patterns   "/v1/policies/patterns"
get setting_profiles  "/v1/setting-profiles"
get data_lists        "/v1/data-lists"
get groups            "/v1/groups?limit=50"
get device_groups     "/v1/device-groups?limit=50"
get agents_summary    "/v1/agents/summary?days=30"
get event_counts      "/v1/events/counts?days=30"
get settings          "/v1/settings"
echo "Saved to $OUT"
