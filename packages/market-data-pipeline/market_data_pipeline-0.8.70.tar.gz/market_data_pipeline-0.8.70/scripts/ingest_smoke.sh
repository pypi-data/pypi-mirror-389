#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8083}"  # pipeline API
echo "[ingest_smoke] Base: $BASE"

echo "1) Status (before):"
curl -sS "$BASE/runtime/ingest/status" | jq .

echo "2) Start synthetic (dry-run=true, 15s):"
curl -sS -X POST "$BASE/runtime/ingest/reload" -H "Content-Type: application/json" -d '{}' | jq .
curl -sS -X POST "$BASE/runtime/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{"provider":"synthetic","dry_run": true, "override_params":{"ticks_per_sec":5}}' | jq .

echo "3) Status (running):"
curl -sS "$BASE/runtime/ingest/status" | jq .

echo "4) Stop:"
curl -sS -X POST "$BASE/runtime/ingest/stop" -H "Content-Type: application/json" -d '{}' | jq .

echo "5) Status (after stop):"
curl -sS "$BASE/runtime/ingest/status" | jq .

echo "[ingest_smoke] Done."
