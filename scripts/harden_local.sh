#!/usr/bin/env bash
# Harden one tinytapeout/ project locally with LibreLane (Docker).
# Usage: harden_local.sh <project-dir-name>
# Example: harden_local.sh tt-uofa-vec-coproc
set -euo pipefail

NAME="${1:?usage: harden_local.sh <project-dir-name>}"
ROOT="/Users/jeffdi/Projects/nydesign"
if [[ -d "$ROOT/_uofa_ci2609_src/tinytapeout/$NAME" ]]; then
  SRC="$ROOT/_uofa_ci2609_src/tinytapeout/$NAME"
elif [[ -d "$ROOT/_uofa_ci2609_src/$NAME" ]]; then
  SRC="$ROOT/_uofa_ci2609_src/$NAME"
else
  echo "missing source: $NAME" >&2
  exit 1
fi
WORK="$ROOT/_tt_harden/$NAME"
CHIP="$ROOT/uofa-ci2609"
PY="$ROOT/nydesign-ci2605/.venv/bin/python"
# Nix LibreLane 3.0.0.dev38 already has OpenROAD/Yosys/Magic/KLayout.
# Docker is unavailable here (disk full / Desktop down), so harden natively.
NIX_LL="/nix/store/f4l1vwqhhrap56dpyzydhscqs6jx43xr-python3.12-librelane-3.0.0.dev38/bin"
SHIM="$ROOT/_tt_harden/bin"
mkdir -p "$SHIM"
cat > "$SHIM/python" <<EOF
#!/bin/bash
if [[ "\${1:-}" == "-m" && "\${2:-}" == "librelane" ]]; then
  shift 2
  exec "$NIX_LL/librelane" "\$@"
fi
exec "$PY" "\$@"
EOF
chmod +x "$SHIM/python"
export PATH="$SHIM:$ROOT/nydesign-ci2605/.venv/bin:$PATH"
export PDK_ROOT="${PDK_ROOT:-/Users/jeffdi/Projects/pdk}"
export PYTHONUNBUFFERED=1

if [[ ! -d "$SRC" ]]; then
  echo "missing source: $SRC" >&2
  exit 1
fi

rm -rf "$WORK"
mkdir -p "$WORK"
rsync -a --exclude .git "$SRC/" "$WORK/"
# Copy tt as a standalone git repo. A symlink to the chip submodule
# breaks GitPython: the submodule gitdir is a relative path.
rsync -a --exclude .git "$CHIP/tt/" "$WORK/tt/"
(
  cd "$WORK/tt"
  git init -q
  git add -A
  git -c user.email="jeffdi@chipfoundry.io" -c user.name="uofa-ci2609 harden" commit -q -m "tt-support-tools"
)

cd "$WORK"
git init -q
git add -A
git -c user.email="jeffdi@chipfoundry.io" -c user.name="uofa-ci2609 harden" commit -q -m "import $NAME"
git remote add origin "https://github.com/parsamrf/AI-HDL-Tape-out-Chipfoundry.git"

echo "=== create-user-config $NAME ==="
"$PY" tt/tt_tool.py --create-user-config

echo "=== harden $NAME (LibreLane nix, no docker) ==="
"$PY" tt/tt_tool.py --harden --no-docker

echo "=== create-tt-submission $NAME ==="
"$PY" tt/tt_tool.py --create-tt-submission

echo "=== copy into chip projects/ ==="
TOP="$("$PY" -c "import yaml; print(yaml.safe_load(open('info.yaml'))['project']['top_module'])")"
"$PY" "$CHIP/copy_hardened_project.py" -s . -n "$TOP" -p "$CHIP/projects"

echo "DONE $NAME"
