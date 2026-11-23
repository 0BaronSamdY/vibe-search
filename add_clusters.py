import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Добавь Leaflet.markercluster CSS в <head>
if 'leaflet.markercluster' not in content:
    cluster_css = '<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">\n<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">'
    content = content.replace('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">', 
                              '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">\n' + cluster_css)
    changes += 1
    print("✅ CSS: markercluster")

# 2. Добавь Leaflet.markercluster JS перед </body>
if 'MarkerCluster.js' not in content:
    cluster_js = '<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>'
    content = content.replace('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>',
                              '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n' + cluster_js)
    changes += 1
    print("✅ JS: markercluster")

# 3. Замени markers={} на markers=null и создай clusterGroup
if 'let places=[],markers={},map=null' in content:
    content = content.replace('let places=[],markers={},map=null', 'let places=[],markers=null,markerCluster=null,map=null')
    changes += 1
    print("✅ State: markerCluster")

# 4. Замени renderMarkers на кластеризованную версию
old_render = """function renderMarkers(list){
  if(!map)return;
  Object.keys(markers).forEach(k=>map.removeLayer(markers[k]));markers={};
  list.forEach(p=>{
    const mk=L.marker([p.latitude,p.longitude],{icon:makeIcon(p)}).addTo(map);
    mk.bindPopup(popupHTML(p),{maxWidth:280});
    mk.on('popupopen',()=>{setTimeout(()=>loadReviews(p.id),150);});
    markers[p.id]=mk;
  });
}"""

new_render = """function renderMarkers(list){
  if(!map)return;
  if(markerCluster){map.removeLayer(markerCluster);markerCluster=null;}
  markerCluster=L.markerClusterGroup({maxClusterRadius:50,spiderfyOnMaxZoom:true});
  list.forEach(p=>{
    const mk=L.marker([p.latitude,p.longitude],{icon:makeIcon(p)});
    mk.bindPopup(popupHTML(p),{maxWidth:280});
    mk.on('popupopen',()=>{setTimeout(()=>loadReviews(p.id),150);});
    markerCluster.addLayer(mk);
  });
  map.addLayer(markerCluster);
}"""

if old_render in content:
    content = content.replace(old_render, new_render)
    changes += 1
    print("✅ renderMarkers: кластеризация")
else:
    print("⚠️  renderMarkers не найден — возможно уже обновлён")

# 5. Обнови fitAll чтобы учитывал кластеры
if 'map.fitBounds(L.latLngBounds(places.map' in content:
    old_fit = 'map.fitBounds(L.latLngBounds(places.map(p=>[p.latitude,p.longitude]))'
    new_fit = 'map.fitBounds(markerCluster.getBounds())'
    content = content.replace(old_fit, new_fit)
    changes += 1
    print("✅ fitAll: cluster bounds")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎯 Всего изменений: {changes}")
