#!/bin/bash
set -e

echo "🔧 Building Anki add-on package..."

# Create output directory
mkdir -p dist

# Navigate to add-on source and zip contents
cd src/anki_statistics_extended
zip -r ../../dist/anki_statistics_extended.ankiaddon . -x "__pycache__/*"

echo "✅ Build completed: dist/card_status_by_tag.ankiaddon"