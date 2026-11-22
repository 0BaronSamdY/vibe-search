import requests
import time
from config import SUPABASE_URL, SUPABASE_KEY

# Твои координаты
LAT = 44.7269
LON = 11.2892
RADIUS = 0.03  # примерно 3 км

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

print(f"Ищем кафе в районе ({LAT}, {LON})...")

query = f"""
[out:json][timeout:60];
(
  node["amenity"="cafe"]({LAT-RADIUS},{LON-RADIUS},{LAT+RADIUS},{LON+RADIUS});
  way["amenity"="cafe"]({LAT-RADIUS},{LON-RADIUS},{LAT+RADIUS},{LON+RADIUS});
);
out center;
"""

headers_overpass = {"User-Agent": "VibeSearchApp/1.0"}

data = None
for server in OVERPASS_SERVERS:
    print(f"Пробуем: {server}")
    try:
        response = requests.post(server, data={"data": query}, headers=headers_overpass, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print("✅ Успех!")
            break
        else:
            print(f"  Ошибка {response.status_code}")
    except Exception as e:
        print(f"  Сбой: {e}")
    time.sleep(2)

if not data:
    print("❌ Ни один сервер не ответил. Подожди 5 минут и повтори.")
    exit(1)

places = []
for element in data.get("elements", []):
    name = element.get("tags", {}).get("name")
    if not name:
        continue
    
    if "lat" in element and "lon" in element:
        lat, lon = element["lat"], element["lon"]
    elif "center" in element:
        lat, lon = element["center"]["lat"], element["center"]["lon"]
    else:
        continue
    
    addr = element.get("tags", {}).get("addr:street", "")
    house = element.get("tags", {}).get("addr:housenumber", "")
    
    places.append({
        "name": name,
        "category": "cafe",
        "address": f"{addr} {house}".strip(),
        "latitude": lat,
        "longitude": lon
    })

print(f"\nНайдено {len(places)} кафе. Добавляем в базу...")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

added = 0
errors = 0
for place in places:
    url = f"{SUPABASE_URL}/rest/v1/places"
    response = requests.post(url, json=place, headers=headers)
    
    if response.status_code in [200, 201, 204]:
        added += 1
    else:
        errors += 1
        if errors <= 3:
            print(f"  Ошибка {place['name']}: {response.status_code} - {response.text[:100]}")
    time.sleep(0.2)

print(f"\n✅ Готово! Добавлено: {added}, ошибок: {errors}")
