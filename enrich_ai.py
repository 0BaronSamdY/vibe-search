import json, math, re, sys, time
import requests
from config import SUPABASE_URL, SUPABASE_KEY, GEMINI_KEY

SB = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY, "Content-Type": "application/json"}
GBASE = "https://generativelanguage.googleapis.com/v1beta"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None

print("📥 Загружаем места…")
r = requests.get(SUPABASE_URL + "/rest/v1/places?select=id,name,address,latitude,longitude&order=id", headers=SB, timeout=30)
r.raise_for_status()
places = r.json()
if LIMIT: places = places[:LIMIT]
print(f"   Мест в работе: {len(places)}")

# --- OSM-теги: один запрос на все места ---
parts = []
for p in places:
    d = 0.0025
    bb = f"{p['latitude']-d},{p['longitude']-d},{p['latitude']+d},{p['longitude']+d}"
    parts.append(f'node["amenity"~"cafe|bar|restaurant"]({bb});way["amenity"~"cafe|bar|restaurant"]({bb});')
query = "[out:json][timeout:60];(" + "".join(parts) + ");out center tags;"

elements = []
for ep in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    try:
        r = requests.post(ep, data={"data": query}, headers={"User-Agent": "VibeSearch/1.0"}, timeout=90)
        if r.status_code == 200:
            elements = r.json().get("elements", [])
            break
    except Exception as e:
        print("   Overpass:", e)
print(f"🗺️  OSM-объектов рядом: {len(elements)}")

def dist(lat1, lon1, lat2, lon2):
    return math.hypot((lat1-lat2)*111320, (lon1-lon2)*111320*math.cos(math.radians(lat1)))

def norm(s): return re.sub(r"[^a-z0-9а-яё]+", " ", (s or "").lower()).strip()

def match_tags(p):
    best, best_score = {}, -1
    for el in elements:
        t = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None: continue
        d = dist(p["latitude"], p["longitude"], lat, lon)
        if d > 150: continue
        score = max(0, 150 - d)
        if norm(t.get("name")) == norm(p["name"]): score += 1000
        if score > best_score: best, best_score = t, score
    return best

# --- Выбор рабочей модели ---
def pick_model():
    names = []
    try:
        r = requests.get(GBASE + "/models", params={"key": GEMINI_KEY, "pageSize": 200}, timeout=30)
        r.raise_for_status()
        names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
        print(f"   Доступно моделей: {len(names)}")
    except Exception as e:
        print("   Список моделей недоступен:", e)
    prefs = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]
    order = [p for p in prefs if p in names]
    order += [n for n in names if n not in prefs and "flash" in n]
    order += [n for n in names if n not in order]
    if not order: order = prefs
    for m in order:
        try:
            r = requests.post(f"{GBASE}/models/{m}:generateContent", params={"key": GEMINI_KEY},
                              json={"contents": [{"parts": [{"text": "Reply with the single word OK"}]}]}, timeout=30)
            if r.status_code == 200:
                print(f"✅ Модель: {m}")
                return m
            print(f"   {m} → {r.status_code}")
        except Exception as e:
            print(f"   {m} → {e}")
    raise SystemExit("❌ Ни одна модель не ответила. Проверь GEMINI_KEY в config.py")

print("🤖 Подбираем модель…")
MODEL = pick_model()

SCHEMA = {"type": "OBJECT", "properties": {
    "noise_level": {"type": "NUMBER"}, "laptop_friendly": {"type": "NUMBER"}, "romantic": {"type": "NUMBER"},
    "confidence": {"type": "NUMBER"},
    "summary_ru": {"type": "STRING"}, "summary_it": {"type": "STRING"}, "summary_en": {"type": "STRING"}},
    "required": ["noise_level", "laptop_friendly", "romantic", "confidence", "summary_ru", "summary_it", "summary_en"]}

