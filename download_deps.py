from __future__ import annotations

import json
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

with (REPO_ROOT / "dependencies.json").open(encoding="utf-8") as handle:
    deps = json.load(handle)

for name, info in deps.items():
    url = info["url"].format(version=info["version"])
    dest = REPO_ROOT / "src" / "anki_statistics_extended" / info["destination"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {name}...")
    urllib.request.urlretrieve(url, dest)
