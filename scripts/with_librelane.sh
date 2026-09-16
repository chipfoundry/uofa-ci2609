#!/usr/bin/env bash
# Run a command inside the Nix LibreLane 3.0.0.dev38 environment (EDA tools + Python).
# Usage: with_librelane.sh python build.py --skip-xor-checks
set -euo pipefail

NIX_LL="/nix/store/f4l1vwqhhrap56dpyzydhscqs6jx43xr-python3.12-librelane-3.0.0.dev38"
NIX_PY="/nix/store/v0vy1c59f0vf71h64caw17hzymvg0zms-python3-3.12.10/bin/python3.12"
WRAP="$NIX_LL/bin/librelane"
WRAPPED="$NIX_LL/bin/.librelane-wrapped"
ROOT="/Users/jeffdi/Projects/nydesign"
BIN="$ROOT/_tt_harden/bin"
mkdir -p "$BIN"
LL_PY="$BIN/ll_python.py"

# Collect EDA tool bins from the nix wrapper without eval (eval glues PATH entries).
EDA_PATH=$(grep -oE "/nix/store/[^']+/bin" "$WRAP" | awk '!seen[$0]++' | paste -sd: -)
export PATH="$EDA_PATH:${PATH:-/usr/bin:/bin}"
export PYTHONNOUSERSITE=true

if [[ ! -f "$LL_PY" ]]; then
  {
    head -n 3 "$WRAPPED"
    cat <<'PY'
import os
import runpy
import sys

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        raise SystemExit(0)
    if args[0] == "-m":
        mod = args[1]
        sys.argv = args[1:]
        runpy.run_module(mod, run_name="__main__", alter_sys=True)
    elif args[0] == "-c":
        sys.argv = args
        exec(compile(args[1], "<string>", "exec"), {"__name__": "__main__"})
    else:
        sys.argv = args
        sys.argv[0] = os.path.abspath(args[0])
        runpy.run_path(args[0], run_name="__main__")
PY
  } > "$LL_PY"
fi

if [[ "${1:-}" == "python" || "${1:-}" == "python3" || "${1:-}" == "python3.12" ]]; then
  shift
  exec "$NIX_PY" "$LL_PY" "$@"
fi
exec "$@"
