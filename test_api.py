import requests
from config import SUPABASE_URL, SUPABASE_KEY

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Запрос: все места с их атрибутами (если есть)
url = f"{SUPABASE_URL}/rest/v1/places?select=name,category,address,vibe_attributes(noise_level,laptop_friendly,romantic,summary)"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"Всего мест в базе: {len(data)}\n")
    
    with_vibe = 0
    without_vibe = 0
    
    for place in data:
        vibes = place.get('vibe_attributes') or []
        if vibes:
            with_vibe += 1
            vibe = vibes[0]
            print(f"✅ {place['name']} ({place['category']})")
            print(f"   📍 {place.get('address', 'адрес неизвестен')}")
            print(f"   🔊 Шум: {vibe.get('noise_level')}")
            print(f"   💻 Для работы: {vibe.get('laptop_friendly')}")
            print(f"   💕 Романтично: {vibe.get('romantic')}")
            print(f"   📝 {vibe.get('summary', '')}")
            print()
        else:
            without_vibe += 1
            print(f"⚪ {place['name']} ({place['category']})")
            print(f"   📍 {place.get('address', 'адрес неизвестен')}")
            print(f"   (настроение ещё не заполнено)")
            print()
    
    print(f"---")
    print(f"С настроением: {with_vibe}")
    print(f"Без настроения: {without_vibe}")
else:
    print(f"Ошибка: {response.status_code}")
    print(response.text)
