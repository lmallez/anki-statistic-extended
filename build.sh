#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLOTLY_PATH="$REPO_ROOT/src/anki_statistics_extended/web/plotly.min.js"
ARCHIVE_PATH="$REPO_ROOT/dist/anki_statistics_extended.ankiaddon"

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

# Navigate to add-on source and zip contents
cd "$REPO_ROOT/src/anki_statistics_extended"
rm -f "$ARCHIVE_PATH"
zip -r "$ARCHIVE_PATH" . -x "__pycache__/*" "*/__pycache__/*" "*.pyc"

echo "✅ Build completed: dist/anki_statistics_extended.ankiaddon"
