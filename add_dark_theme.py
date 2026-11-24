import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Добавляем CSS-переменные тёмной темы ПЕРЕД закрывающим </style>
dark_css = """
/* ===== ТЁМНАЯ ТЕМА ===== */
body.dark{
  background:radial-gradient(900px 420px at 85% -60px,rgba(233,161,59,.12),transparent 60%),radial-gradient(700px 380px at -80px 30%,rgba(196,71,43,.10),transparent 60%),#1a120b;
  color:#f5e6d3;
}
body.dark header{background:rgba(26,18,11,.95);border-bottom-color:rgba(245,230,211,.15)}
body.dark .brand{color:#f5e6d3}
body.dark .lang-btn{border-color:rgba(245,230,211,.3);color:#f5e6d3;background:transparent}
body.dark .lang-btn.on{background:#C4472B;border-color:#C4472B;color:#fff}
body.dark .panel,body.dark .card{background:#2a1f17;border-color:rgba(245,230,211,.12);box-shadow:0 10px 26px rgba(0,0,0,.4)}
body.dark .card{border-left-color:var(--spine,#C4472B)}
body.dark .searchrow input,body.dark select,body.dark .chip,body.dark .preset,body.dark .type-btn{background:#1f1610;border-color:rgba(245,230,211,.15);color:#f5e6d3}
body.dark .searchrow input:focus{border-color:#C4472B}
body.dark .chip.on{background:#7C2D3E;border-color:#7C2D3E;color:#fff}
body.dark .preset.on{background:#E9A13B;border-color:#E9A13B;color:#1a120b}
body.dark .type-btn.on{background:#E9A13B;border-color:#E9A13B;color:#1a120b}
body.dark .fgroup label{color:#f5e6d3}
body.dark .fgroup .val{background:#1a120b;color:#f5e6d3}
body.dark input[type=range]{background:#3a2a1f}
body.dark input[type=range]::-webkit-slider-thumb{background:#C4472B;border-color:#2a1f17}
body.dark input[type=range]::-moz-range-thumb{background:#C4472B;border-color:#2a1f17}
body.dark input[type=range]::-moz-range-track{background:#3a2a1f}
body.dark .stats{color:#b8a89a}
body.dark .stats b{color:#E9A13B}
body.dark .card h3{color:#f5e6d3}
body.dark .addr{color:#b8a89a}
body.dark .dist{color:#7ab0d4}
body.dark .met-l{color:#b8a89a}
body.dark .met-v{color:#f5e6d3}
body.dark .bar{background:#3a2a1f}
body.dark .sum{background:#1f1610;color:#b8a89a}
body.dark .btn.primary{background:#C4472B;color:#fff}
body.dark .btn.primary:hover{background:#93301C}
body.dark .btn.ghost{border-color:rgba(196,71,43,.5);color:#E9A13B}
body.dark .btn.ghost:hover{background:rgba(196,71,43,.15)}
body.dark .notice{background:#2a1f17;border-color:rgba(196,71,43,.4);color:#f5e6d3}
body.dark .notice h3{color:#f5e6d3}
body.dark .notice p{color:#b8a89a}
body.dark footer{color:#b8a89a}
body.dark .heart{background:#1f1610;border-color:rgba(245,230,211,.2);color:#b8a89a}
body.dark .heart:hover{border-color:#7C2D3E;color:#7C2D3E}
body.dark .heart.on{background:#7C2D3E;border-color:#7C2D3E;color:#fff}
body.dark .pin{border-color:#2a1f17}
body.dark .pin.fav{box-shadow:0 0 0 3px rgba(124,45,62,.5),0 3px 8px rgba(0,0,0,.5)}
body.dark .leaflet-popup-content-wrapper{background:#2a1f17;color:#f5e6d3;border-color:rgba(245,230,211,.15)}
body.dark .leaflet-popup-tip{background:#2a1f17}
body.dark .leaflet-bar a{background:#2a1f17;color:#E9A13B;border-bottom-color:rgba(245,230,211,.15)}
body.dark .pop-img{background:#1f1610}
body.dark .pop-t{color:#f5e6d3}
body.dark .pop-a{color:#b8a89a}
body.dark .pop-dist{color:#7ab0d4}
body.dark .pop-m div{background:#1f1610}
body.dark .pop-m b{color:#f5e6d3}
body.dark .pop-m span{color:#b8a89a}
body.dark .pop-s{color:#b8a89a}
body.dark .pop-reviews{border-top-color:rgba(245,230,211,.15)}
body.dark .pop-reviews h4{color:#b8a89a}
body.dark .pop-review b{color:#f5e6d3}
body.dark .pop-review .cmt{color:#b8a89a}
body.dark .pop-review-form input,body.dark .pop-review-form textarea,body.dark .pop-review-form select{background:#1f1610;border-color:rgba(245,230,211,.15);color:#f5e6d3}
body.dark .pop-review-form button{background:#C4472B;color:#fff}
body.dark .pop-acts button{background:#1f1610;border-color:rgba(245,230,211,.2);color:#b8a89a}
body.dark .pop-acts button.on{background:#7C2D3E;border-color:#7C2D3E;color:#fff}
body.dark #toast{background:#f5e6d3;color:#1a120b}
body.dark #toast button{color:#C4472B}
body.dark .install-banner{background:#C4472B;color:#fff}
body.dark .install-banner button{background:#fff;color:#C4472B}
body.dark .legend{background:rgba(26,18,11,.9);border-color:rgba(245,230,211,.15);color:#b8a89a}
body.dark .tool{background:#2a1f17;border-color:rgba(245,230,211,.15);color:#E9A13B}
body.dark .tool:hover{background:#C4472B;color:#fff}
body.dark .me{background:#7ab0d4}
body.dark .card-img-placeholder{background:linear-gradient(135deg,#1f1610 0%,#2a1f17 100%);color:#b8a89a}
body.dark .type-badge.cafe{background:#E9A13B;color:#1a120b}
body.dark .type-badge.bar{background:#7C2D3E;color:#fff}
body.dark .type-badge.restaurant{background:#5F8F4E;color:#fff}
body.dark .hero h1{color:#f5e6d3}
body.dark .hero h1 em{color:#E9A13B}
body.dark .hero p{color:#b8a89a}
body.dark .arches{background-image:radial-gradient(circle at 14px 14px,transparent 10px,#C4472B 10.5px,#C4472B 12px,transparent 12.5px)}
body.dark .map-wrap{border-color:rgba(245,230,211,.15);background:#1a120b}

/* Кнопка темы */
.theme-btn{width:38px;height:38px;border-radius:50%;border:1.5px solid rgba(147,48,28,.35);background:transparent;font-size:18px;display:grid;place-items:center;transition:all .2s;margin-left:6px}
.theme-btn:hover{background:#C4472B;border-color:#C4472B;color:#fff}
body.dark .theme-btn{border-color:rgba(245,230,211,.3);color:#f5e6d3}
body.dark .theme-btn:hover{background:#E9A13B;border-color:#E9A13B;color:#1a120b}
"""

