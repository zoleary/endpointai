#!/usr/bin/env bash
# READ-ONLY (plus one dry-run validate). Prints what's needed to match the tenant's policy format.
# Usage: scripts/inspect-policy-format.sh      (run it; don't "source" it)
. "$(dirname "$0")/_auth.sh"
S=$(ls -d "$(dirname "$0")"/../snapshot/* 2>/dev/null | tail -1)
[ -n "$S" ] || { echo "Run scripts/snapshot.sh first"; exit 1; }

echo "=== 1. Full validation error (dry run, nothing saved) ==="
curl -s -X POST "$API/v1/policies/validate" -H "$H" -H "Content-Type: application/json" \
  --data @"$(dirname "$0")/../policies/02-dangerous-commands.json" | jq . | head -40

echo; echo "=== 2. Supported rule types and sample patterns ==="
jq '{ruleTypes, categoryToRuleType, total, sample: .patterns[0:3]}' "$S/policy_patterns.json" | head -60

echo; echo "=== 3. Shape of one existing policy (first 2 rules) ==="
jq '.policies[0] | if .rules then (.rules |= .[0:2]) else . end' "$S/policies.json" | head -60
