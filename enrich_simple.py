import requests
import time
from config import SUPABASE_URL, SUPABASE_KEY

print("📥 Загружаем места из базы...")
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/places?select=id,name,address,latitude,longitude",
    headers=headers
)
places = response.json()
print(f"   Найдено {len(places)} мест")

def get_osm_tags(lat, lon, radius=0.001):
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"="cafe"]({lat-radius},{lon-radius},{lat+radius},{lon+radius});
      way["amenity"="cafe"]({lat-radius},{lon-radius},{lat+radius},{lon+radius});
    );
    out tags;
    """
    try:
        r = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            headers={"User-Agent": "VibeSearch/1.0"},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                el_lat = el.get("lat", el.get("center", {}).get("lat", 0))
                el_lon = el.get("lon", el.get("center", {}).get("lon", 0))
                if abs(el_lat - lat) < 0.0005 and abs(el_lon - lon) < 0.0005:
                    return tags
    except:
        pass
    return {}

def analyze_by_rules(tags):
    noise = 0.5
    laptop = 0.5
    romantic = 0.5
    summary_parts = []
    
    outdoor = tags.get("outdoor_seating", "")
    smoking = tags.get("smoking", "")
    
    if outdoor in ["yes", "separate"]:
        noise = 0.7
        summary_parts.append("есть летняя терраса")
    if smoking in ["yes", "outside"]:
        noise = max(noise, 0.6)
        summary_parts.append("разрешено курение")
    
    wifi = tags.get("internet_access", "")
    wlan = tags.get("internet_access:wlan", "")
    cuisine = tags.get("cuisine", "").lower()
    
    if wifi in ["wlan", "yes"] or wlan == "yes":
        laptop = 0.8
        summary_parts.append("есть Wi-Fi")
    elif wifi == "no":
        laptop = 0.2
        summary_parts.append("нет интернета")
    
    if "pizza" in cuisine or "fast_food" in cuisine:
        laptop = min(laptop, 0.4)
        summary_parts.append("быстрое питание")
    elif "regional" in cuisine or "italian" in cuisine:
        laptop = max(laptop, 0.6)
        summary_parts.append("итальянская кухня")
    
    if outdoor in ["yes", "separate"] and smoking in ["no", "isolated"]:
        romantic = 0.7
        summary_parts.append("уютная терраса")
    if "bar" in tags.get("name", "").lower():
        romantic = min(romantic, 0.4)
    
    if not summary_parts:
        summary_parts.append("стандартное кафе")
    
    summary = f"Кафе, {', '.join(summary_parts[:3])}."
    
    return {
        "noise_level": round(noise, 1),
        "laptop_friendly": round(laptop, 1),
        "romantic": round(romantic, 1),
        "summary": summary
    }

print("\n📊 Анализируем по правилам...")

success = 0
failed = 0

for place in places:
    print(f"\n   Анализирую: {place['name']}...")
    tags = get_osm_tags(place["latitude"], place["longitude"])
    result = analyze_by_rules(tags)
    
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/vibe_attributes?place_id=eq.{place['id']}",
        headers=headers
    )
    
    data = {
        "place_id": place["id"],
        **result
    }
    
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/vibe_attributes",
        json=data,
        headers={**headers, "Prefer": "return=minimal"}
    )
    
    if r.status_code in [200, 201, 204]:
        print(f"   ✅ {place['name']}: шум={result['noise_level']}, работа={result['laptop_friendly']}, романтика={result['romantic']}")
        print(f"      📝 {result['summary']}")
        success += 1
    else:
        print(f"   ❌ Ошибка сохранения: {r.status_code}")
        failed += 1
    
    time.sleep(0.5)

print(f"\n{'='*50}")
print(f"✅ Готово! Обработано: {success}, ошибок: {failed}")
print(f"Запусти python test_api.py чтобы увидеть результат")
