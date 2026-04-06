#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLOTLY_PATH="$REPO_ROOT/src/anki_statistics_extended/web/plotly.min.js"
ARCHIVE_PATH="$REPO_ROOT/dist/anki_statistics_extended.ankiaddon"
BUILD_DIR="$(mktemp -d)"
DEFAULT_VERSION="$(
  python3 -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' \
    "$REPO_ROOT/src/anki_statistics_extended/manifest.json"
)"

RAW_VERSION="${VERSION:-$DEFAULT_VERSION}"
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

# Build from a temporary copy so the placeholder version is always resolved.
cp -R "$REPO_ROOT/src/anki_statistics_extended/." "$BUILD_DIR/"
python3 - "$BUILD_DIR/manifest.json" "$VERSION_VALUE" "$MOD_VALUE" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = sys.argv[2]
manifest["mod"] = int(sys.argv[3])
manifest_path.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
PY

echo "Version: $VERSION_VALUE"

cd "$BUILD_DIR"
rm -f "$ARCHIVE_PATH"
zip -r "$ARCHIVE_PATH" . -x "__pycache__/*" "*/__pycache__/*" "*.pyc"

echo "✅ Build completed: dist/anki_statistics_extended.ankiaddon"
