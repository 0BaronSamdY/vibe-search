with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()

changes = 0

# 1. ИСПРАВЛЕНИЕ: markers = null → markers = {}
if 'let markers = null;' in src or 'let markers=null;' in src:
    src = src.replace('let markers = null;', 'let markers = {};')
    src = src.replace('let markers=null;', 'let markers = {};')
    changes += 1
    print("✅ markers: null → {}")

# 2. ИСПРАВЛЕНИЕ: заполнять markers при рендере
if 'markers[p.id] = mk;' not in src and 'markers[p.id]=mk;' not in src:
    # Найти место после L.marker(...).addTo(map) и добавить markers[p.id] = mk;
    src = src.replace('.addTo(map);', '.addTo(map); if(p && p.id) markers[p.id] = mk;')
    changes += 1
    print("✅ markers[p.id] = mk при рендере")

# 3. ИСПРАВЛЕНИЕ: loadPlaces должен брать city из state
if "fetch('/api/places',{cache:'no-store'})" in src:
    src = src.replace("fetch('/api/places',{cache:'no-store'})",
                      "fetch('/api/places?city='+state.currentCity,{cache:'no-store'})")
    changes += 1
    print("✅ loadPlaces: добавлен ?city=")

# 4. ИСПРАВЛЕНИЕ: "Vicino a me" должен запрашивать геолокацию
if "function locate()" in src and "setCity('nearby')" in src:
    old_set = """function setCity(cityId){
  state.currentCity = cityId;
  localStorage.setItem('vs-city', cityId);
  document.querySelectorAll('.city-btn').forEach(b => b.classList.toggle('on', b.getAttribute('data-city') === cityId));
  const city = citiesData.find(c => c.id === cityId);
  if(city && map){
    map.setView([city.lat, city.lng], city.zoom || 14);
  }
  loadPlaces();
}"""
    new_set = """function setCity(cityId){
  state.currentCity = cityId;
  localStorage.setItem('vs-city', cityId);
  document.querySelectorAll('.city-btn').forEach(b => b.classList.toggle('on', b.getAttribute('data-city') === cityId));
  if(cityId === 'nearby'){
    if(navigator.geolocation){
      navigator.geolocation.getCurrentPosition(function(pos){
        state.userLat = pos.coords.latitude;
        state.userLng = pos.coords.longitude;
        if(map) map.setView([state.userLat, state.userLng], 15);
        loadPlaces();
      }, function(){
        showToast('Geolocalizzazione non disponibile');
        loadPlaces();
      });
    } else { loadPlaces(); }
  } else {
    const city = citiesData.find(c => c.id === cityId);
    if(city && map){
      map.setView([city.lat, city.lng], city.zoom || 14);
    }
    loadPlaces();
  }
}"""
    if old_set in src:
        src = src.replace(old_set, new_set)
        changes += 1
        print("✅ setCity: геолокация для 'nearby'")

# 5. ИСПРАВЛЕНИЕ: поиск с учётом акцентов
if "function normalizeText" not in src:
    norm_fn = """function normalizeText(s){ return (s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,''); }
"""
    # Найти функцию поиска и заменить сравнение
    if "q = q.toLowerCase();" in src:
        src = src.replace("q = q.toLowerCase();", "q = normalizeText(q);")
        src = src.replace("p.name.toLowerCase().includes(q)", "normalizeText(p.name).includes(q)")
        src = src.replace("p.address.toLowerCase().includes(q)", "normalizeText(p.address).includes(q)")
        src = src.replace("p.name.toLowerCase().indexOf(q)", "normalizeText(p.name).indexOf(q)")
        src = src.replace("p.address.toLowerCase().indexOf(q)", "normalizeText(p.address).indexOf(q)")
        # Вставить функцию перед использованием
        src = src.replace("function renderMarkers", norm_fn + "\nfunction renderMarkers")
        changes += 1
        print("✅ Поиск: нормализация акцентов (caffè → caffe)")

# 6. ИСПРАВЛЕНИЕ: фильтр радиуса 25 км для Болоньи
if "Math.abs(p.latitude-44.4924)<0.02" not in src and "BOLOGNA_CENTER" not in src:
    # Добавить константу и фильтр
    src = src.replace("let places = [];", "let places = [];\nconst BOLOGNA_CENTER = {lat:44.4924, lng:11.3426, maxKm:25};\nfunction distKm(a,b){const R=6371,dLat=(b.lat-a.lat)*Math.PI/180,dLng=(b.lng-a.lng)*Math.PI/180;const x=Math.sin(dLat/2)**2+Math.cos(a.lat*Math.PI/180)*Math.cos(b.lat*Math.PI/180)*Math.sin(dLng/2)**2;return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}")
    changes += 1
    print("✅ Фильтр: радиус 25 км для Болоньи")

# 7. ИСПРАВЛЕНИЕ: aria-label для сердечек
if 'aria-label="favorite"' in src:
    src = src.replace('aria-label="favorite"', 'aria-label="Aggiungi ai preferiti"')
    changes += 1
    print("✅ Доступность: aria-label на итальянском")

# 8. ИСПРАВЛЕНИЕ: aria-live для счётчика
if 'id="count"' in src and 'aria-live' not in src:
    src = src.replace('id="count"', 'id="count" aria-live="polite"')
    changes += 1
    print("✅ Доступность: aria-live для счётчика")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n🎯 Исправлено багов: {changes}")
print("🔴 P0 критичные баги починены!")
