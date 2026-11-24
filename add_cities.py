import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Добавляем API endpoint /api/cities ПЕРЕД @app.route('/api/places')
cities_api = """@app.route('/api/cities')
def get_cities():
    headers = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY}
    url = SUPABASE_URL + "/rest/v1/cities?select=id,name_ru,name_it,name_en,lat,lng,zoom,radius_km&active=eq.true&order=name_it"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return jsonify({"error": "bad response"}), 502
        return jsonify(data)
    except Exception:
        return jsonify({"error": "upstream unavailable"}), 502

"""

if "@app.route('/api/cities')" not in content:
    content = content.replace("@app.route('/api/places')", cities_api + "@app.route('/api/places')")
    changes += 1
    print("✅ API: /api/cities")

# 2. Обновляем /api/places — добавляем параметр city
old_places_url = '"/rest/v1/places?select=id,name,address,latitude,longitude,image_url,place_type,vibe_attributes(noise_level,laptop_friendly,romantic,summary,summary_ru,summary_it,summary_en)"'
new_places_url = '"/rest/v1/places?select=id,name,address,latitude,longitude,image_url,place_type,city,vibe_attributes(noise_level,laptop_friendly,romantic,summary,summary_ru,summary_it,summary_en)"'

if old_places_url in content:
    content = content.replace(old_places_url, new_places_url)
    changes += 1
    print("✅ API: добавлен city в select")

# 3. Добавляем фильтрацию по city в get_places
if "request.args.get('city'" not in content:
    old_filter = "if not isinstance(data, list):"
    new_filter = """city = request.args.get('city', 'bologna')
        data = [p for p in data if p.get('city', 'bologna') == city]
        if not isinstance(data, list):"""
    content = content.replace(old_filter, new_filter)
    changes += 1
    print("✅ API: фильтрация по city")

# 4. Добавляем CSS для переключателя городов
city_css = """.city-switcher{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px}
.city-btn{padding:6px 12px;border-radius:999px;border:1.5px solid var(--track);background:var(--cream);font-size:12px;font-weight:600;color:var(--muted);transition:all .2s}
.city-btn:hover{border-color:var(--terracotta);color:var(--terracotta)}
.city-btn.on{background:var(--terracotta);border-color:var(--terracotta);color:var(--paper)}
body.dark .city-btn{background:#1f1610;border-color:rgba(245,230,211,.15);color:#b8a89a}
body.dark .city-btn:hover{border-color:#C4472B;color:#E9A13B}
body.dark .city-btn.on{background:#C4472B;border-color:#C4472B;color:#fff}
"""

if '.city-switcher{' not in content:
    content = content.replace('</style>', city_css + '\n</style>')
    changes += 1
    print("✅ CSS: city-switcher")

# 5. Добавляем HTML переключателя ПЕРЕД type-filter
city_html = """        <div class="city-switcher" id="citySwitcher">
          <button class="city-btn on" data-city="bologna" onclick="setCity('bologna')">🏛️ Bologna</button>
          <button class="city-btn" data-city="rome" onclick="setCity('rome')">🏛️ Roma</button>
          <button class="city-btn" data-city="milan" onclick="setCity('milan')">🏛️ Milano</button>
          <button class="city-btn" data-city="florence" onclick="setCity('florence')">🏛️ Firenze</button>
        </div>
"""

if 'id="citySwitcher"' not in content:
    content = content.replace('<div class="type-filter">', city_html + '        <div class="type-filter">')
    changes += 1
    print("✅ HTML: city-switcher")

# 6. Добавляем state.currentCity
if "currentCity:'bologna'" not in content and "currentCity: 'bologna'" not in content:
    content = content.replace("placeType:'all'", "placeType:'all',currentCity:'bologna'")
    changes += 1
    print("✅ State: currentCity")

# 7. Добавляем функцию setCity и loadCities
city_js = """
let citiesData = [];
function setCity(cityId){
  state.currentCity = cityId;
  localStorage.setItem('vs-city', cityId);
  document.querySelectorAll('.city-btn').forEach(b => b.classList.toggle('on', b.getAttribute('data-city') === cityId));
  const city = citiesData.find(c => c.id === cityId);
  if(city && map){
    map.setView([city.lat, city.lng], city.zoom || 14);
  }
  loadPlaces();
}
function loadCities(){
  fetch('/api/cities').then(r => r.json()).then(data => {
    if(!Array.isArray(data)) return;
    citiesData = data;
    const saved = localStorage.getItem('vs-city') || 'bologna';
    const switcher = document.getElementById('citySwitcher');
    if(switcher && data.length > 0){
      switcher.innerHTML = data.map(c => 
        '<button class="city-btn' + (c.id === saved ? ' on' : '') + '" data-city="' + c.id + '" onclick="setCity(\\'' + c.id + '\\')">' + 
        '🏛️ ' + c['name_' + lang] + '</button>'
      ).join('');
    }
    const city = data.find(c => c.id === saved);
    if(city && map){
      map.setView([city.lat, city.lng], city.zoom || 14);
    }
  }).catch(() => {});
}
"""

if 'function setCity' not in content:
    content = content.replace("loadPlaces();", "loadCities();loadPlaces();\n" + city_js)
    changes += 1
    print("✅ JS: setCity + loadCities")

# 8. Обновляем loadPlaces — добавляем параметр city
if "fetch('/api/places'" in content and "city=" not in content:
    content = content.replace(
        "fetch('/api/places',{cache:'no-store'})",
        "fetch('/api/places?city='+state.currentCity,{cache:'no-store'})"
    )
    changes += 1
    print("✅ JS: city параметр в запросе")

# 9. Обновляем fitAll для текущего города
if "map.setView([44.4924,11.3426],14)" in content:
    content = content.replace(
        "map.setView([44.4924,11.3426],14);map.fitBounds(L.latLngBounds(places.filter(p=>Math.abs(p.latitude-44.4924)<0.02&&Math.abs(p.longitude-11.3426)<0.03).map(p=>[p.latitude,p.longitude])),{padding:[36,36],maxZoom:16});",
        "const city=citiesData.find(c=>c.id===state.currentCity);if(city){map.setView([city.lat,city.lng],city.zoom||14);}map.fitBounds(L.latLngBounds(places.map(p=>[p.latitude,p.longitude])),{padding:[36,36],maxZoom:16});"
    )
    changes += 1
    print("✅ JS: fitAll для текущего города")

# 10. Сброс currentCity при resetAll
if "state.placeType='all'" in content and "state.currentCity='bologna'" not in content:
    content = content.replace("state.placeType='all';", "state.placeType='all';state.currentCity='bologna';")
    changes += 1
    print("✅ Reset: сброс currentCity")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎯 Всего изменений: {changes}")
print("🌍 Города добавлены!")
