from flask import Flask, render_template_string, jsonify
import requests
from config import SUPABASE_URL, SUPABASE_KEY

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vibe Search Bologna</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}
.container{max-width:600px;margin:0 auto}
.lang-switcher{display:flex;justify-content:center;gap:10px;margin-bottom:20px}
.lang-btn{padding:8px 16px;border:2px solid rgba(255,255,255,0.3);border-radius:20px;background:rgba(255,255,255,0.1);color:white;font-weight:600;cursor:pointer}
.lang-btn.active{background:white;color:#667eea}
h1{color:white;text-align:center;margin-bottom:10px;font-size:28px}
.subtitle{color:rgba(255,255,255,0.9);text-align:center;margin-bottom:20px;font-size:14px}
#map{height:300px;border-radius:15px;margin-bottom:20px;box-shadow:0 5px 20px rgba(0,0,0,0.2)}
.filters{background:white;border-radius:15px;padding:20px;margin-bottom:20px}
.filter-group{margin-bottom:15px}
.filter-group label{display:block;font-weight:600;margin-bottom:5px;color:#333}
.filter-group input[type=range]{width:100%;height:6px;border-radius:3px;background:#ddd}
.filter-value{display:inline-block;background:#667eea;color:white;padding:2px 8px;border-radius:10px;font-size:12px;margin-left:10px}
.presets{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}
.preset-btn{flex:1;min-width:100px;padding:12px;border:none;border-radius:10px;background:white;color:#667eea;font-weight:600;cursor:pointer}
.places{display:flex;flex-direction:column;gap:15px}
.place-card{background:white;border-radius:15px;padding:20px;box-shadow:0 5px 20px rgba(0,0,0,0.15)}
.place-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.place-name{font-size:18px;font-weight:700;color:#333}
.noise-indicator{width:12px;height:12px;border-radius:50%}
.noise-low{background:#4CAF50}
.noise-medium{background:#FFC107}
.noise-high{background:#F44336}
.place-address{color:#666;font-size:14px;margin-bottom:15px}
.metrics{display:flex;justify-content:space-around;margin-bottom:15px}
.metric{text-align:center}
.metric-value{font-size:20px;font-weight:700;color:#667eea}
.metric-label{font-size:11px;color:#999;margin-top:3px}
.summary{background:#f5f5f5;padding:12px;border-radius:8px;font-size:14px;color:#555;margin-bottom:15px}
.map-link{display:block;text-align:center;padding:10px;background:#667eea;color:white;text-decoration:none;border-radius:8px;font-weight:600}
.stats{text-align:center;color:white;margin-bottom:15px;font-size:14px}
.leaflet-popup-content-wrapper{border-radius:10px}
.leaflet-popup-content{margin:10px;font-size:14px}
.popup-title{font-weight:700;font-size:16px;margin-bottom:5px}
.popup-metrics{display:flex;gap:10px;margin:8px 0}
.popup-metric{text-align:center;flex:1}
.popup-metric-value{font-size:18px;font-weight:700;color:#667eea}
.popup-metric-label{font-size:10px;color:#999}
</style>
</head>
<body>
<div class="container">
<div class="lang-switcher">
<button class="lang-btn" data-lang="ru" onclick="setLanguage('ru',this)">RU</button>
<button class="lang-btn" data-lang="it" onclick="setLanguage('it',this)">IT</button>
<button class="lang-btn" data-lang="en" onclick="setLanguage('en',this)">EN</button>
</div>
<h1 data-i18n="title">Vibe Search</h1>
<p class="subtitle" data-i18n="subtitle">Bologna</p>

<div id="map"></div>

<div class="presets">
<button class="preset-btn" onclick="applyPreset('work')" data-i18n="preset_work">Work</button>
<button class="preset-btn" onclick="applyPreset('date')" data-i18n="preset_date">Date</button>
<button class="preset-btn" onclick="applyPreset('party')" data-i18n="preset_party">Party</button>
</div>
<div class="filters">
<div class="filter-group"><label data-i18n="filter_noise">Noise <span class="filter-value" id="noise-val">0-1</span></label><input type="range" id="noise-min" min="0" max="1" step="0.1" value="0" oninput="updateFilters()"><input type="range" id="noise-max" min="0" max="1" step="0.1" value="1" oninput="updateFilters()"></div>
<div class="filter-group"><label data-i18n="filter_laptop">Work <span class="filter-value" id="laptop-val">0-1</span></label><input type="range" id="laptop-min" min="0" max="1" step="0.1" value="0" oninput="updateFilters()"><input type="range" id="laptop-max" min="0" max="1" step="0.1" value="1" oninput="updateFilters()"></div>
<div class="filter-group"><label data-i18n="filter_romantic">Romantic <span class="filter-value" id="romantic-val">0-1</span></label><input type="range" id="romantic-min" min="0" max="1" step="0.1" value="0" oninput="updateFilters()"><input type="range" id="romantic-max" min="0" max="1" step="0.1" value="1" oninput="updateFilters()"></div>
</div>
<div class="stats" id="stats">Loading...</div>
<div class="places" id="places"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const T={ru:{title:"Vibe Search",subtitle:"Болонья - Найди место",preset_work:"Тихо для работы",preset_date:"Для свидания",preset_party:"Тусовка",filter_noise:"Шум",filter_laptop:"Для работы",filter_romantic:"Романтика",found:"Найдено",of:"из",nothing_found:"Ничего не найдено",noise:"Шум",work:"Работа",romantic:"Романтика",no_description:"Нет описания",build_route:"Маршрут",address_unknown:"адрес неизвестен",route:"Построить маршрут"},it:{title:"Vibe Search",subtitle:"Bologna - Trova il posto",preset_work:"Silenzioso",preset_date:"Appuntamento",preset_party:"Festa",filter_noise:"Rumore",filter_laptop:"Lavoro",filter_romantic:"Romantico",found:"Trovato",of:"di",nothing_found:"Nessun risultato",noise:"Rumore",work:"Lavoro",romantic:"Romantico",no_description:"Nessuna descrizione",build_route:"Percorso",address_unknown:"indirizzo sconosciuto",route:"Calcola percorso"},en:{title:"Vibe Search",subtitle:"Bologna - Find a place",preset_work:"Quiet for work",preset_date:"For a date",preset_party:"Party",filter_noise:"Noise",filter_laptop:"For work",filter_romantic:"Romantic",found:"Found",of:"of",nothing_found:"Nothing found",noise:"Noise",work:"Work",romantic:"Romantic",no_description:"No description",build_route:"Route",address_unknown:"address unknown",route:"Build route"}};
let lang=localStorage.getItem('lang')||'ru';
let places=[];
let markers=[];
let map;

function t(k){return T[lang][k]||k}

function setLanguage(l,btn){
    lang=l;
    localStorage.setItem('lang',l);
    document.querySelectorAll('[data-i18n]').forEach(e=>{
        const k=e.getAttribute('data-i18n');
        if(T[l][k]){
            const span=e.querySelector('.filter-value');
            if(span){e.firstChild.textContent=T[l][k]+' ';}
            else{e.textContent=T[l][k];}
        }
    });
    document.querySelectorAll('.lang-btn').forEach(b=>b.classList.remove('active'));
    const target=btn||document.querySelector('.lang-btn[data-lang="'+l+'"]');
    if(target)target.classList.add('active');
    updateFilters();
}

function getNoiseColor(level){
    if(level<0.4)return '#4CAF50';
    if(level<0.7)return '#FFC107';
    return '#F44336';
}

function createCustomIcon(color){
    return L.divIcon({
        className:'custom-marker',
        html:'<div style="background:'+color+';width:20px;height:20px;border-radius:50%;border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3)"></div>',
        iconSize:[20,20],
        iconAnchor:[10,10]
    });
}

async function loadPlaces(){
    const stats=document.getElementById('stats');
    try{
        stats.textContent='Loading...';
        const r=await fetch('/api/places');
        if(!r.ok)throw new Error('HTTP '+r.status);
        places=await r.json();
        console.log('Loaded',places.length,'places');
        initMap();
        updateFilters();
    }catch(e){
        stats.textContent='Error: '+e.message;
        console.error(e);
    }
}

function initMap(){
    if(map)return;
    map=L.map('map').setView([44.4924,11.3426],14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
        attribution:'© OpenStreetMap',
        maxZoom:19
    }).addTo(map);
}

function updateMarkers(filtered){
    markers.forEach(m=>map.removeLayer(m));
    markers=[];
    filtered.forEach(p=>{
        const v=p.vibe_attributes[0];
        const color=getNoiseColor(v.noise_level);
        const marker=L.marker([p.latitude,p.longitude],{icon:createCustomIcon(color)}).addTo(map);
        const popupContent='<div class="popup-title">'+p.name+'</div>'+
            '<div style="font-size:12px;color:#666;margin-bottom:8px">'+(p.address||t('address_unknown'))+'</div>'+
            '<div class="popup-metrics">'+
            '<div class="popup-metric"><div class="popup-metric-value">'+v.noise_level.toFixed(1)+'</div><div class="popup-metric-label">'+t('noise')+'</div></div>'+
            '<div class="popup-metric"><div class="popup-metric-value">'+v.laptop_friendly.toFixed(1)+'</div><div class="popup-metric-label">'+t('work')+'</div></div>'+
            '<div class="popup-metric"><div class="popup-metric-value">'+v.romantic.toFixed(1)+'</div><div class="popup-metric-label">'+t('romantic')+'</div></div>'+
            '</div>'+
            '<div style="font-size:12px;color:#555;margin-bottom:8px">'+(v.summary||t('no_description'))+'</div>'+
            '<a href="https://www.google.com/maps/dir/?api=1&destination='+p.latitude+','+p.longitude+'" target="_blank" style="display:block;text-align:center;padding:6px;background:#667eea;color:white;text-decoration:none;border-radius:5px;font-size:12px;font-weight:600">'+t('route')+'</a>';
        marker.bindPopup(popupContent);
        markers.push(marker);
    });
}

function updateFilters(){
    const nMin=+document.getElementById('noise-min').value;
    const nMax=+document.getElementById('noise-max').value;
    const lMin=+document.getElementById('laptop-min').value;
    const lMax=+document.getElementById('laptop-max').value;
    const rMin=+document.getElementById('romantic-min').value;
    const rMax=+document.getElementById('romantic-max').value;
    document.getElementById('noise-val').textContent=nMin+'-'+nMax;
    document.getElementById('laptop-val').textContent=lMin+'-'+lMax;
    document.getElementById('romantic-val').textContent=rMin+'-'+rMax;
    const f=places.filter(p=>{
        if(!p.vibe_attributes||!p.vibe_attributes.length)return false;
        const v=p.vibe_attributes[0];
        return nMin<=v.noise_level&&v.noise_level<=nMax&&lMin<=v.laptop_friendly&&v.laptop_friendly<=lMax&&rMin<=v.romantic&&v.romantic<=rMax;
    });
    updateMarkers(f);
    renderPlaces(f);
}

function renderPlaces(ps){
    document.getElementById('stats').textContent=t('found')+': '+ps.length+' '+t('of')+' '+places.length;
    const c=document.getElementById('places');
    if(!ps.length){c.innerHTML='<div style="text-align:center;color:white;padding:20px">'+t('nothing_found')+'</div>';return}
    c.innerHTML=ps.map(p=>{
        const v=p.vibe_attributes[0];
        const nc=v.noise_level<0.4?'noise-low':v.noise_level<0.7?'noise-medium':'noise-high';
        return '<div class="place-card"><div class="place-header"><div class="place-name">'+p.name+'</div><div class="noise-indicator '+nc+'"></div></div><div class="place-address">'+(p.address||t('address_unknown'))+'</div><div class="metrics"><div class="metric"><div class="metric-value">'+v.noise_level.toFixed(1)+'</div><div class="metric-label">'+t('noise')+'</div></div><div class="metric"><div class="metric-value">'+v.laptop_friendly.toFixed(1)+'</div><div class="metric-label">'+t('work')+'</div></div><div class="metric"><div class="metric-value">'+v.romantic.toFixed(1)+'</div><div class="metric-label">'+t('romantic')+'</div></div></div><div class="summary">'+(v.summary||t('no_description'))+'</div><a href="https://www.google.com/maps/dir/?api=1&destination='+p.latitude+','+p.longitude+'" class="map-link" target="_blank">'+t('build_route')+'</a></div>';
    }).join('');
}

function applyPreset(type){
    if(type==='work'){document.getElementById('noise-min').value=0;document.getElementById('noise-max').value=0.4;document.getElementById('laptop-min').value=0.6;document.getElementById('laptop-max').value=1;document.getElementById('romantic-min').value=0;document.getElementById('romantic-max').value=1}
    else if(type==='date'){document.getElementById('noise-min').value=0;document.getElementById('noise-max').value=0.6;document.getElementById('laptop-min').value=0;document.getElementById('laptop-max').value=1;document.getElementById('romantic-min').value=0.6;document.getElementById('romantic-max').value=1}
    else{document.getElementById('noise-min').value=0.6;document.getElementById('noise-max').value=1;document.getElementById('laptop-min').value=0;document.getElementById('laptop-max').value=1;document.getElementById('romantic-min').value=0;document.getElementById('romantic-max').value=0.4}
    updateFilters();
}

setLanguage(lang);
loadPlaces();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/places')
def get_places():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY
    }
    url = SUPABASE_URL + "/rest/v1/places?select=id,name,address,latitude,longitude,vibe_attributes(noise_level,laptop_friendly,romantic,summary)"
    response = requests.get(url, headers=headers)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
