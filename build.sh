#!/bin/bash
set -e

echo "🔧 Building Anki add-on package..."

# Create output directory
mkdir -p dist

# Download dependencies
echo "📥 Downloading dependencies..."
python download_deps.py

# Navigate to add-on source and zip contents
cd src/anki_statistics_extended
zip -r ../../dist/anki_statistics_extended.ankiaddon . -x "__pycache__/*"

echo "✅ Build completed: dist/anki_statistics_extended.ankiaddon"