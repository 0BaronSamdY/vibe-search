import requests
from config import SUPABASE_URL, SUPABASE_KEY, GEMINI_KEY
H = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY, "Content-Type": "application/json"}
base = {"name": "__test__", "address": "test", "latitude": 43.77, "longitude": 11.25, "place_type": "cafe", "city": "florence", "image_url": None}
vibe = {"noise_level": 0.5, "laptop_friendly": 0.5, "romantic": 0.5, "summary": "t", "summary_ru": "t", "summary_it": "t", "summary_en": "t"}

r = requests.post(SUPABASE_URL + "/rest/v1/places", json=base, headers=H)
print("A) place only:", r.status_code, r.text[:200])

p2 = dict(base); p2["name"] = "__test2__"; p2["vibe_attributes"] = vibe
r = requests.post(SUPABASE_URL + "/rest/v1/places", json=p2, headers=H)
print("B) vibe object:", r.status_code, r.text[:200])

p3 = dict(base); p3["name"] = "__test3__"; p3["vibe_attributes"] = [vibe]
r = requests.post(SUPABASE_URL + "/rest/v1/places", json=p3, headers=H)
print("C) vibe array:", r.status_code, r.text[:200])

requests.delete(SUPABASE_URL + "/rest/v1/places?name=like.__test*", headers=H)
print("test rows cleaned")

r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"key": GEMINI_KEY}, timeout=20)
print("GEMINI v1beta:", r.status_code)
if r.ok:
    print([m["name"] for m in r.json().get("models", []) if "flash" in m["name"]][:8])
else:
    print(r.text[:200])
    r = requests.get("https://generativelanguage.googleapis.com/v1/models", params={"key": GEMINI_KEY}, timeout=20)
    print("GEMINI v1:", r.status_code)
    if r.ok:
        print([m["name"] for m in r.json().get("models", []) if "flash" in m["name"]][:8])
    else:
        print(r.text[:200])
