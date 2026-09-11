"""Hit local /ask for each golden question. Stdlib only."""
import json, pathlib, urllib.request

base = "http://localhost:8000"
qs = json.loads(pathlib.Path(__file__).with_name("golden_questions.json").read_text())
for item in qs:
    req = urllib.request.Request(f"{base}/ask", data=json.dumps({"query": item["q"], "lang": item.get("lang", "en"), "crop": "grape"}).encode(), headers={"Content-Type": "application/json"})
    print(urllib.request.urlopen(req).read().decode()[:500])
