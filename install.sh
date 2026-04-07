#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || -z "${1:-}" ]]; then
  echo "Usage: ./install.sh <version>" >&2
  exit 1
fi

VERSION_VALUE="$1"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$REPO_ROOT/src/anki_statistics_extended"
MANIFEST_PATH="$SRC_DIR/manifest.json"
ARCHIVE_PATH="$REPO_ROOT/dist/anki_statistics_extended.ankiaddon"
INSTALL_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$INSTALL_DIR"
}

trap cleanup EXIT

if [[ ! -f "$MANIFEST_PATH" ]]; then
  echo "manifest.json not found at $MANIFEST_PATH" >&2
  exit 1
fi

PACKAGE_NAME="$(
  python3 -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["package"])' \
    "$MANIFEST_PATH"
)"

if [[ -n "${ANKI_ADDONS_DIR:-}" ]]; then
  ADDONS_DIR="$ANKI_ADDONS_DIR"
elif [[ -d "$HOME/Library/Application Support/Anki2/addons21" ]]; then
  ADDONS_DIR="$HOME/Library/Application Support/Anki2/addons21"
elif [[ -d "$HOME/.local/share/Anki2/addons21" ]]; then
  ADDONS_DIR="$HOME/.local/share/Anki2/addons21"
else
  echo "Could not find an Anki add-ons directory." >&2
  echo "Set ANKI_ADDONS_DIR to your addons21 path and rerun." >&2
  exit 1
fi

TARGET_DIR="$ADDONS_DIR/$PACKAGE_NAME"

"$REPO_ROOT/build.sh" "$VERSION_VALUE"

echo "Installing add-on into $TARGET_DIR"
mkdir -p "$TARGET_DIR"
unzip -oq "$ARCHIVE_PATH" -d "$INSTALL_DIR"

rsync -a --delete \
  --exclude "meta.json" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  "$INSTALL_DIR/" "$TARGET_DIR/"

echo "Install complete."
echo "Addon dir: $TARGET_DIR"
