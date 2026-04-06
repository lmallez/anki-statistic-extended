#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLOTLY_PATH="$REPO_ROOT/src/anki_statistics_extended/web/plotly.min.js"
ARCHIVE_PATH="$REPO_ROOT/dist/anki_statistics_extended.ankiaddon"
BUILD_DIR="$(mktemp -d)"
RAW_VERSION="${VERSION:-dev}"
VERSION_VALUE="${RAW_VERSION#v}"

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

# Build from a temporary copy so the placeholder version is always resolved.
cp -R "$REPO_ROOT/src/anki_statistics_extended/." "$BUILD_DIR/"
python3 - "$BUILD_DIR/manifest.json" "$VERSION_VALUE" <<'PY'
from pathlib import Path
import sys

manifest_path = Path(sys.argv[1])
manifest_path.write_text(
    manifest_path.read_text().replace("${VERSION}", sys.argv[2])
)
PY

echo "Version: $VERSION_VALUE"

cd "$BUILD_DIR"
rm -f "$ARCHIVE_PATH"
zip -r "$ARCHIVE_PATH" . -x "__pycache__/*" "*/__pycache__/*" "*.pyc"

echo "✅ Build completed: dist/anki_statistics_extended.ankiaddon"
