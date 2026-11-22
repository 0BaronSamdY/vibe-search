import os
from flask import Flask, render_template_string, jsonify
import requests

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
    except ImportError:
        pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#C4472B">
<title>Vibe Search · Bologna</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{
  --terracotta:#C4472B; --terracotta-deep:#93301C; --ochre:#E9A13B;
  --espresso:#2A1B12; --cream:#FAF1E4; --paper:#FFFDF8;
  --olive:#5F8F4E; --wine:#7C2D3E; --sky:#3E7CA6;
  --muted:#6B5A4E; --line:rgba(42,27,18,.12); --track:#E8DCC9;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  font-family:'Inter',system-ui,sans-serif;color:var(--espresso);
  background:
    radial-gradient(900px 420px at 85% -60px, rgba(233,161,59,.20), transparent 60%),
    radial-gradient(700px 380px at -80px 30%, rgba(196,71,43,.14), transparent 60%),
    var(--cream);
  min-height:100vh;
}
body::before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.5;z-index:0;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/><feColorMatrix type='saturate' values='0'/></filter><rect width='120' height='120' filter='url(%23n)' opacity='0.05'/></svg>");}
::selection{background:var(--ochre);color:var(--espresso)}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-track{background:var(--cream)}
::-webkit-scrollbar-thumb{background:rgba(196,71,43,.45);border-radius:8px;border:2px solid var(--cream)}
::-webkit-scrollbar-thumb:hover{background:var(--terracotta)}
*{scrollbar-width:thin;scrollbar-color:rgba(196,71,43,.55) var(--cream)}
button{font:inherit;cursor:pointer}
a{color:var(--terracotta-deep)}
:focus-visible{outline:3px solid var(--sky);outline-offset:2px;border-radius:6px}

header{position:sticky;top:0;z-index:500;background:rgba(250,241,228,.88);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.head-in{max-width:1180px;margin:0 auto;padding:12px 18px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{display:flex;align-items:center;gap:10px;font-family:'Fraunces',serif;font-weight:700;font-size:20px;color:var(--terracotta-deep)}
.brand svg{flex:none}
.langs{display:flex;gap:6px}
.lang-btn{padding:7px 13px;border-radius:999px;border:1.5px solid rgba(147,48,28,.35);background:transparent;color:var(--terracotta-deep);font-weight:600;font-size:13px;transition:all .2s}
.lang-btn:hover{border-color:var(--terracotta)}
.lang-btn.on{background:var(--terracotta);border-color:var(--terracotta);color:var(--paper)}

.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 60px;position:relative;z-index:1}
.hero h1{font-family:'Fraunces',serif;font-size:clamp(34px,6vw,52px);font-weight:700;color:var(--espresso);line-height:1.05}
.hero h1 em{font-style:italic;color:var(--terracotta)}
.hero p{margin-top:8px;color:var(--muted);font-size:15px}
.arches{height:14px;margin:16px 0 20px;opacity:.5;
  background-image:radial-gradient(circle at 14px 14px, transparent 10px, var(--terracotta) 10.5px, var(--terracotta) 12px, transparent 12.5px);
  background-size:28px 14px;background-repeat:repeat-x}

.layout{display:grid;grid-template-columns:1fr;gap:20px}
.map-wrap{position:relative;height:310px;border-radius:18px;overflow:hidden;border:1px solid var(--line);box-shadow:0 14px 34px rgba(42,27,18,.16);scroll-margin-top:86px;background:var(--track)}
#map{position:absolute;inset:0}
.map-tools{position:absolute;top:12px;right:12px;z-index:800;display:flex;flex-direction:column;gap:8px}
.tool{width:40px;height:40px;border-radius:12px;border:1px solid var(--line);background:var(--paper);color:var(--terracotta-deep);display:grid;place-items:center;box-shadow:0 4px 12px rgba(42,27,18,.18);transition:all .2s}
.tool:hover{background:var(--terracotta);color:var(--paper);transform:translateY(-1px)}
.legend{position:absolute;left:12px;bottom:12px;z-index:800;display:flex;gap:12px;background:rgba(255,253,248,.94);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:12px;font-weight:600;color:var(--muted);box-shadow:0 4px 12px rgba(42,27,18,.14)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}

.panel{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 10px 26px rgba(42,27,18,.10);display:flex;flex-direction:column;gap:14px}
.searchrow{position:relative}
.searchrow input{width:100%;padding:12px 42px 12px 40px;border-radius:12px;border:1.5px solid var(--track);background:var(--cream);font:inherit;color:var(--espresso);transition:border .2s}
.searchrow input:focus{border-color:var(--terracotta);outline:none}
.searchrow .mag{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--muted)}
#clearQ{position:absolute;right:8px;top:50%;transform:translateY(-50%);width:28px;height:28px;border:none;border-radius:50%;background:var(--track);color:var(--espresso);font-size:15px;display:none}
#clearQ.show{display:block}
.row2{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
select{flex:1;min-width:170px;padding:10px 12px;border-radius:12px;border:1.5px solid var(--track);background:var(--cream);font:inherit;font-size:13px;font-weight:600;color:var(--espresso)}
.chip{padding:10px 14px;border-radius:999px;border:1.5px solid var(--track);background:var(--cream);font-size:13px;font-weight:600;color:var(--muted);transition:all .2s}
.chip:hover{border-color:var(--wine);color:var(--wine)}
.chip.on{background:var(--wine);border-color:var(--wine);color:var(--paper)}
.chip b{margin-left:4px}
.presets{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.preset{padding:12px 8px;border-radius:12px;border:1.5px solid var(--track);background:var(--cream);font-weight:600;font-size:13px;color:var(--espresso);transition:all .2s}
.preset:hover{transform:translateY(-1px);border-color:var(--ochre)}
.preset.on{background:var(--ochre);border-color:var(--ochre);color:var(--espresso);box-shadow:0 6px 16px rgba(233,161,59,.4)}
.fgroup label{display:flex;align-items:center;gap:8px;font-weight:600;font-size:14px;margin-bottom:6px}
.fgroup .val{margin-left:auto;background:var(--espresso);color:var(--cream);font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;font-variant-numeric:tabular-nums}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:6px;border-radius:6px;background:var(--track);margin:7px 0}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:var(--terracotta);border:3px solid var(--paper);box-shadow:0 2px 6px rgba(42,27,18,.3);cursor:grab;transition:transform .15s}
input[type=range]::-webkit-slider-thumb:hover{transform:scale(1.15)}
input[type=range]::-moz-range-thumb{width:14px;height:14px;border-radius:50%;background:var(--terracotta);border:3px solid var(--paper);box-shadow:0 2px 6px rgba(42,27,18,.3);cursor:grab}
input[type=range]::-moz-range-track{height:6px;border-radius:6px;background:var(--track)}

