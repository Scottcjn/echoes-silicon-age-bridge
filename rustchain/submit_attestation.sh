#!/usr/bin/env bash
set -euo pipefail

NODE_URL="${1:-http://50.28.86.131:8099}"
PAYLOAD="${2:-rustchain/attest_payload.sample.json}"
OUT="${3:-rustchain/attest_response.json}"

curl -sS -X POST "$NODE_URL/attest/submit" \
  -H "Content-Type: application/json" \
  --data @"$PAYLOAD" > "$OUT"

echo "Wrote response to $OUT"
