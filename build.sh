#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLOTLY_PATH="$REPO_ROOT/src/anki_statistics_extended/web/plotly.min.js"
ARCHIVE_PATH="$REPO_ROOT/dist/anki_statistics_extended.ankiaddon"
BUILD_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$BUILD_DIR"
}

trap cleanup EXIT

echo "🔧 Building Anki add-on package..."

# Create output directory
mkdir -p "$REPO_ROOT/dist"

# Download dependencies
if [[ -f "$PLOTLY_PATH" ]]; then
  echo "📦 Using checked-in Plotly bundle..."
else
  echo "📥 Downloading dependencies..."
  python3 "$REPO_ROOT/download_deps.py"
fi

# Build from a temporary copy so CI can override the manifest version safely.
cp -R "$REPO_ROOT/src/anki_statistics_extended/." "$BUILD_DIR/"

if [[ -n "${ANKI_ADDON_VERSION:-}" ]]; then
  echo "🏷️ Setting manifest version to $ANKI_ADDON_VERSION..."
  python3 - "$BUILD_DIR/manifest.json" "$ANKI_ADDON_VERSION" <<'PY'
import json
import pathlib
import sys

manifest_path = pathlib.Path(sys.argv[1])
version = sys.argv[2]

manifest = json.loads(manifest_path.read_text())
manifest["version"] = version
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
PY
fi

cd "$BUILD_DIR"
rm -f "$ARCHIVE_PATH"
zip -r "$ARCHIVE_PATH" . -x "__pycache__/*" "*/__pycache__/*" "*.pyc"

echo "✅ Build completed: dist/anki_statistics_extended.ankiaddon"
