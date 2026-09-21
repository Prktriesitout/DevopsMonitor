#!/usr/bin/env bash
#
# scripts/health_check.sh — Synthetic health probe guard (Phase 13, Task 13.2.1).
#
# Probes GET <service>/api/health exactly 10 times and exits 0 only if all
# 10 probes succeed (HTTP 200 via curl -f); exits non-zero otherwise so the
# Jenkins Verify/Rollback stage can trigger `kubectl rollout undo`.
#
# Usage:
#   ./scripts/health_check.sh [SERVICE_URL]
#   SERVICE_URL=http://localhost:8000 ./scripts/health_check.sh
#
# Target resolution (first match wins):
#   1. Positional argument $1 (e.g. http://localhost:8000 for local override).
#   2. SERVICE_URL environment variable.
#   3. Default in-cluster service address http://devops-monitored-app-service:8000.
set -euo pipefail

SERVICE_URL="${1:-${SERVICE_URL:-http://devops-monitored-app-service:8000}}"
HEALTH_ENDPOINT="${SERVICE_URL}/api/health"

echo "[INFO] Starting synthetic health verification against ${HEALTH_ENDPOINT} (10 attempts)"

PASS_COUNT=0

for i in $(seq 1 10); do
  if curl -f -sS --max-time 5 "${HEALTH_ENDPOINT}" > /dev/null; then
    PASS_COUNT=$((PASS_COUNT + 1))
    echo "[INFO] Health check ${i}/10 passed (${HEALTH_ENDPOINT} -> 200 OK)"
  else
    echo "[ERROR] Health check ${i}/10 failed (${HEALTH_ENDPOINT} unreachable or non-200)"
  fi
  if [ "${i}" -lt 10 ]; then
    sleep 3
  fi
done

if [ "${PASS_COUNT}" -eq 10 ]; then
  echo "[INFO] Health verification SUCCEEDED — all 10/10 probes returned 200 OK"
  exit 0
else
  echo "[ERROR] Health verification FAILED — ${PASS_COUNT}/10 probes passed; rollback required"
  exit 1
fi
