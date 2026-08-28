#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$ROOT/Python"
PIGEON="${PIGEON_ENV:-$HOME/anaconda/envs/pigeon}"

if [ ! -x "$PIGEON/bin/python" ]; then
  echo "conda env 'pigeon' not found at $PIGEON" >&2
  exit 1
fi

export PATH="$PIGEON/bin:$PATH"

if ! command -v aid >/dev/null 2>&1; then
  pip install -e "$PYTHON_DIR"
fi

exec aid "$@"
