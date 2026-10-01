# Sourced by the other scripts. Needs CLIENT_ID and CLIENT_SECRET exported (or in ../.env).
if [ -z "${BASH_VERSION:-}" ]; then echo "Run the script directly (e.g. scripts/snapshot.sh); do not source it."; return 1 2>/dev/null || exit 1; fi
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${CLIENT_SECRET:-}" ] && [ -f "$HERE/../.env" ]; then set -a; . "$HERE/../.env"; set +a; fi
: "${CLIENT_ID:?export CLIENT_ID first}"; : "${CLIENT_SECRET:?export CLIENT_SECRET first}"
ID="${ZSAI_ID_HOST:-https://id.zsai.sqrx.io}"
API="${ZSAI_API_HOST:-https://use2.api.zsai.sqrx.io}"
TOKEN=$(curl -s -X POST "$ID/v1/auth/token" -u "$CLIENT_ID:$CLIENT_SECRET" | jq -r '.access_token // empty')
[ -n "$TOKEN" ] || { echo "Token failed. Check CLIENT_ID / CLIENT_SECRET."; exit 1; }
H="Authorization: Bearer $TOKEN"