.stats{margin:18px 2px 12px;font-size:14px;font-weight:600;color:var(--muted)}
.stats b{color:var(--terracotta-deep)}
.places{display:flex;flex-direction:column;gap:14px}
.card{background:var(--paper);border:1px solid var(--line);border-left:6px solid var(--spine,var(--terracotta));border-radius:16px;padding:18px;box-shadow:0 6px 18px rgba(42,27,18,.08);transition:transform .2s,box-shadow .2s;animation:rise .35s ease both}
.card:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(42,27,18,.14)}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.card h3{font-family:'Fraunces',serif;font-size:20px;font-weight:700;line-height:1.2}
.heart{flex:none;width:36px;height:36px;border-radius:50%;border:1.5px solid var(--track);background:var(--cream);color:#C9B8A8;font-size:17px;line-height:1;transition:all .2s}
.heart:hover{border-color:var(--wine);color:var(--wine);transform:scale(1.08)}
.heart.on{background:var(--wine);border-color:var(--wine);color:var(--paper)}
.addr{color:var(--muted);font-size:13px;margin:4px 0 12px}
.mets{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px}
.met{display:flex;flex-direction:column;gap:3px}
.met-l{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.met-v{font-family:'Fraunces',serif;font-size:20px;font-weight:700}
.bar{height:5px;border-radius:5px;background:var(--track);overflow:hidden}
.bar i{display:block;height:100%;border-radius:5px;transition:width .4s ease}
.sum{background:var(--cream);border-radius:10px;padding:11px 13px;font-size:13.5px;line-height:1.5;color:var(--muted);margin-bottom:14px}
.acts{display:flex;gap:8px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:10px 16px;border-radius:11px;font-weight:600;font-size:13.5px;text-decoration:none;border:1.5px solid transparent;transition:all .2s}
.btn.primary{background:var(--terracotta);color:var(--paper);flex:1}
.btn.primary:hover{background:var(--terracotta-deep)}
.btn.ghost{background:transparent;border-color:rgba(147,48,28,.4);color:var(--terracotta-deep)}
.btn.ghost:hover{border-color:var(--terracotta);background:rgba(196,71,43,.08)}

.notice{background:var(--paper);border:1px dashed rgba(147,48,28,.4);border-radius:16px;padding:34px 22px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:10px}
.notice .cup{font-size:38px}
.notice h3{font-family:'Fraunces',serif;font-size:20px}
.notice p{color:var(--muted);font-size:14px}
.skel{pointer-events:none}
.sk{display:block;border-radius:8px;background:linear-gradient(90deg,var(--track) 25%,#F4EADA 50%,var(--track) 75%);background-size:200% 100%;animation:shim 1.2s infinite}
.sk.l1{height:22px;width:60%;margin-bottom:12px}
.sk.l2{height:14px;width:85%;margin-bottom:10px}
.sk.l3{height:52px;width:100%}
@keyframes shim{to{background-position:-200% 0}}

#toast{position:fixed;left:50%;bottom:22px;transform:translate(-50%,16px);z-index:1200;background:var(--espresso);color:var(--cream);padding:12px 18px;border-radius:12px;font-size:14px;font-weight:600;display:flex;gap:14px;align-items:center;box-shadow:0 12px 30px rgba(42,27,18,.4);opacity:0;pointer-events:none;transition:all .3s}
#toast.show{opacity:1;transform:translate(-50%,0);pointer-events:auto}
#toast button{border:none;background:transparent;color:var(--ochre);font-weight:700;font-size:14px}

footer{margin-top:34px;text-align:center;color:var(--muted);font-size:12px}

.leaflet-container{font-family:'Inter',sans-serif;background:var(--track)}
.leaflet-popup-content-wrapper{background:var(--paper);color:var(--espresso);border-radius:14px;border:1px solid var(--line);box-shadow:0 12px 30px rgba(42,27,18,.25)}
.leaflet-popup-tip{background:var(--paper)}
.leaflet-popup-content{margin:14px 16px;font-size:13px;line-height:1.45}
.leaflet-bar a{background:var(--paper);color:var(--terracotta-deep);border-bottom:1px solid var(--line)}
.leaflet-bar a:hover{background:var(--cream);color:var(--terracotta)}
.vs-pin-wrap{background:none;border:none}
.pin{display:block;width:16px;height:16px;border-radius:50%;border:3px solid var(--paper);box-shadow:0 3px 8px rgba(42,27,18,.4);color:var(--paper);font-size:9px;line-height:16px;text-align:center}
.pin.fav{box-shadow:0 0 0 3px rgba(124,45,62,.4),0 3px 8px rgba(42,27,18,.4)}
.me{display:block;width:12px;height:12px;border-radius:50%;background:var(--sky);border:3px solid #fff;animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 3px rgba(62,124,166,.35)}70%{box-shadow:0 0 0 14px rgba(62,124,166,0)}100%{box-shadow:0 0 0 3px rgba(62,124,166,0)}}
.pop-t{font-family:'Fraunces',serif;font-weight:700;font-size:16px;margin-bottom:2px}
.pop-a{color:var(--muted);font-size:12px;margin-bottom:8px}
.pop-m{display:flex;gap:8px;margin-bottom:8px}
.pop-m div{flex:1;text-align:center;background:var(--cream);border-radius:8px;padding:6px 2px}
.pop-m b{display:block;font-family:'Fraunces',serif;font-size:15px}
.pop-m span{font-size:10px;color:var(--muted)}
.pop-s{color:var(--muted);font-size:12px;margin-bottom:10px}
.pop-acts{display:flex;gap:6px}
.pop-acts a,.pop-acts button{flex:1;text-align:center;padding:7px 6px;border-radius:8px;font-size:12px;font-weight:600;text-decoration:none}
.pop-acts a{background:var(--terracotta);color:var(--paper)}
.pop-acts button{border:1.5px solid var(--track);background:var(--cream);color:#C9B8A8}
.pop-acts button.on{background:var(--wine);border-color:var(--wine);color:var(--paper)}

@media(min-width:980px){
  .layout{grid-template-columns:minmax(400px,46%) 1fr;align-items:start}
  .map-col{position:sticky;top:84px}
  .map-wrap{height:calc(100vh - 120px);min-height:480px}
}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<header><div class="head-in">
  <div class="brand">
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none"><path d="M4 8h12v6a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V8Z" fill="#C4472B"/><path d="M16 9h2a3 3 0 0 1 0 6h-2" stroke="#93301C" stroke-width="2"/><path d="M7 5c0-1.2 1-1.3 1-2.5M11 5c0-1.2 1-1.3 1-2.5" stroke="#E9A13B" stroke-width="1.6" stroke-linecap="round"/></svg>
    Vibe Search
  </div>
  <div class="langs">
    <button class="lang-btn" data-lang="ru" onclick="setLanguage('ru')">RU</button>
    <button class="lang-btn" data-lang="it" onclick="setLanguage('it')">IT</button>
    <button class="lang-btn" data-lang="en" onclick="setLanguage('en')">EN</button>
  </div>
</div></header>

<div class="wrap">
  <div class="hero">
    <h1>Vibe <em>Search</em></h1>
    <p data-i18n="subtitle">Болонья · найди место под настроение</p>
  </div>
  <div class="arches"></div>

  <div class="layout">
    <div class="map-col">
      <div class="map-wrap" id="mapWrap">
        <div id="map"></div>
        <div class="map-tools">
          <button class="tool" id="fitBtn" aria-label="fit"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M9 3H3v6M15 3h6v6M9 21H3v-6M15 21h6v-6"/></svg></button>
          <button class="tool" id="locBtn" aria-label="locate"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="6"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg></button>
        </div>
        <div class="legend">
          <span><i style="background:#5F8F4E"></i><span data-i18n="legend_quiet">тихо</span></span>
          <span><i style="background:#E9A13B"></i><span data-i18n="legend_mid">средне</span></span>
          <span><i style="background:#C4472B"></i><span data-i18n="legend_loud">шумно</span></span>
        </div>
      </div>
    </div>

    <div class="list-col">
      <section class="panel">
        <div class="searchrow">
          <svg class="mag" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input id="q" type="text" data-i18n-ph="search_ph" placeholder="Поиск по названию или адресу…" autocomplete="off">
          <button id="clearQ" aria-label="clear">×</button>
        </div>
        <div class="row2">
          <select id="sortSel">
            <option value="default" data-i18n="sort_default">Сортировка: по умолчанию</option>
            <option value="quiet" data-i18n="sort_quiet">Сначала тихие</option>
            <option value="work" data-i18n="sort_work">Лучшие для работы</option>
            <option value="romantic" data-i18n="sort_romantic">Самые романтичные</option>
            <option value="name" data-i18n="sort_name">По имени А–Я</option>
          </select>
          <button class="chip" id="favChip">♥ <span data-i18n="favs">Избранное</span><b id="favCount">0</b></button>
          <button class="chip" id="resetBtn" data-i18n="reset">Сбросить</button>
        </div>
        <div class="presets">
          <button class="preset" data-preset="work" onclick="applyPreset('work')" data-i18n="preset_work">🤫 Тихо для работы</button>
          <button class="preset" data-preset="date" onclick="applyPreset('date')" data-i18n="preset_date">💑 Для свидания</button>
          <button class="preset" data-preset="party" onclick="applyPreset('party')" data-i18n="preset_party">🎉 Тусовка</button>
        </div>
        <div class="fgroup">
          <label><span data-i18n="filter_noise">Шум</span><span class="val" id="noiseVal">0.0 – 1.0</span></label>
          <input type="range" id="nMin" min="0" max="1" step="0.1" value="0" aria-label="noise min">
          <input type="range" id="nMax" min="0" max="1" step="0.1" value="1" aria-label="noise max">
        </div>
        <div class="fgroup">
          <label><span data-i18n="filter_laptop">Для работы</span><span class="val" id="laptopVal">0.0 – 1.0</span></label>
          <input type="range" id="lMin" min="0" max="1" step="0.1" value="0" aria-label="work min">
          <input type="range" id="lMax" min="0" max="1" step="0.1" value="1" aria-label="work max">
        </div>
        <div class="fgroup">
          <label><span data-i18n="filter_romantic">Романтика</span><span class="val" id="romanticVal">0.0 – 1.0</span></label>
          <input type="range" id="rMin" min="0" max="1" step="0.1" value="0" aria-label="romantic min">
          <input type="range" id="rMax" min="0" max="1" step="0.1" value="1" aria-label="romantic max">
        </div>
      </section>

      <div class="stats" id="stats"></div>
      <div class="places" id="places"></div>
    </div>
  </div>

  <footer><span data-i18n="data_note">Данные © OpenStreetMap contributors</span> · Vibe Search</footer>
</div>

<div id="toast" role="status"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const T={
ru:{subtitle:"Болонья · найди место под настроение",search_ph:"Поиск по названию или адресу…",sort_default:"Сортировка: по умолчанию",sort_quiet:"Сначала тихие",sort_work:"Лучшие для работы",sort_romantic:"Самые романтичные",sort_name:"По имени А–Я",preset_work:"🤫 Тихо для работы",preset_date:"💑 Для свидания",preset_party:"🎉 Тусовка",favs:"Избранное",reset:"Сбросить",filter_noise:"Шум",filter_laptop:"Для работы",filter_romantic:"Романтика",legend_quiet:"тихо",legend_mid:"средне",legend_loud:"шумно",found:"Найдено",of:"из",nothing_found:"Ничего не найдено",nothing_hint:"Попробуй смягчить фильтры или сбросить их.",error_title:"Не удалось загрузить места",retry:"Повторить",loading:"Загружаем места…",noise:"Шум",work:"Работа",romantic:"Романтика",no_description:"Описание появится позже.",route:"Маршрут",show_map:"На карте",address_unknown:"адрес уточняется",fav_add:"Добавлено в избранное",fav_remove:"Убрано из избранного",undo:"Вернуть",loc_err:"Не удалось определить местоположение",fit_title:"Показать все места",loc_title:"Моё местоположение",data_note:"Данные © OpenStreetMap contributors"},
it:{subtitle:"Bologna · trova il posto giusto",search_ph:"Cerca per nome o indirizzo…",sort_default:"Ordina: predefinito",sort_quiet:"Prima i silenziosi",sort_work:"Migliori per lavorare",sort_romantic:"Più romantici",sort_name:"Nome A–Z",preset_work:"🤫 Silenzioso",preset_date:"💑 Appuntamento",preset_party:"🎉 Festa",favs:"Preferiti",reset:"Azzera",filter_noise:"Rumore",filter_laptop:"Lavoro",filter_romantic:"Romantico",legend_quiet:"silenzioso",legend_mid:"medio",legend_loud:"rumoroso",found:"Trovati",of:"di",nothing_found:"Nessun risultato",nothing_hint:"Prova ad allargare i filtri o ad azzerarli.",error_title:"Impossibile caricare i luoghi",retry:"Riprova",loading:"Caricamento…",noise:"Rumore",work:"Lavoro",romantic:"Romantico",no_description:"Descrizione in arrivo.",route:"Percorso",show_map:"Mappa",address_unknown:"indirizzo in arrivo",fav_add:"Aggiunto ai preferiti",fav_remove:"Rimosso dai preferiti",undo:"Annulla",loc_err:"Posizione non disponibile",fit_title:"Mostra tutti",loc_title:"La mia posizione",data_note:"Dati © OpenStreetMap contributors"},
en:{subtitle:"Bologna · find a place that matches your mood",search_ph:"Search by name or address…",sort_default:"Sort: default",sort_quiet:"Quietest first",sort_work:"Best for work",sort_romantic:"Most romantic",sort_name:"Name A–Z",preset_work:"🤫 Quiet for work",preset_date:"💑 For a date",preset_party:"🎉 Party",favs:"Favorites",reset:"Reset",filter_noise:"Noise",filter_laptop:"For work",filter_romantic:"Romantic",legend_quiet:"quiet",legend_mid:"medium",legend_loud:"loud",found:"Found",of:"of",nothing_found:"Nothing found",nothing_hint:"Try loosening the filters or reset them.",error_title:"Could not load places",retry:"Retry",loading:"Loading places…",noise:"Noise",work:"Work",romantic:"Romantic",no_description:"Description coming soon.",route:"Route",show_map:"On map",address_unknown:"address pending",fav_add:"Added to favorites",fav_remove:"Removed from favorites",undo:"Undo",loc_err:"Location unavailable",fit_title:"Show all places",loc_title:"My location",data_note:"Data © OpenStreetMap contributors"}
};
let lang=localStorage.getItem('vs-lang')||'ru';
if(!T[lang])lang='ru';
let places=[],markers={},map=null,userMarker=null,toastTimer=null,loadFailed=false;
let favs=new Set();
try{favs=new Set(JSON.parse(localStorage.getItem('vs-favs')||'[]'))}catch(e){}
const state={q:'',sort:'default',favOnly:false,preset:null};
const $=id=>document.getElementById(id);
function t(k){return (T[lang]&&T[lang][k])||k}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function num(x){return typeof x==='number'&&isFinite(x)?x:0.5}
function noiseColor(v){return v<0.4?'#5F8F4E':v<0.7?'#E9A13B':'#C4472B'}

function setLanguage(l){
  lang=l;localStorage.setItem('vs-lang',l);document.documentElement.lang=l;
  document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.getAttribute('data-i18n'))});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{el.placeholder=t(el.getAttribute('data-i18n-ph'))});
  document.querySelectorAll('#sortSel option').forEach(o=>{o.textContent=t(o.getAttribute('data-i18n'))});
  document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('on',b.getAttribute('data-lang')===l));
  $('fitBtn').title=t('fit_title');$('fitBtn').setAttribute('aria-label',t('fit_title'));
  $('locBtn').title=t('loc_title');$('locBtn').setAttribute('aria-label',t('loc_title'));
  if(loadFailed)renderError();else applyFilters();
}

function makeIcon(p){
  const v=p.vibe_attributes[0],fav=favs.has(p.id);
  return L.divIcon({className:'vs-pin-wrap',html:'<span class="pin'+(fav?' fav':'')+'" style="background:'+noiseColor(v.noise_level)+'">'+(fav?'♥':'')+'</span>',iconSize:[22,22],iconAnchor:[11,11],popupAnchor:[0,-10]});
}
function popupHTML(p){
  const v=p.vibe_attributes[0],fav=favs.has(p.id);
  return '<div class="pop-t">'+esc(p.name)+'</div><div class="pop-a">'+esc(p.address||t('address_unknown'))+'</div>'
  +'<div class="pop-m"><div><b>'+v.noise_level.toFixed(1)+'</b><span>'+t('noise')+'</span></div><div><b>'+v.laptop_friendly.toFixed(1)+'</b><span>'+t('work')+'</span></div><div><b>'+v.romantic.toFixed(1)+'</b><span>'+t('romantic')+'</span></div></div>'
  +'<div class="pop-s">'+esc(v.summary||t('no_description'))+'</div>'
  +'<div class="pop-acts"><a target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination='+p.latitude+','+p.longitude+'">'+t('route')+'</a><button data-fav="'+p.id+'" class="'+(fav?'on':'')+'" aria-pressed="'+fav+'" onclick="toggleFav('+p.id+')">♥</button></div>';
}
function renderMarkers(list){
  if(!map)return;
  Object.keys(markers).forEach(k=>map.removeLayer(markers[k]));markers={};
  list.forEach(p=>{const mk=L.marker([p.latitude,p.longitude],{icon:makeIcon(p)}).addTo(map);mk.bindPopup(popupHTML(p),{maxWidth:270});markers[p.id]=mk;});
}
function met(label,val,color){
  return '<div class="met"><span class="met-l">'+label+'</span><span class="met-v">'+val.toFixed(1)+'</span><span class="bar"><i style="width:'+Math.round(val*100)+'%;background:'+color+'"></i></span></div>';
}
function cardHTML(p){
  const v=p.vibe_attributes[0],fav=favs.has(p.id);
  return '<article class="card" style="--spine:'+noiseColor(v.noise_level)+'">'
  +'<div class="card-top"><h3>'+esc(p.name)+'</h3><button class="heart'+(fav?' on':'')+'" data-fav="'+p.id+'" aria-pressed="'+fav+'" onclick="toggleFav('+p.id+')" aria-label="favorite">♥</button></div>'
  +'<p class="addr">'+esc(p.address||t('address_unknown'))+'</p>'
  +'<div class="mets">'+met(t('noise'),v.noise_level,noiseColor(v.noise_level))+met(t('work'),v.laptop_friendly,'#3E7CA6')+met(t('romantic'),v.romantic,'#7C2D3E')+'</div>'
  +'<p class="sum">'+esc(v.summary||t('no_description'))+'</p>'
  +'<div class="acts"><a class="btn primary" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination='+p.latitude+','+p.longitude+'">'+t('route')+'</a><button class="btn ghost" onclick="focusPlace('+p.id+')">'+t('show_map')+'</button></div>'
  +'</article>';
}
function emptyHTML(){
  return '<div class="notice"><div class="cup">☕</div><h3>'+t('nothing_found')+'</h3><p>'+t('nothing_hint')+'</p><button class="btn ghost" onclick="resetAll()">'+t('reset')+'</button></div>';
}
function renderSkeleton(){
  let h='';for(let i=0;i<3;i++)h+='<div class="card skel"><span class="sk l1"></span><span class="sk l2"></span><span class="sk l3"></span></div>';
  $('places').innerHTML=h;
}
function renderError(){
  $('stats').textContent='';
  $('places').innerHTML='<div class="notice"><div class="cup">⚠️</div><h3>'+t('error_title')+'</h3><button class="btn primary" onclick="loadPlaces()">'+t('retry')+'</button></div>';
}

function applyFilters(){
  const nMin=+$('nMin').value,nMax=+$('nMax').value,lMin=+$('lMin').value,lMax=+$('lMax').value,rMin=+$('rMin').value,rMax=+$('rMax').value;
  $('noiseVal').textContent=nMin.toFixed(1)+' – '+nMax.toFixed(1);
  $('laptopVal').textContent=lMin.toFixed(1)+' – '+lMax.toFixed(1);
  $('romanticVal').textContent=rMin.toFixed(1)+' – '+rMax.toFixed(1);
  let list=places.filter(p=>{
    const v=p.vibe_attributes[0];
    if(state.favOnly&&!favs.has(p.id))return false;
    if(state.q){const hay=((p.name||'')+' '+(p.address||'')+' '+(v.summary||'')).toLowerCase();if(hay.indexOf(state.q)===-1)return false;}
    return v.noise_level>=nMin&&v.noise_level<=nMax&&v.laptop_friendly>=lMin&&v.laptop_friendly<=lMax&&v.romantic>=rMin&&v.romantic<=rMax;
  });
  const k=state.sort;
  list.sort((a,b)=>{
    const va=a.vibe_attributes[0],vb=b.vibe_attributes[0];
    if(k==='quiet')return va.noise_level-vb.noise_level;
    if(k==='work')return vb.laptop_friendly-va.laptop_friendly;
    if(k==='romantic')return vb.romantic-va.romantic;
    if(k==='name')return String(a.name).localeCompare(String(b.name));
    return a.id-b.id;
  });
  renderMarkers(list);
  $('places').innerHTML=list.length?list.map(cardHTML).join(''):emptyHTML();
  $('stats').innerHTML=t('found')+': <b>'+list.length+'</b> '+t('of')+' '+places.length;
  document.querySelectorAll('.preset').forEach(b=>b.classList.toggle('on',b.getAttribute('data-preset')===state.preset));
  $('favChip').classList.toggle('on',state.favOnly);
  $('clearQ').classList.toggle('show',!!state.q);
}

function initMap(){
  if(map)return;
  map=L.map('map',{zoomControl:false});
  L.control.zoom({position:'bottomright'}).addTo(map);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:19}).addTo(map);
  setTimeout(()=>map.invalidateSize(),60);
}
function fitAll(){
  if(!map||!places.length)return;
  map.fitBounds(L.latLngBounds(places.map(p=>[p.latitude,p.longitude])),{padding:[36,36],maxZoom:16});
}
function focusPlace(id){
  const p=places.find(x=>x.id===id);if(!p||!map)return;
  $('mapWrap').scrollIntoView({behavior:'smooth',block:'start'});
  map.setView([p.latitude,p.longitude],17,{animate:true});
  if(markers[id])markers[id].openPopup();
}
function locate(){
  if(!navigator.geolocation){toast(t('loc_err'));return;}
  navigator.geolocation.getCurrentPosition(pos=>{
    const ll=[pos.coords.latitude,pos.coords.longitude];
    if(userMarker)map.removeLayer(userMarker);
    userMarker=L.marker(ll,{icon:L.divIcon({className:'vs-pin-wrap',html:'<span class="me"></span>',iconSize:[18,18],iconAnchor:[9,9]})}).addTo(map);
    map.setView(ll,15,{animate:true});
  },()=>toast(t('loc_err')),{timeout:8000});
}

