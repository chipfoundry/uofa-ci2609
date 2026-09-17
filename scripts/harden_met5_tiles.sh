#!/usr/bin/env bash
# Reharden the three imported tiles that shipped with met5.drawing.
set -u
ROOT="/Users/jeffdi/Projects/nydesign"
CHIP="$ROOT/uofa-ci2609"
HARDEN="$CHIP/scripts/harden_local.sh"
LOGDIR="$ROOT/_tt_harden"
SUMMARY="$LOGDIR/met5_reharden_summary.txt"

mkdir -p "$LOGDIR"
: > "$SUMMARY"

TILES=(
  uofa-traffic
  itims-spi
  necrl-aes128
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
