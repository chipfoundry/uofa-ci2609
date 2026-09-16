#!/usr/bin/env bash
# Sequential harden of SLM tiles. Skips GEMM.
set -u

ROOT="/Users/jeffdi/Projects/nydesign"
CHIP="$ROOT/uofa-ci2609"
HARDEN="$CHIP/scripts/harden_local.sh"
LOGDIR="$ROOT/_tt_harden"
SUMMARY="$LOGDIR/slm_queue_summary.txt"

mkdir -p "$LOGDIR"
: > "$SUMMARY"

TILES=(
  tt-slm-dma
  tt-slm-kv
  tt-slm-softmax
  tt-slm-rmsnorm
  tt-slm-cpu
)

for name in "${TILES[@]}"; do
  echo "========== $name =========="
  if "$HARDEN" "$name" > "$LOGDIR/${name}.log" 2>&1; then
    echo "PASS $name" | tee -a "$SUMMARY"
  else
    echo "FAIL $name (see $LOGDIR/${name}.log)" | tee -a "$SUMMARY"
  fi
done

echo "========== slm queue done =========="
cat "$SUMMARY"
