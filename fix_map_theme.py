with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Убираем переключение тайлов из toggleTheme
old_toggle = """function toggleTheme(){
  document.body.classList.toggle('dark');
  const isDark=document.body.classList.contains('dark');
  localStorage.setItem('vs-theme',isDark?'dark':'light');
  document.getElementById('themeBtn').textContent=isDark?'☀️':'🌙';
  if(map){
    if(isDark){
      if(window._lightTiles)map.removeLayer(window._lightTiles);
      if(!window._darkTiles){
        window._darkTiles=L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© OpenStreetMap © CARTO',maxZoom:19});
      }
      window._darkTiles.addTo(map);
    }else{
      if(window._darkTiles)map.removeLayer(window._darkTiles);
      if(!window._lightTiles){
        window._lightTiles=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:19});
      }
      window._lightTiles.addTo(map);
    }
  }
}"""

new_toggle = """function toggleTheme(){
  document.body.classList.toggle('dark');
  const isDark=document.body.classList.contains('dark');
  localStorage.setItem('vs-theme',isDark?'dark':'light');
  document.getElementById('themeBtn').textContent=isDark?'☀️':'🌙';
}"""

if old_toggle in content:
    content = content.replace(old_toggle, new_toggle)
    print("✅ toggleTheme: убрано переключение тайлов")
else:
    print("⚠️  old_toggle не найден — возможно уже исправлено")

# 2. Убираем window._lightTiles из инициализации карты
if "window._lightTiles=L.tileLayer" in content:
    content = content.replace(
        "window._lightTiles=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:19});window._lightTiles.addTo(map);",
        "L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:19}).addTo(map);"
    )
    print("✅ Map: убран window._lightTiles")

# 3. Убираем applySavedTheme (он тоже менял тайлы)
if "function applySavedTheme" in content:
    content = content.replace("applySavedTheme();", "")
    print("✅ Убран applySavedTheme")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎯 Карта останется светлой в любой теме!")
