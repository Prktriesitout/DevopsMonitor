#!/usr/bin/env bash
#
# scripts/simulate_traffic.sh — Traffic + chaos generator (Phase 14, Tasks 14.1.1-14.1.2).
#
# Generates continuous background HTTP traffic against the DevOps
# Monitoring application (/api/data) and, in chaos mode, fires
# concentrated bursts of /api/simulate-error requests sufficient to push
# the 5xx error rate above 5% sustained past the 2-minute
# HighHTTPErrorRate for-duration (docker/prometheus/alert_rules.yml).
#
# Localhost-only default — no credentials or external URLs:
#   http://localhost:8000 (overridable via positional arg or env).
#
# Usage:
#   ./scripts/simulate_traffic.sh [OPTIONS] [BASE_URL]
#
# Options:
#   --chaos              Enable chaos mode (concentrated /api/simulate-error bursts).
#   --mode normal|chaos  Select mode explicitly (MODE env var also honored).
#   --url BASE_URL       Base URL of the app (BASE_URL / SERVICE_URL env also honored).
#   --interval SECS      Delay between normal /api/data requests (default: 0.5).
#   --duration SECS      Auto-stop after SECS seconds (default: 0 = run until Ctrl-C).
#   -h, --help           Show this help and exit.
#
# Precedence for the base URL (first match wins):
#   1. Positional argument BASE_URL.
#   2. --url flag.
#   3. BASE_URL environment variable (SERVICE_URL fallback).
#   4. Default http://localhost:8000.
#
# Examples:
#   ./scripts/simulate_traffic.sh                       # normal traffic loop only
#   ./scripts/simulate_traffic.sh --chaos               # normal loop + chaos error bursts
#   ./scripts/simulate_traffic.sh --mode chaos          # same chaos mode via --mode
#   BASE_URL=http://localhost:8000 ./scripts/simulate_traffic.sh --chaos
#   ./scripts/simulate_traffic.sh --duration 300 --chaos
#
set -euo pipefail

DEFAULT_URL="http://localhost:8000"

BASE_URL="${BASE_URL:-${SERVICE_URL:-$DEFAULT_URL}}"
MODE="${MODE:-normal}"
CHAOS="${CHAOS:-0}"
INTERVAL="${INTERVAL:-0.5}"
DURATION="${DURATION:-0}"
POSITIONAL_URL=""

usage() {
  sed -n '2,/^set -euo pipefail$/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --chaos)
      CHAOS="1"
      MODE="chaos"
      shift
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --mode=*)
      MODE="${1#--mode=}"
      shift
      ;;
    --url)
      BASE_URL="${2:-}"
      shift 2
      ;;
    --url=*)
      BASE_URL="${1#--url=}"
      shift
      ;;
    --interval)
      INTERVAL="${2:-}"
      shift 2
      ;;
    --interval=*)
      INTERVAL="${1#--interval=}"
      shift
      ;;
    --duration)
      DURATION="${2:-}"
      shift 2
      ;;
    --duration=*)
      DURATION="${1#--duration=}"
      shift
      ;;
    --*)
      echo "[ERROR] Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      POSITIONAL_URL="$1"
      shift
      ;;
  esac
done

if [ -n "${POSITIONAL_URL}" ]; then
  BASE_URL="${POSITIONAL_URL}"
fi

if [ "${MODE}" = "chaos" ]; then
  CHAOS="1"
fi

if ! command -v curl > /dev/null 2>&1; then
  echo "[ERROR] curl is required but not installed" >&2
  exit 1
fi

if ! command -v seq > /dev/null 2>&1; then
  echo "[ERROR] seq (coreutils) is required but not installed" >&2
  exit 1
fi

echo "[INFO] Base URL: ${BASE_URL}"
echo "[INFO] Mode: ${MODE} (chaos=${CHAOS}), interval=${INTERVAL}s, duration=${DURATION}s"

# Track background loop PIDs so the EXIT/INT/TERM trap leaves no orphans.
PIDS=""

cleanup() {
  echo "[INFO] Stopping traffic generator; cleaning up background loops..."
  # shellcheck disable=SC2086
  if [ -n "${PIDS}" ]; then
    # shellcheck disable=SC2086
    for pid in ${PIDS}; do
      if kill -0 "${pid}" 2> /dev/null; then
        echo "[INFO] Terminating background loop pid=${pid}"
        kill "${pid}" 2> /dev/null || true
      fi
    done
    wait 2> /dev/null || true
  fi
  echo "[INFO] Traffic generator stopped"
}
trap cleanup INT TERM EXIT

# Normal background loop: curl /api/data continuously.
normal_loop() {
  echo "[INFO] Starting normal traffic loop -> ${BASE_URL}/api/data"
  while true; do
    if ! curl -sS --max-time 5 "${BASE_URL}/api/data" > /dev/null; then
      echo "[ERROR] Normal request failed: ${BASE_URL}/api/data unreachable or non-2xx"
    fi
    sleep "${INTERVAL}"
  done
}

# Chaos background loop: concentrated /api/simulate-error bursts.
# ~20 parallel 500-errors per cycle keeps the 5xx share far above the
# 5% HighHTTPErrorRate threshold for as long as chaos mode runs, so the
# 2-minute for-duration is satisfied while this loop is alive.
chaos_loop() {
  echo "[INFO] Starting chaos error-burst loop -> ${BASE_URL}/api/simulate-error"
  while true; do
    for _ in $(seq 1 20); do
      curl -sS --max-time 5 "${BASE_URL}/api/simulate-error" > /dev/null 2>&1 &
    done
    wait || true
    sleep 0.5
  done
}

normal_loop &
PIDS="${PIDS} $!"

if [ "${CHAOS}" = "1" ]; then
  echo "[INFO] Chaos mode enabled: firing concentrated /api/simulate-error bursts"
  chaos_loop &
  PIDS="${PIDS} $!"
else
  echo "[INFO] Chaos mode disabled: normal /api/data traffic only (pass --chaos to inject 500s)"
fi

if [ "${DURATION}" != "0" ] && [ "${DURATION}" != "" ]; then
  echo "[INFO] Running for ${DURATION}s, then exiting (trap will clean up loops)"
  sleep "${DURATION}"
  exit 0
fi

echo "[INFO] Traffic generator running (Ctrl-C to stop; trap cleans up background loops)"
wait
