with open('import_nearby.py', 'r', encoding='utf-8') as f:
    src = f.read()

# 1. Новая функция overpass_query с 4 серверами
new_func = '''def overpass_query(lat, lng, radius_km):
    radius_m = radius_km * 1000
    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="cafe"](around:{radius_m},{lat},{lng});
      node["amenity"="bar"](around:{radius_m},{lat},{lng});
      node["amenity"="pub"](around:{radius_m},{lat},{lng});
      node["amenity"="restaurant"](around:{radius_m},{lat},{lng});
    );
    out body;
    """
    servers = [
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]
    headers = {"User-Agent": "VibeSearch/1.0", "Accept": "application/json"}
    last = None
    for url in servers:
        host = url.split("/")[2]
        try:
            print(f"  🌐 {host} ...")
            r = requests.post(url, data={"data": query}, headers=headers, timeout=90)
            r.raise_for_status()
            els = r.json().get("elements", [])
            print(f"  ✅ {host} OK")
            return els
        except Exception as e:
            last = e
            print(f"  ⚠️  {host}: {str(e)[:70]}")
            time.sleep(2)
    raise last

'''

start = src.index('def overpass_query')
end = src.index('def classify_place')
src = src[:start] + new_func + '\n' + src[end:]
print("✅ Overpass: 4 сервера с автопереключением")

# 2. Правильная метка города вместо "nearby"
src = src.replace('def import_nearby(lat, lng, radius_km=2, city_name="Nearby"):',
                  'def import_nearby(lat, lng, radius_km=2, city_name="Nearby", city_id="nearby"):')
src = src.replace('"city": "nearby",', '"city": city_id,')
print("✅ City: правильная метка города")

# 3. Дедупликация внутри города, а не глобально
src = src.replace('r = requests.get(f"{SUPABASE_URL}/rest/v1/places?select=id,name", headers=HEADERS)',
                  'r = requests.get(f"{SUPABASE_URL}/rest/v1/places?select=id,name&city=eq.{city_id}", headers=HEADERS)')
print("✅ Dedup: по городу")

# 4. Карта названий -> id города
src = src.replace('if __name__ == "__main__":',
                  'CITY_MAP = {"bologna":"bologna","firenze":"florence","florence":"florence","roma":"rome","rome":"rome","milano":"milan","milan":"milan"}\n\nif __name__ == "__main__":')
src = src.replace('import_nearby(lat, lng, radius, city_name)',
                  'import_nearby(lat, lng, radius, city_name, CITY_MAP.get(city_name.lower(), "nearby"))')
print("✅ CITY_MAP: Firenze->florence, Roma->rome, Milano->milan")

with open('import_nearby.py', 'w', encoding='utf-8') as f:
    f.write(src)

print("\n🔧 Готово! Запускай импорт.")
