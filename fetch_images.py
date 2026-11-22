import re, time, requests
from config import SUPABASE_URL, SUPABASE_KEY

SB = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY, "Content-Type": "application/json"}

print("📥 Загружаем места…")
r = requests.get(SUPABASE_URL + "/rest/v1/places?select=id,name,address&order=id", headers=SB, timeout=30)
r.raise_for_status()
places = r.json()
print(f"   Мест: {len(places)}")

def clean_name(name):
    return re.sub(r'[^\w\s]', '', name).strip()

def search_wikipedia(name):
    """Ищем фото через Wikipedia REST API"""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(name)}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if 'thumbnail' in data:
                return data['thumbnail']['source']
    except:
        pass
    return None

def search_commons_direct(name):
    """Прямой поиск файлов на Wikimedia Commons"""
    # Ищем файлы с именем места
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "allimages",
        "aiprefix": name[:3] if len(name) >= 3 else name,
        "ailimit": 50,
        "aifilterbots": "all",
        "format": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            images = r.json().get("query", {}).get("allimages", [])
            for img in images:
                title = img["title"]
                if name.lower() in title.lower():
                    return get_thumb_url(title)
    except:
        pass
    return None

def search_commons_search(name):
    """Поиск через API поиска Commons"""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"file:{name} Bologna",
        "gsrnamespace": 6,
        "gsrlimit": 5,
        "prop": "imageinfo",
        "iiprop": "thumburl",
        "iiurlwidth": 400,
        "format": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for page in pages.values():
                if "imageinfo" in page:
                    return page["imageinfo"][0]["thumburl"]
    except:
        pass
    return None

def search_by_street(street):
    """Ищем фото улицы"""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"file:{street} Bologna",
        "gsrnamespace": 6,
        "gsrlimit": 3,
        "prop": "imageinfo",
        "iiprop": "thumburl",
        "iiurlwidth": 400,
        "format": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for page in pages.values():
                if "imageinfo" in page:
                    return page["imageinfo"][0]["thumburl"]
    except:
        pass
    return None

def get_thumb_url(title):
    """Получаем thumbnail URL по названию файла"""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "thumburl",
        "iiurlwidth": 400,
        "format": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for page in pages.values():
                if "imageinfo" in page:
                    return page["imageinfo"][0]["thumburl"]
    except:
        pass
    return None

def fallback_generic():
    """Если ничего не нашли — берём общее фото Болоньи"""
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Bologna_-_Piazza_Maggiore_%282%29.jpg/400px-Bologna_-_Piazza_Maggiore_%282%29.jpg"

ok = skip = fail = 0
for i, p in enumerate(places, 1):
    print(f"\n[{i}/{len(places)}] {p['name']}")
    
    if p.get("image_url"):
        print("   ⏭️  Уже есть фото")
        skip += 1
        continue
    
    name = clean_name(p["name"])
    img_url = None
    
    # 1. Пробуем Wikipedia
    print(f"   🔍 Wikipedia: {name}")
    img_url = search_wikipedia(name)
    if img_url:
        print(f"   ✅ Найдено в Wikipedia")
    
    # 2. Прямой поиск файлов на Commons
    if not img_url:
        print(f"   🔍 Commons direct: {name}")
        img_url = search_commons_direct(name)
        if img_url:
            print(f"   ✅ Найдено в Commons (direct)")
    
    # 3. Поиск через generator=search
    if not img_url:
        print(f"   🔍 Commons search: {name}")
        img_url = search_commons_search(name)
        if img_url:
            print(f"   ✅ Найдено в Commons (search)")
    
    # 4. Fallback на улицу
    if not img_url and p.get("address"):
        street = p["address"].split(",")[0].strip()
        print(f"   🔍 Street: {street}")
        img_url = search_by_street(street)
        if img_url:
            print(f"   ✅ Найдено фото улицы")
    
    # 5. Общий fallback
    if not img_url:
        print(f"   🔍 Generic fallback")
        img_url = fallback_generic()
        if img_url:
            print(f"   ✅ Использовано общее фото Болоньи")
    
    if img_url:
        # Сохраняем в БД
        r = requests.patch(
            SUPABASE_URL + f"/rest/v1/places?id=eq.{p['id']}",
            json={"image_url": img_url},
            headers={**SB, "Prefer": "return=minimal"},
            timeout=30
        )
        if r.status_code in (200, 201, 204):
            print(f"   💾 Сохранено: {img_url[:70]}...")
            ok += 1
        else:
            print(f"   ❌ Ошибка сохранения: {r.status_code}")
            fail += 1
    else:
        print("   ⚠️  Фото не найдено")
        fail += 1
    
    time.sleep(2)

print("\n" + "=" * 50)
print(f"✅ Готово: {ok} добавлено, {skip} уже было, {fail} без фото")
