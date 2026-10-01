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

# `aid` can exist from an older editable install (moved checkout). Reinstall
# unless aid_gui resolves inside this tree.
installed_src="$(
  python -c 'import aid_gui, pathlib; print(pathlib.Path(aid_gui.__file__).resolve().parents[1])' 2>/dev/null || true
)"
if [ "$installed_src" != "$PYTHON_DIR/src" ]; then
  pip install -e "$PYTHON_DIR"
fi

# pigeon/bin/qt6.conf points Qt at conda's Qt 6.7 plugins. pip PySide6 is 6.11,
# so xcb is rejected ("Could not find the Qt platform plugin xcb").
qt_plugins="$(
  python -c 'import PySide6, pathlib; print(pathlib.Path(PySide6.__file__).resolve().parent / "Qt" / "plugins")'
)"
export QT_PLUGIN_PATH="$qt_plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$qt_plugins/platforms"

exec aid "$@"
