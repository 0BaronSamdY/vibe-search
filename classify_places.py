import re
import requests
from config import SUPABASE_URL, SUPABASE_KEY

SB = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY, "Content-Type": "application/json"}

print("📥 Загружаем все места из базы…")
r = requests.get(SUPABASE_URL + "/rest/v1/places?select=id,name,place_type&order=id", headers=SB, timeout=30)
r.raise_for_status()
places = r.json()
print(f"   Всего мест: {len(places)}")

# Ключевые слова для классификации
BAR_WORDS = re.compile(r'\b(bar|pub|birra|cocktail|lounge|club|discoteca|enoteca|wine|drink|aperitivo)\b', re.I)
RESTAURANT_WORDS = re.compile(r'\b(ristorante|restaurant|trattoria|osteria|pizzeria|pizzaria|rosticceria|tavola|mensa|cucina|food|eatery|bistrot|bistro)\b', re.I)

updated = 0
skipped = 0

for p in places:
    name = p.get('name', '') or ''
    current_type = p.get('place_type')
    
    # Определяем тип по имени
    if BAR_WORDS.search(name):
        new_type = 'bar'
    elif RESTAURANT_WORDS.search(name):
        new_type = 'restaurant'
    else:
        new_type = 'cafe'
    
    # Обновляем только если тип изменился или отсутствует
    if current_type != new_type:
        r = requests.patch(
            SUPABASE_URL + f"/rest/v1/places?id=eq.{p['id']}",
            json={"place_type": new_type},
            headers={**SB, "Prefer": "return=minimal"},
            timeout=15
        )
        if r.status_code in (200, 201, 204):
            updated += 1
            print(f"   ✅ [{new_type}] {name}")
        else:
            print(f"   ❌ {name} — {r.status_code}")
    else:
        skipped += 1

print("\n" + "=" * 50)
print(f"✅ Обновлено: {updated}")
print(f"⏭️  Без изменений: {skipped}")

# Статистика
stats = {"cafe": 0, "bar": 0, "restaurant": 0}
for p in places:
    t = p.get('place_type', 'cafe')
    if t in stats:
        stats[t] += 1
    else:
        stats['cafe'] += 1
print(f"\n📊 Итого: кафе={stats['cafe']}, бары={stats['bar']}, рестораны={stats['restaurant']}")
