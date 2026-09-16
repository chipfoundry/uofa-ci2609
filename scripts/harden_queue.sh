#!/usr/bin/env bash
# Sequential harden of remaining UofA tiles. Skips GEMM.
# Waits for an in-flight canary PID if given as $1.
set -u

ROOT="/Users/jeffdi/Projects/nydesign"
CHIP="$ROOT/uofa-ci2609"
PY="$ROOT/nydesign-ci2605/.venv/bin/python"
HARDEN="$CHIP/scripts/harden_local.sh"
LOGDIR="$ROOT/_tt_harden"
CANARY_PID="${1:-}"
SUMMARY="$LOGDIR/queue_summary.txt"

mkdir -p "$LOGDIR"
: > "$SUMMARY"

finish_canary() {
  local work="$LOGDIR/tt-uofa-vec-coproc"
  echo "=== finish canary tt-uofa-vec-coproc ==="
  if [[ ! -d "$work/runs/wokwi/final" ]]; then
    echo "FAIL tt-uofa-vec-coproc (no final views)" | tee -a "$SUMMARY"
    return 1
  fi
  export PATH="$LOGDIR/bin:$ROOT/nydesign-ci2605/.venv/bin:$PATH"
  export PDK_ROOT="${PDK_ROOT:-/Users/jeffdi/Projects/pdk}"
  export PYTHONUNBUFFERED=1
  (
    cd "$work"
    "$PY" tt/tt_tool.py --create-tt-submission
    "$PY" "$CHIP/copy_hardened_project.py" -s . -p "$CHIP/projects"
  )
  echo "PASS tt-uofa-vec-coproc" | tee -a "$SUMMARY"
}

if [[ -n "$CANARY_PID" ]]; then
  echo "waiting for canary pid $CANARY_PID..."
  while kill -0 "$CANARY_PID" 2>/dev/null; do
    sleep 15
  done
  echo "canary pid $CANARY_PID exited"
  finish_canary || echo "canary post-steps failed" | tee -a "$SUMMARY"
fi

TILES=(
  tt-uofa-bmi
  tt-uofa-bmu
  tt-uofa-mul
  tt-uofa-gpio
  tt-uofa-bp
  tt-uofa-vec-proc
)

for name in "${TILES[@]}"; do
  echo "========== $name =========="
  if "$HARDEN" "$name" > "$LOGDIR/${name}.log" 2>&1; then
    echo "PASS $name" | tee -a "$SUMMARY"
  else
    echo "FAIL $name (see $LOGDIR/${name}.log)" | tee -a "$SUMMARY"
  fi
done

echo "========== queue done =========="
cat "$SUMMARY"