if '/* ===== ТЁМНАЯ ТЕМА ===== */' not in content:
    content = content.replace('</style>', dark_css + '\n</style>')
    changes += 1
    print("✅ CSS: тёмная тема")

# 2. Добавляем кнопку-переключатель в шапку РЯДОМ с языками
theme_btn_html = '<button class="theme-btn" id="themeBtn" onclick="toggleTheme()" title="Сменить тему">🌙</button>'
if 'id="themeBtn"' not in content:
    old_langs = '<div class="langs">'
    new_langs = '<div class="langs">' + theme_btn_html
    content = content.replace(old_langs, new_langs)
    changes += 1
    print("✅ HTML: кнопка темы")

# 3. Добавляем JS-функцию toggleTheme и применение при загрузке
theme_js = """
function toggleTheme(){
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
}
function applySavedTheme(){
  const saved=localStorage.getItem('vs-theme');
  if(saved==='dark'){
    document.body.classList.add('dark');
    document.getElementById('themeBtn').textContent='☀️';
  }
}
"""

if 'function toggleTheme' not in content:
    content = content.replace('setLanguage(lang);updateFavCount();loadPlaces();',
                              'applySavedTheme();setLanguage(lang);updateFavCount();loadPlaces();\n' + theme_js)
    changes += 1
    print("✅ JS: toggleTheme + applySavedTheme")

# 4. Сохраняем светлые тайлы в переменную для переключения
if "L.tileLayer('https://{s}.tile.openstreetmap.org" in content and 'window._lightTiles' not in content:
    content = content.replace(
        "L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:19}).addTo(map);",
        "window._lightTiles=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:19});window._lightTiles.addTo(map);"
    )
    changes += 1
    print("✅ Map: light tiles в переменную")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎯 Всего изменений: {changes}")
print("🌙 Тёмная тема готова!")