PROMPT = """You are a local guide scoring the vibe of a place for a discovery app in Italy.
Estimate three scores in [0,1], one decimal: noise_level (0 silent, 1 loud party), laptop_friendly (0 impossible, 1 ideal remote-work spot), romantic (0 utilitarian, 1 perfect date spot).
Use ONLY the evidence: name, address, OpenStreetMap tags. Signals: amenity type, outdoor_seating, smoking, internet_access, cuisine, opening_hours. A bar is louder than a tea room; wlan raises laptop_friendly; terrace and evening hours raise romantic. If a dimension has no evidence, stay near 0.5 but still differentiate from the other signals. NEVER invent concrete facts (no Wi-Fi, prices or hours unless present in tags).
confidence in [0,1]: how much evidence you had.
Write three summaries of the SAME place, 1-2 sentences, max 160 characters each, natural and specific: summary_ru in Russian, summary_it in Italian, summary_en in English. Mention real tags when present (terrace, Wi-Fi, cuisine); otherwise describe the likely atmosphere honestly.
Place: {name}
Address: {address}
OSM tags: {tags}
"""

def ask_ai(p, tags):
    body = {"contents": [{"parts": [{"text": PROMPT.format(
                name=p["name"], address=p.get("address") or "unknown",
                tags=json.dumps(tags, ensure_ascii=False))}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json", "responseSchema": SCHEMA}}
    for attempt in range(4):
        try:
            r = requests.post(f"{GBASE}/models/{MODEL}:generateContent", params={"key": GEMINI_KEY}, json=body, timeout=60)
            if r.status_code == 200:
                txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(txt)
            if r.status_code in (429, 500, 503):
                wait = 12 * (attempt + 1)
                print(f"   ⏳ {r.status_code}, пауза {wait}с…")
                time.sleep(wait)
                continue
            print(f"   ❌ HTTP {r.status_code}: {r.text[:160]}")
            return None
        except Exception as e:
            print(f"   ⏳ {e}")
            time.sleep(8)
    return None

def clamp(x): return round(min(1.0, max(0.0, float(x))), 1)

def save(pid, d):
    payload = {"place_id": pid,
               "noise_level": clamp(d["noise_level"]), "laptop_friendly": clamp(d["laptop_friendly"]),
               "romantic": clamp(d["romantic"]), "confidence": clamp(d.get("confidence", 0.5)),
               "summary": d["summary_ru"], "summary_ru": d["summary_ru"],
               "summary_it": d["summary_it"], "summary_en": d["summary_en"], "ai_model": MODEL}
    r = requests.post(SUPABASE_URL + "/rest/v1/vibe_attributes?on_conflict=place_id", json=payload,
                      headers={**SB, "Prefer": "resolution=merge-duplicates,return=minimal"}, timeout=30)
    if r.status_code in (200, 201, 204): return True
    requests.delete(SUPABASE_URL + f"/rest/v1/vibe_attributes?place_id=eq.{pid}", headers=SB, timeout=30)
    r = requests.post(SUPABASE_URL + "/rest/v1/vibe_attributes", json=payload,
                      headers={**SB, "Prefer": "return=minimal"}, timeout=30)
    return r.status_code in (200, 201, 204)

def backfill_address(p, tags):
    if p.get("address"): return
    street = tags.get("addr:street")
    if street:
        addr = (street + " " + tags.get("addr:housenumber", "")).strip()
        requests.patch(SUPABASE_URL + f"/rest/v1/places?id=eq.{p['id']}", json={"address": addr},
                       headers={**SB, "Prefer": "return=minimal"}, timeout=30)

ok = fail = 0
for i, p in enumerate(places, 1):
    print(f"\n[{i}/{len(places)}] {p['name']}")
    tags = match_tags(p)
    print(f"   OSM-тегов: {len(tags)}")
    d = ask_ai(p, tags)
    if not d:
        fail += 1
        continue
    if save(p["id"], d):
        backfill_address(p, tags)
        ok += 1
        print(f"   ✅ шум={clamp(d['noise_level'])} работа={clamp(d['laptop_friendly'])} романтика={clamp(d['romantic'])} conf={clamp(d.get('confidence',0.5))}")
        print(f"   🇮🇹 {d['summary_it'][:90]}")
    else:
        fail += 1
        print("   ❌ Ошибка сохранения")
    time.sleep(6)

print("\n" + "=" * 50)
print(f"✅ Готово: {ok} обогащено, {fail} ошибок. Модель: {MODEL}")
