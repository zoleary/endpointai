#!/usr/bin/env bash
# DRY RUN ONLY. Sends your existing (known-good) first policy to POST /v1/policies/validate
# wrapped five different ways, to find the body shape the validator expects. Nothing is saved.
. "$(dirname "$0")/_auth.sh"
POL=$(ls -d "$(dirname "$0")"/../snapshot/* | tail -1)/policies.json
try() {
  printf '%-34s ' "$1"
  jq -c "$2" "$POL" | curl -s -X POST "$API/v1/policies/validate" -H "$H" -H "Content-Type: application/json" --data @- \
    | jq -c '{error, message, valid, ok} | with_entries(select(.value != null))' | cut -c1-300
}
try "A full policy object"            '.policies[0]'
try "B name+enabled+rules"            '.policies[0] | {name, enabled, rules}'
try "C rules document only"           '.policies[0].rules'
try "D {rules: [array]}"              '{rules: .policies[0].rules.rules}'
try "E bare rules array"              '.policies[0].rules.rules'
echo; echo "Top-level keys of the policies file:"; jq -c 'keys' "$POL"