function updateFavCount(){$('favCount').textContent=favs.size}
function setFav(id,on){
  if(on)favs.add(id);else favs.delete(id);
  localStorage.setItem('vs-favs',JSON.stringify(Array.from(favs)));
  document.querySelectorAll('[data-fav="'+id+'"]').forEach(b=>{b.classList.toggle('on',on);b.setAttribute('aria-pressed',on);});
  const p=places.find(x=>x.id===id);
  if(p&&markers[id])markers[id].setIcon(makeIcon(p));
  updateFavCount();
  if(state.favOnly)applyFilters();
}
function toggleFav(id){
  const on=!favs.has(id);setFav(id,on);
  if(on)toast(t('fav_add'));
  else toast(t('fav_remove'),t('undo'),function(){setFav(id,true)});
}
function toast(msg,label,fn){
  const el=$('toast');clearTimeout(toastTimer);
  el.innerHTML='<span>'+esc(msg)+'</span>'+(label?'<button id="toastAct">'+esc(label)+'</button>':'');
  el.classList.add('show');
  if(label)$('toastAct').onclick=function(){el.classList.remove('show');fn();};
  toastTimer=setTimeout(()=>el.classList.remove('show'),3500);
}

function applyPreset(type){
  state.preset=type;
  const set=(a,b)=>{$('nMin').value=a[0];$('nMax').value=a[1];$('lMin').value=b[0];$('lMax').value=b[1];};
  if(type==='work'){set([0,0.4],[0.6,1]);$('rMin').value=0;$('rMax').value=1;}
  else if(type==='date'){set([0,0.6],[0,1]);$('rMin').value=0.6;$('rMax').value=1;}
  else{set([0.6,1],[0,1]);$('rMin').value=0;$('rMax').value=0.4;}
  applyFilters();
}
function resetAll(){
  state.q='';state.sort='default';state.favOnly=false;state.preset=null;
  $('q').value='';$('sortSel').value='default';
  ['nMin','lMin','rMin'].forEach(id=>$(id).value=0);
  ['nMax','lMax','rMax'].forEach(id=>$(id).value=1);
  applyFilters();fitAll();
}

