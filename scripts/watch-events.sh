#!/usr/bin/env bash
# READ-ONLY. Shows the latest agent events. Handy on a second screen during the demo.
# Usage: scripts/watch-events.sh [verdict]     e.g. scripts/watch-events.sh block
. "$(dirname "$0")/_auth.sh"
V="${1:-}"; Q="days=1&limit=10"; [ -n "$V" ] && Q="$Q&ef_verdict=$V"
curl -s "$API/v1/events?$Q" -H "$H" | jq -r '(.events // .items // .data // [])[] | [(.time // .ts // .created_at // ""), (.user // ""), (.tool // ""), (.verdict // "-"), ((.summary // .command // .reason // "") | tostring | .[0:70])] | @tsv'
