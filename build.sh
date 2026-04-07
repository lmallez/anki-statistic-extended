#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || -z "${1:-}" ]]; then
  echo "Usage: ./build.sh <version>" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLOTLY_PATH="$REPO_ROOT/src/anki_statistics_extended/web/plotly.min.js"
ARCHIVE_PATH="$REPO_ROOT/dist/anki_statistics_extended.ankiaddon"
BUILD_DIR="$(mktemp -d)"
RAW_VERSION="$1"
VERSION_VALUE="${RAW_VERSION#v}"
MOD_VALUE="$(date -u +%s)"

cleanup() {
  rm -rf "$BUILD_DIR"
}

trap cleanup EXIT

echo "🔧 Building Anki add-on package..."

if [[ ! "$VERSION_VALUE" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9]+)*$ ]]; then
  echo "Invalid version: $RAW_VERSION" >&2
  exit 1
fi

# Create output directory
mkdir -p "$REPO_ROOT/dist"

# Download dependencies
if [[ -f "$PLOTLY_PATH" ]]; then
  echo "📦 Using checked-in Plotly bundle..."
else
  echo "📥 Downloading dependencies..."
  python3 "$REPO_ROOT/download_deps.py"
fi

# Build from a temporary copy so the manifest placeholders are always resolved.
cp -R "$REPO_ROOT/src/anki_statistics_extended/." "$BUILD_DIR/"
python3 - "$BUILD_DIR/manifest.json" "$VERSION_VALUE" "$MOD_VALUE" <<'PY'
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
manifest_text = manifest_path.read_text(encoding="utf-8")
manifest_text = manifest_text.replace("${VERSION}", sys.argv[2])
manifest_text = manifest_text.replace('"${MOD}"', sys.argv[3])
manifest_path.write_text(manifest_text, encoding="utf-8")
PY

echo "Version: $VERSION_VALUE"

cd "$BUILD_DIR"
rm -f "$ARCHIVE_PATH"
zip -r "$ARCHIVE_PATH" . -x "__pycache__/*" "*/__pycache__/*" "*.pyc"

echo "✅ Build completed: dist/anki_statistics_extended.ankiaddon"
