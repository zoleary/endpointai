#!/usr/bin/env bash
# Step 1 (default): DRY RUN. Validates policies/01-04 with POST /v1/policies/validate. Nothing is saved.
# Step 2: --apply   Asks y/N for EACH policy, then creates it with POST /v1/policies (needs an admin API key).
# Match items written as {"pattern_id": "..."} are filled in from your tenant's built-in patterns
# (latest snapshot/*/policy_patterns.json, so run scripts/snapshot.sh first).
# Policies are created but NOT assigned. Assign them in the console (docs/TEST_PLAN.md, section 3).
. "$(dirname "$0")/_auth.sh"
ROOT="$(dirname "$0")/.."
APPLY="${1:-}"
PAT=$(ls -d "$ROOT"/snapshot/* 2>/dev/null | tail -1)/policy_patterns.json
[ -f "$PAT" ] || { echo "Run scripts/snapshot.sh first (needed for built-in patterns)"; exit 1; }
BUILD="$(mktemp -d)"; trap 'rm -rf "$BUILD"' EXIT

for f in "$ROOT"/policies/0[1-4]-*.json; do
  name=$(jq -r .name "$f"); out="$BUILD/$(basename "$f")"
  jq --slurpfile P "$PAT" '
    .rules.rules[].match.any |= map(
      if (.pattern_id and (.value | not)) then
        . as $m | ([$P[0].patterns[] | select(.id == $m.pattern_id)][0]) as $p
        | if $p then {field: $p.field, op: "regex", value: $p.regex, pattern_id: $p.id}
          else ("WARNING: built-in pattern \($m.pattern_id) not found, skipped\n" | stderr | empty) end
      else . end)' "$f" > "$out"
  printf '\n== %s\n' "$name"
  curl -s -X POST "$API/v1/policies/validate" -H "$H" -H "Content-Type: application/json" --data @"$out" \
    | jq -c 'del(.version) | if (.error|not) and (.valid|not) then {response: .} else . end'
  if [ "$APPLY" = "--apply" ]; then
    read -r -p "Create \"$name\" in your tenant? [y/N] " ok
    if [ "$ok" = "y" ]; then
      curl -s -X POST "$API/v1/policies" -H "$H" -H "Content-Type: application/json" --data @"$out" \
        | jq -c '{id, name, error, message, request_id} | with_entries(select(.value != null))'
    else
      echo "skipped"
    fi
  fi
done
[ "$APPLY" = "--apply" ] || echo -e "\nDry run only. Re-run with --apply to create the policies."
