#!/usr/bin/env bash
# DRY RUN ONLY: POST /v1/policies/validate checks a policy without saving it.
# Usage: scripts/validate-policy.sh policies/lab-baseline.json
. "$(dirname "$0")/_auth.sh"
FILE="${1:?usage: $0 policy.json}"
curl -s -X POST "$API/v1/policies/validate" -H "$H" -H "Content-Type: application/json" \
  --data @"$FILE" | jq '{valid, errors, error, request_id} | with_entries(select(.value != null))'
