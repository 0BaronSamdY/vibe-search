import re

with open('import_cities.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем заголовки для Overpass
old_request = 'r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=180)'
new_request = 'r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, headers={"User-Agent": "VibeSearch/1.0", "Accept": "application/json"}, timeout=180)'

if old_request in content:
    content = content.replace(old_request, new_request)
    print("✅ Overpass: добавлены заголовки")
else:
    print("⚠️  Не нашёл строку для замены")

with open('import_cities.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("🔧 Скрипт исправлен!")
