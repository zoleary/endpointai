#!/usr/bin/env bash
# Step 1 (default): DRY RUN. Validates policies/01-04 with POST /v1/policies/validate. Nothing is saved.
# Step 2: --apply   Asks y/N for EACH policy, then creates it with POST /v1/policies (needs an admin API key).
# Policies are created but NOT assigned. Assign them in the console (see docs/TEST_PLAN.md, section 3).
. "$(dirname "$0")/_auth.sh"
APPLY="${1:-}"
for f in "$(dirname "$0")"/../policies/0[1-4]-*.json; do
  name=$(jq -r .name "$f")
  printf '\n== %s\n' "$name"
  curl -s -X POST "$API/v1/policies/validate" -H "$H" -H "Content-Type: application/json" --data @"$f" \
    | jq -c '{valid, errors, error, request_id} | with_entries(select(.value != null))'
  if [ "$APPLY" = "--apply" ]; then
    read -r -p "Create \"$name\" in your tenant? [y/N] " ok
    if [ "$ok" = "y" ]; then
      curl -s -X POST "$API/v1/policies" -H "$H" -H "Content-Type: application/json" --data @"$f" \
        | jq -c '{id, name, error, request_id} | with_entries(select(.value != null))'
    else
      echo "skipped"
    fi
  fi
done
[ "$APPLY" = "--apply" ] || echo -e "\nDry run only. Re-run with --apply to create the policies."