function loadPlaces(){
  loadFailed=false;
  $('stats').textContent=t('loading');
  renderSkeleton();
  fetch('/api/places',{cache:'no-store'})
  .then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
  .then(data=>{
    if(!Array.isArray(data))throw new Error('bad data');
    places=data.filter(p=>p&&p.latitude!=null&&p.longitude!=null).map(p=>{
      const v=(p.vibe_attributes&&p.vibe_attributes[0])||{};
      p.vibe_attributes=[{noise_level:num(v.noise_level),laptop_friendly:num(v.laptop_friendly),romantic:num(v.romantic),summary:v.summary||''}];
      return p;
    });
    initMap();fitAll();applyFilters();
  })
  .catch(()=>{loadFailed=true;renderError();});
}

[['nMin','nMax'],['lMin','lMax'],['rMin','rMax']].forEach(pair=>{
  const a=$(pair[0]),b=$(pair[1]);
  a.addEventListener('input',()=>{if(+a.value>+b.value)b.value=a.value;state.preset=null;applyFilters();});
  b.addEventListener('input',()=>{if(+b.value<+a.value)a.value=b.value;state.preset=null;applyFilters();});
});
$('q').addEventListener('input',e=>{state.q=e.target.value.trim().toLowerCase();applyFilters();});
$('clearQ').onclick=()=>{$('q').value='';state.q='';applyFilters();};
$('sortSel').onchange=e=>{state.sort=e.target.value;applyFilters();};
$('favChip').onclick=()=>{state.favOnly=!state.favOnly;applyFilters();};
$('resetBtn').onclick=resetAll;
$('fitBtn').onclick=fitAll;
$('locBtn').onclick=locate;
window.addEventListener('resize',()=>{if(map)map.invalidateSize();});

setLanguage(lang);
updateFavCount();
loadPlaces();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/healthz')
def healthz():
    return 'ok'

@app.route('/api/places')
def get_places():
    headers = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY}
    url = SUPABASE_URL + "/rest/v1/places?select=id,name,address,latitude,longitude,vibe_attributes(noise_level,laptop_friendly,romantic,summary)"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return jsonify({"error": "bad response"}), 502
        resp = jsonify(data)
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception:
        return jsonify({"error": "upstream unavailable"}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
