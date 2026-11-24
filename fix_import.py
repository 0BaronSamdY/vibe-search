with open('import_cities.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Уменьшаем радиус для больших городов
content = content.replace("('rome', 'Рим', 'Roma', 'Rome', 41.9028, 12.4964, 13, 8, true)", 
                          "('rome', 'Рим', 'Roma', 'Rome', 41.9028, 12.4964, 13, 5, true)")
content = content.replace("('milan', 'Милан', 'Milano', 'Milan', 45.4642, 9.1900, 13, 8, true)", 
                          "('milan', 'Милан', 'Milano', 'Milan', 45.4642, 9.1900, 13, 5, true)")
content = content.replace("('florence', 'Флоренция', 'Firenze', 'Florence', 43.7696, 11.2558, 14, 5, true)", 
                          "('florence', 'Флоренция', 'Firenze', 'Florence', 43.7696, 11.2558, 14, 4, true)")
print("✅ Радиус уменьшен")

# 2. Упрощаем запрос Overpass (только основные типы)
old_query = '''query = f"""
    [out:json][timeout:120];
    (
      node["amenity"="cafe"](around:{radius_m},{lat},{lng});
      node["amenity"="bar"](around:{radius_m},{lat},{lng});
      node["amenity"="pub"](around:{radius_m},{lat},{lng});
      node["amenity"="restaurant"](around:{radius_m},{lat},{lng});
      node["amenity"="fast_food"](around:{radius_m},{lat},{lng});
      node["amenity"="biergarten"](around:{radius_m},{lat},{lng});
      node["amenity"="cafe"]["cuisine"](around:{radius_m},{lat},{lng});
    );
    out body;
    """'''

new_query = '''query = f"""
    [out:json][timeout:180];
    (
      node["amenity"="cafe"](around:{radius_m},{lat},{lng});
      node["amenity"="bar"](around:{radius_m},{lat},{lng});
      node["amenity"="pub"](around:{radius_m},{lat},{lng});
      node["amenity"="restaurant"](around:{radius_m},{lat},{lng});
    );
    out body;
    """'''

if old_query in content:
    content = content.replace(old_query, new_query)
    print("✅ Запрос упрощён")
else:
    print("⚠️  Не нашёл запрос для замены")

# 3. Добавляем retry-логику
old_request = 'r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, headers={"User-Agent": "VibeSearch/1.0", "Accept": "application/json"}, timeout=180)'
new_request = '''for attempt in range(3):
        try:
            r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, headers={"User-Agent": "VibeSearch/1.0", "Accept": "application/json"}, timeout=180)
            r.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  ⚠️  Retry {attempt+1}/3: {e}")
            time.sleep(5)'''

if old_request in content:
    content = content.replace(old_request, new_request)
    print("✅ Retry-логика добавлена")

with open('import_cities.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🔧 Скрипт исправлен!")
