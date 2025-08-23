import json
import os
import urllib.request

with open("dependencies.json") as f:
    deps = json.load(f)

for name, info in deps.items():
    url = info["url"].format(version=info["version"])
    dest = os.path.join("src/anki_statistics_extended", info["destination"])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Downloading {name}...")
    urllib.request.urlretrieve(url, dest)