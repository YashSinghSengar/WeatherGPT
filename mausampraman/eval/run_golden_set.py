"""Golden set: /ask items via HTTP, target_date items via get_divergence_scenario."""
import json, pathlib, sys, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

base = "http://localhost:8000"
qs = json.loads(pathlib.Path(__file__).with_name("golden_questions.json").read_text())
for item in qs:
    if item.get("target_date"):
        from data.geocoder import geocode
        from data.openmeteo_client import get_divergence_scenario, prevruns_per_model
        from confidence.engine import grade, model_spread

        lat, lon = geocode(item.get("location", "Nashik"))
        scen = get_divergence_scenario(lat, lon, item["target_date"])
        per = prevruns_per_model(lat, lon, item["target_date"])
        g = grade(per, None, 30, 2)
        print(item["target_date"], "spread=", round(model_spread(per), 1), "grade=", g["grade"], "scenario_precip=", scen["precip_mm"])
        continue
    body = {"query": item["q"], "lang": item.get("lang", "en"), "crop": "grape"}
    if item.get("stage"):
        body["stage"] = item["stage"]
    try:
        req = urllib.request.Request(f"{base}/ask", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        print(item.get("class"), "->", urllib.request.urlopen(req).read().decode()[:300], flush=True)
    except urllib.error.HTTPError as e:
        print(item.get("class"), "-> HTTP", e.code, item["q"][:60], flush=True)
