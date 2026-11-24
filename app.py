import os
from flask import Flask, render_template_string, jsonify, send_from_directory, request
import requests

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
    except ImportError:
        pass

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/healthz')
def healthz():
    return 'ok'

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json', mimetype='application/json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('.', 'service-worker.js', mimetype='application/javascript')

@app.route('/api/cities')
def get_cities():
    headers = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY}
    url = SUPABASE_URL + "/rest/v1/cities?select=id,name_ru,name_it,name_en,lat,lng,zoom,radius_km&active=eq.true&order=name_it"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        city = request.args.get('city', 'bologna')
        data = [p for p in data if p.get('city', 'bologna') == city]
        if not isinstance(data, list):
            return jsonify({"error": "bad response"}), 502
        return jsonify(data)
    except Exception:
        return jsonify({"error": "upstream unavailable"}), 502

@app.route('/api/places')
def get_places():
    headers = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY}
    url = SUPABASE_URL + "/rest/v1/places?select=id,name,address,latitude,longitude,image_url,vibe_attributes(noise_level,laptop_friendly,romantic,summary,summary_ru,summary_it,summary_en)"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 400:
            url = SUPABASE_URL + "/rest/v1/places?select=id,name,address,latitude,longitude,image_url,vibe_attributes(noise_level,laptop_friendly,romantic,summary)"
            response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        city = request.args.get('city', 'bologna')
        data = [p for p in data if p.get('city', 'bologna') == city]
        if not isinstance(data, list):
            return jsonify({"error": "bad response"}), 502
        resp = jsonify(data)
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception:
        return jsonify({"error": "upstream unavailable"}), 502

@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.json
    if not data or 'place_id' not in data or 'author_name' not in data:
        return jsonify({"error": "missing fields"}), 400
    headers = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY, "Content-Type": "application/json", "Prefer": "return=minimal"}
    payload = {
        "place_id": int(data['place_id']),
        "author_name": str(data['author_name'])[:100],
        "rating": min(5, max(1, int(data.get('rating', 5)))),
        "comment": str(data.get('comment', ''))[:1000]
    }
    try:
        r = requests.post(SUPABASE_URL + "/rest/v1/reviews", json=payload, headers=headers, timeout=15)
        if r.status_code in (200, 201, 204):
            return jsonify({"success": True}), 201
        return jsonify({"error": "failed", "status": r.status_code}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route('/api/reviews/<int:place_id>')
def get_reviews(place_id):
    headers = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY}
    url = SUPABASE_URL + f"/rest/v1/reviews?place_id=eq.{place_id}&order=created_at.desc&limit=10"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception:
        return jsonify([]), 200

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#C4472B">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2935/2935226.png">
<title>Vibe Search · Bologna</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
:root{--terracotta:#C4472B;--terracotta-deep:#93301C;--ochre:#E9A13B;--espresso:#2A1B12;--cream:#FAF1E4;--paper:#FFFDF8;--olive:#5F8F4E;--wine:#7C2D3E;--sky:#3E7CA6;--muted:#6B5A4E;--line:rgba(42,27,18,.12);--track:#E8DCC9}
*{margin:0;padding:0;box-sizing:border-box}html{scroll-behavior:smooth}
body{font-family:'Inter',system-ui,sans-serif;color:var(--espresso);background:radial-gradient(900px 420px at 85% -60px,rgba(233,161,59,.20),transparent 60%),radial-gradient(700px 380px at -80px 30%,rgba(196,71,43,.14),transparent 60%),var(--cream);min-height:100vh}
button{font:inherit;cursor:pointer}a{color:var(--terracotta-deep)}:focus-visible{outline:3px solid var(--sky);outline-offset:2px;border-radius:6px}
header{position:sticky;top:0;z-index:500;background:rgba(250,241,228,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.head-in{max-width:1180px;margin:0 auto;padding:12px 18px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{display:flex;align-items:center;gap:10px;font-family:'Fraunces',serif;font-weight:700;font-size:20px;color:var(--terracotta-deep)}
.langs{display:flex;gap:6px}.lang-btn{padding:7px 13px;border-radius:999px;border:1.5px solid rgba(147,48,28,.35);background:transparent;color:var(--terracotta-deep);font-weight:600;font-size:13px;transition:all .2s}
.lang-btn.on{background:var(--terracotta);border-color:var(--terracotta);color:var(--paper)}
.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 60px}
.hero h1{font-family:'Fraunces',serif;font-size:clamp(34px,6vw,52px);font-weight:700;color:var(--espresso);line-height:1.05}.hero h1 em{font-style:italic;color:var(--terracotta)}
.hero p{margin-top:8px;color:var(--muted);font-size:15px}
.arches{height:14px;margin:16px 0 20px;opacity:.5;background-image:radial-gradient(circle at 14px 14px,transparent 10px,var(--terracotta) 10.5px,var(--terracotta) 12px,transparent 12.5px);background-size:28px 14px;background-repeat:repeat-x}
.layout{display:grid;grid-template-columns:1fr;gap:20px}
.map-wrap{position:relative;height:310px;border-radius:18px;overflow:hidden;border:1px solid var(--line);box-shadow:0 14px 34px rgba(42,27,18,.16);background:var(--track)}
#map{position:absolute;inset:0}
.map-tools{position:absolute;top:12px;right:12px;z-index:800;display:flex;flex-direction:column;gap:8px}
.tool{width:40px;height:40px;border-radius:12px;border:1px solid var(--line);background:var(--paper);color:var(--terracotta-deep);display:grid;place-items:center;box-shadow:0 4px 12px rgba(42,27,18,.18);transition:all .2s}
.tool:hover{background:var(--terracotta);color:var(--paper)}
.legend{position:absolute;left:12px;bottom:12px;z-index:800;display:flex;gap:12px;background:rgba(255,253,248,.94);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:12px;font-weight:600;color:var(--muted);box-shadow:0 4px 12px rgba(42,27,18,.14)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.panel{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 10px 26px rgba(42,27,18,.10);display:flex;flex-direction:column;gap:14px}
.searchrow{position:relative}.searchrow input{width:100%;padding:12px 42px 12px 40px;border-radius:12px;border:1.5px solid var(--track);background:var(--cream);font:inherit;color:var(--espresso);transition:border .2s}
.searchrow input:focus{border-color:var(--terracotta);outline:none}
.searchrow .mag{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--muted)}
#clearQ{position:absolute;right:8px;top:50%;transform:translateY(-50%);width:28px;height:28px;border:none;border-radius:50%;background:var(--track);color:var(--espresso);font-size:15px;display:none}
#clearQ.show{display:block}
.row2{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
select{flex:1;min-width:170px;padding:10px 12px;border-radius:12px;border:1.5px solid var(--track);background:var(--cream);font:inherit;font-size:13px;font-weight:600;color:var(--espresso)}
.chip{padding:10px 14px;border-radius:999px;border:1.5px solid var(--track);background:var(--cream);font-size:13px;font-weight:600;color:var(--muted);transition:all .2s}
.chip:hover{border-color:var(--wine);color:var(--wine)}.chip.on{background:var(--wine);border-color:var(--wine);color:var(--paper)}.chip b{margin-left:4px}
.type-filter{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:4px}
.type-btn{padding:8px 14px;border-radius:999px;border:1.5px solid var(--track);background:var(--cream);font-size:13px;font-weight:600;color:var(--muted);transition:all .2s}
.type-btn:hover{border-color:var(--ochre);color:var(--ochre)}.type-btn.on{background:var(--ochre);border-color:var(--ochre);color:var(--espresso)}
.presets{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.preset{padding:12px 8px;border-radius:12px;border:1.5px solid var(--track);background:var(--cream);font-weight:600;font-size:13px;color:var(--espresso);transition:all .2s}
.preset:hover{transform:translateY(-1px);border-color:var(--ochre)}.preset.on{background:var(--ochre);border-color:var(--ochre);color:var(--espresso);box-shadow:0 6px 16px rgba(233,161,59,.4)}
.fgroup label{display:flex;align-items:center;gap:8px;font-weight:600;font-size:14px;margin-bottom:6px}
.fgroup .val{margin-left:auto;background:var(--espresso);color:var(--cream);font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;font-variant-numeric:tabular-nums}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:6px;border-radius:6px;background:var(--track);margin:7px 0}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:var(--terracotta);border:3px solid var(--paper);box-shadow:0 2px 6px rgba(42,27,18,.3);cursor:grab}
input[type=range]::-moz-range-thumb{width:14px;height:14px;border-radius:50%;background:var(--terracotta);border:3px solid var(--paper);box-shadow:0 2px 6px rgba(42,27,18,.3);cursor:grab}
input[type=range]::-moz-range-track{height:6px;border-radius:6px;background:var(--track)}
.stats{margin:18px 2px 12px;font-size:14px;font-weight:600;color:var(--muted)}.stats b{color:var(--terracotta-deep)}
.places{display:flex;flex-direction:column;gap:14px}
.card{background:var(--paper);border:1px solid var(--line);border-left:6px solid var(--spine,var(--terracotta));border-radius:16px;overflow:hidden;box-shadow:0 6px 18px rgba(42,27,18,.08);transition:transform .2s,box-shadow .2s;animation:rise .35s ease both}
.card:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(42,27,18,.14)}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.card-img{width:100%;height:180px;object-fit:cover;background:var(--track);display:block}
.card-img-placeholder{width:100%;height:180px;background:linear-gradient(135deg,var(--track) 0%,var(--cream) 100%);display:flex;align-items:center;justify-content:center;font-size:48px;color:var(--muted)}
.card-body{padding:18px}.card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.card h3{font-family:'Fraunces',serif;font-size:20px;font-weight:700;line-height:1.2}
.type-badge{display:inline-block;padding:3px 8px;border-radius:6px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-left:8px}
.type-badge.cafe{background:#E9A13B;color:var(--espresso)}
.type-badge.bar{background:#7C2D3E;color:var(--paper)}
.type-badge.restaurant{background:#5F8F4E;color:var(--paper)}
.heart{flex:none;width:36px;height:36px;border-radius:50%;border:1.5px solid var(--track);background:var(--cream);color:#C9B8A8;font-size:17px;line-height:1;transition:all .2s}
.heart:hover{border-color:var(--wine);color:var(--wine)}.heart.on{background:var(--wine);border-color:var(--wine);color:var(--paper)}
.addr{color:var(--muted);font-size:13px;margin:4px 0 12px}.dist{font-size:12px;color:var(--sky);margin-bottom:8px}
.mets{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px}.met{display:flex;flex-direction:column;gap:3px}
.met-l{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}.met-v{font-family:'Fraunces',serif;font-size:20px;font-weight:700}
.bar{height:5px;border-radius:5px;background:var(--track);overflow:hidden}.bar i{display:block;height:100%;border-radius:5px;transition:width .4s ease}
.sum{background:var(--cream);border-radius:10px;padding:11px 13px;font-size:13.5px;line-height:1.5;color:var(--muted);margin-bottom:14px}
.acts{display:flex;gap:8px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:10px 16px;border-radius:11px;font-weight:600;font-size:13.5px;text-decoration:none;border:1.5px solid transparent;transition:all .2s}
.btn.primary{background:var(--terracotta);color:var(--paper);flex:1}.btn.primary:hover{background:var(--terracotta-deep)}
.btn.ghost{background:transparent;border-color:rgba(147,48,28,.4);color:var(--terracotta-deep)}.btn.ghost:hover{border-color:var(--terracotta);background:rgba(196,71,43,.08)}
.notice{background:var(--paper);border:1px dashed rgba(147,48,28,.4);border-radius:16px;padding:34px 22px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:10px}
.notice .cup{font-size:38px}.notice h3{font-family:'Fraunces',serif;font-size:20px}.notice p{color:var(--muted);font-size:14px}
footer{margin-top:34px;text-align:center;color:var(--muted);font-size:12px}
.leaflet-container{font-family:'Inter',sans-serif;background:var(--track)}
.leaflet-popup-content-wrapper{background:var(--paper);color:var(--espresso);border-radius:14px;border:1px solid var(--line);box-shadow:0 12px 30px rgba(42,27,18,.25)}
.leaflet-popup-tip{background:var(--paper)}.leaflet-popup-content{margin:14px 16px;font-size:13px;line-height:1.45}
.leaflet-bar a{background:var(--paper);color:var(--terracotta-deep);border-bottom:1px solid var(--line)}
.vs-pin-wrap{background:none;border:none}
.pin{display:block;width:16px;height:16px;border-radius:50%;border:3px solid var(--paper);box-shadow:0 3px 8px rgba(42,27,18,.4);color:var(--paper);font-size:9px;line-height:16px;text-align:center}
.pin.fav{box-shadow:0 0 0 3px rgba(124,45,62,.4),0 3px 8px rgba(42,27,18,.4)}
.me{display:block;width:12px;height:12px;border-radius:50%;background:var(--sky);border:3px solid #fff;animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 3px rgba(62,124,166,.35)}70%{box-shadow:0 0 0 14px rgba(62,124,166,0)}100%{box-shadow:0 0 0 3px rgba(62,124,166,0)}}
.pop-img{width:100%;height:120px;object-fit:cover;border-radius:8px;margin-bottom:8px;background:var(--track)}
.pop-t{font-family:'Fraunces',serif;font-weight:700;font-size:16px;margin-bottom:2px}.pop-a{color:var(--muted);font-size:12px;margin-bottom:8px}.pop-dist{font-size:11px;color:var(--sky);margin-bottom:6px}
.pop-m{display:flex;gap:8px;margin-bottom:8px}.pop-m div{flex:1;text-align:center;background:var(--cream);border-radius:8px;padding:6px 2px}
.pop-m b{display:block;font-family:'Fraunces',serif;font-size:15px}.pop-m span{font-size:10px;color:var(--muted)}
.pop-s{color:var(--muted);font-size:12px;margin-bottom:10px}
.pop-reviews{border-top:1px solid var(--line);padding-top:8px;margin-top:8px}.pop-reviews h4{font-size:11px;font-weight:600;color:var(--muted);margin-bottom:6px}
.pop-review{font-size:11px;margin-bottom:6px}.pop-review b{color:var(--espresso)}.pop-review .stars{color:var(--ochre)}.pop-review .cmt{color:var(--muted);display:block;margin-top:2px}
.pop-review-form{margin-top:8px}.pop-review-form input,.pop-review-form textarea,.pop-review-form select{width:100%;padding:6px 8px;border:1px solid var(--track);border-radius:6px;font:inherit;font-size:11px;margin-bottom:4px;background:var(--cream);color:var(--espresso)}
.pop-review-form textarea{resize:vertical;min-height:40px}.pop-review-form button{width:100%;padding:7px;background:var(--terracotta);color:var(--paper);border:none;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer}
.pop-review-form button:hover{background:var(--terracotta-deep)}
.pop-acts{display:flex;gap:6px;margin-top:8px}.pop-acts a,.pop-acts button{flex:1;text-align:center;padding:7px 6px;border-radius:8px;font-size:12px;font-weight:600;text-decoration:none}
.pop-acts a{background:var(--terracotta);color:var(--paper)}.pop-acts button{border:1.5px solid var(--track);background:var(--cream);color:#C9B8A8}.pop-acts button.on{background:var(--wine);border-color:var(--wine);color:var(--paper)}
#toast{position:fixed;left:50%;bottom:22px;transform:translate(-50%,16px);z-index:1200;background:var(--espresso);color:var(--cream);padding:12px 18px;border-radius:12px;font-size:14px;font-weight:600;display:flex;gap:14px;align-items:center;box-shadow:0 12px 30px rgba(42,27,18,.4);opacity:0;pointer-events:none;transition:all .3s}
#toast.show{opacity:1;transform:translate(-50%,0);pointer-events:auto}#toast button{border:none;background:transparent;color:var(--ochre);font-weight:700;font-size:14px}
.install-banner{position:fixed;bottom:0;left:0;right:0;background:var(--terracotta);color:var(--paper);padding:14px 18px;display:flex;justify-content:space-between;align-items:center;gap:12px;z-index:1000;transform:translateY(100%);transition:transform .3s}
.install-banner.show{transform:translateY(0)}.install-banner button{background:var(--paper);color:var(--terracotta);border:none;padding:8px 16px;border-radius:8px;font-weight:600}
@media(min-width:980px){.layout{grid-template-columns:minmax(400px,46%) 1fr;align-items:start}.map-col{position:sticky;top:84px}.map-wrap{height:calc(100vh - 120px);min-height:480px}}

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

.city-switcher{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px}
.city-btn{padding:6px 12px;border-radius:999px;border:1.5px solid var(--track);background:var(--cream);font-size:12px;font-weight:600;color:var(--muted);transition:all .2s}
.city-btn:hover{border-color:var(--terracotta);color:var(--terracotta)}
.city-btn.on{background:var(--terracotta);border-color:var(--terracotta);color:var(--paper)}
body.dark .city-btn{background:#1f1610;border-color:rgba(245,230,211,.15);color:#b8a89a}
body.dark .city-btn:hover{border-color:#C4472B;color:#E9A13B}
body.dark .city-btn.on{background:#C4472B;border-color:#C4472B;color:#fff}

</style>
</head>
<body>
<header><div class="head-in">
  <div class="brand">☕ Vibe Search</div>
  <div class="langs"><button class="theme-btn" id="themeBtn" onclick="toggleTheme()" title="Сменить тему">🌙</button>
    <button class="lang-btn" data-lang="ru" onclick="setLanguage('ru')">RU</button>
    <button class="lang-btn" data-lang="it" onclick="setLanguage('it')">IT</button>
    <button class="lang-btn" data-lang="en" onclick="setLanguage('en')">EN</button>
  </div>
</div></header>
<div class="wrap">
  <div class="hero"><h1>Vibe <em>Search</em></h1><p data-i18n="subtitle">Болонья · найди место под настроение</p></div>
  <div class="arches"></div>
  <div class="layout">
    <div class="map-col">
      <div class="map-wrap" id="mapWrap">
        <div id="map"></div>
        <div class="map-tools">
          <button class="tool" id="fitBtn" title="Показать все">⊞</button>
          <button class="tool" id="locBtn" title="Моё место">◎</button>
        </div>
        <div class="legend"><span><i style="background:#5F8F4E"></i><span data-i18n="legend_quiet">тихо</span></span><span><i style="background:#E9A13B"></i><span data-i18n="legend_mid">средне</span></span><span><i style="background:#C4472B"></i><span data-i18n="legend_loud">шумно</span></span></div>
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
            <option value="nearby" data-i18n="sort_nearby">Ближайшие ко мне</option>
          </select>
          <button class="chip" id="favChip">♥ <span data-i18n="favs">Избранное</span> <b id="favCount">0</b></button>
          <button class="chip" id="resetBtn" data-i18n="reset">Сбросить</button>
        </div>
                <div class="city-switcher" id="citySwitcher">
          <button class="city-btn on" data-city="bologna" onclick="setCity('bologna')">🏛️ Bologna</button>
          <button class="city-btn" data-city="rome" onclick="setCity('rome')">🏛️ Roma</button>
          <button class="city-btn" data-city="milan" onclick="setCity('milan')">🏛️ Milano</button>
          <button class="city-btn" data-city="florence" onclick="setCity('florence')">🏛️ Firenze</button>
        </div>
        <div class="type-filter">
          <button class="type-btn on" data-type="all" onclick="setType('all')">🏪 <span data-i18n="type_all">Все</span></button>
          <button class="type-btn" data-type="cafe" onclick="setType('cafe')">☕ <span data-i18n="type_cafe">Кафе</span></button>
          <button class="type-btn" data-type="bar" onclick="setType('bar')">🍷 <span data-i18n="type_bar">Бары</span></button>
          <button class="type-btn" data-type="restaurant" onclick="setType('restaurant')">🍽️ <span data-i18n="type_restaurant">Рестораны</span></button>
        </div>
        <div class="presets">
          <button class="preset" data-preset="work" onclick="applyPreset('work')" data-i18n="preset_work">🤫 Тихо для работы</button>
          <button class="preset" data-preset="date" onclick="applyPreset('date')" data-i18n="preset_date">💑 Для свидания</button>
          <button class="preset" data-preset="party" onclick="applyPreset('party')" data-i18n="preset_party">🎉 Тусовка</button>
        </div>
        <div class="fgroup"><label><span data-i18n="filter_noise">Шум</span><span class="val" id="noiseVal">0.0 – 1.0</span></label><input type="range" id="nMin" min="0" max="1" step="0.1" value="0"><input type="range" id="nMax" min="0" max="1" step="0.1" value="1"></div>
        <div class="fgroup"><label><span data-i18n="filter_laptop">Для работы</span><span class="val" id="laptopVal">0.0 – 1.0</span></label><input type="range" id="lMin" min="0" max="1" step="0.1" value="0"><input type="range" id="lMax" min="0" max="1" step="0.1" value="1"></div>
        <div class="fgroup"><label><span data-i18n="filter_romantic">Романтика</span><span class="val" id="romanticVal">0.0 – 1.0</span></label><input type="range" id="rMin" min="0" max="1" step="0.1" value="0"><input type="range" id="rMax" min="0" max="1" step="0.1" value="1"></div>
      </section>
      <div class="stats" id="stats"></div>
      <div class="places" id="places"></div>
    </div>
  </div>
  <footer><span data-i18n="data_note">Данные © OpenStreetMap contributors</span> · Vibe Search</footer>
</div>
<div id="toast"></div>
<div class="install-banner" id="installBanner">
  <span data-i18n="install_text">Установить приложение?</span>
  <button id="installBtn" data-i18n="install_btn">Установить</button>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const T={ru:{subtitle:"Болонья · найди место под настроение",search_ph:"Поиск по названию или адресу…",sort_default:"Сортировка: по умолчанию",sort_quiet:"Сначала тихие",sort_work:"Лучшие для работы",sort_romantic:"Самые романтичные",sort_name:"По имени А–Я",sort_nearby:"Ближайшие ко мне",preset_work:"🤫 Тихо для работы",preset_date:"💑 Для свидания",preset_party:"🎉 Тусовка",favs:"Избранное",reset:"Сбросить",filter_noise:"Шум",filter_laptop:"Для работы",filter_romantic:"Романтика",legend_quiet:"тихо",legend_mid:"средне",legend_loud:"шумно",found:"Найдено",of:"из",nothing_found:"Ничего не найдено",nothing_hint:"Попробуй смягчить фильтры или сбросить их.",error_title:"Не удалось загрузить места",retry:"Повторить",loading:"Загружаем места…",noise:"Шум",work:"Работа",romantic:"Романтика",no_description:"Описание появится позже.",route:"Маршрут",show_map:"На карте",address_unknown:"адрес уточняется",fav_add:"Добавлено в избранное",fav_remove:"Убрано из избранного",undo:"Вернуть",loc_err:"Не удалось определить местоположение",fit_title:"Показать все места",loc_title:"Моё местоположение",data_note:"Данные © OpenStreetMap contributors",install_text:"Установить приложение?",install_btn:"Установить",km_away:"км от вас",m_away:"м от вас",reviews:"Отзывы",no_reviews:"Пока нет отзывов",your_name:"Твоё имя",comment:"Комментарий",submit_review:"Отправить",review_added:"✅ Отзыв добавлен!",review_error:"❌ Ошибка при отправке",review_load_err:"Не удалось загрузить",type_all:"Все",type_cafe:"Кафе",type_bar:"Бары",type_restaurant:"Рестораны"},it:{subtitle:"Bologna · trova il posto giusto",search_ph:"Cerca per nome o indirizzo…",sort_default:"Ordina: predefinito",sort_quiet:"Prima i silenziosi",sort_work:"Migliori per lavorare",sort_romantic:"Più romantici",sort_name:"Nome A–Z",sort_nearby:"Più vicini a me",preset_work:"🤫 Silenzioso",preset_date:"💑 Appuntamento",preset_party:"🎉 Festa",favs:"Preferiti",reset:"Azzera",filter_noise:"Rumore",filter_laptop:"Lavoro",filter_romantic:"Romantico",legend_quiet:"silenzioso",legend_mid:"medio",legend_loud:"rumoroso",found:"Trovati",of:"di",nothing_found:"Nessun risultato",nothing_hint:"Prova ad allargare i filtri o ad azzerarli.",error_title:"Impossibile caricare i luoghi",retry:"Riprova",loading:"Caricamento…",noise:"Rumore",work:"Lavoro",romantic:"Romantico",no_description:"Descrizione in arrivo.",route:"Percorso",show_map:"Mappa",address_unknown:"indirizzo in arrivo",fav_add:"Aggiunto ai preferiti",fav_remove:"Rimosso dai preferiti",undo:"Annulla",loc_err:"Posizione non disponibile",fit_title:"Mostra tutti",loc_title:"La mia posizione",data_note:"Dati © OpenStreetMap contributors",install_text:"Installare l'app?",install_btn:"Installa",km_away:"km da te",m_away:"m da te",reviews:"Recensioni",no_reviews:"Nessuna recensione",your_name:"Il tuo nome",comment:"Commento",submit_review:"Invia",review_added:"✅ Recensione aggiunta!",review_error:"❌ Errore nell'invio",review_load_err:"Impossibile caricare",type_all:"Tutti",type_cafe:"Caffè",type_bar:"Bar",type_restaurant:"Ristoranti"},en:{subtitle:"Bologna · find a place that matches your mood",search_ph:"Search by name or address…",sort_default:"Sort: default",sort_quiet:"Quietest first",sort_work:"Best for work",sort_romantic:"Most romantic",sort_name:"Name A–Z",sort_nearby:"Nearest to me",preset_work:"🤫 Quiet for work",preset_date:"💑 For a date",preset_party:"🎉 Party",favs:"Favorites",reset:"Reset",filter_noise:"Noise",filter_laptop:"For work",filter_romantic:"Romantic",legend_quiet:"quiet",legend_mid:"medium",legend_loud:"loud",found:"Found",of:"of",nothing_found:"Nothing found",nothing_hint:"Try loosening the filters or reset them.",error_title:"Could not load places",retry:"Retry",loading:"Loading places…",noise:"Noise",work:"Work",romantic:"Romantic",no_description:"Description coming soon.",route:"Route",show_map:"On map",address_unknown:"address pending",fav_add:"Added to favorites",fav_remove:"Removed from favorites",undo:"Undo",loc_err:"Location unavailable",fit_title:"Show all places",loc_title:"My location",data_note:"Data © OpenStreetMap contributors",install_text:"Install the app?",install_btn:"Install",km_away:"km away",m_away:"m away",reviews:"Reviews",no_reviews:"No reviews yet",your_name:"Your name",comment:"Comment",submit_review:"Submit",review_added:"✅ Review added!",review_error:"❌ Submission error",review_load_err:"Could not load",type_all:"All",type_cafe:"Cafés",type_bar:"Bars",type_restaurant:"Restaurants"}};

let lang=localStorage.getItem('vs-lang')||'ru';
if(!T[lang])lang='ru';
let places=[],markers=null,markerCluster=null,map=null,userMarker=null,toastTimer=null,loadFailed=false,userLocation=null;
let favs=new Set();
try{favs=new Set(JSON.parse(localStorage.getItem('vs-favs')||'[]'))}catch(e){}
const state={q:'',sort:'default',favOnly:false,preset:null,placeType:'all',currentCity:'bologna'};
const $=id=>document.getElementById(id);

function t(k){return (T[lang]&&T[lang][k])||k}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
function num(x){return typeof x==='number'&&isFinite(x)?x:0.5}
function noiseColor(v){return v<0.4?'#5F8F4E':v<0.7?'#E9A13B':'#C4472B'}
function summaryFor(v){return (v&&v['summary_'+lang])||v.summary||t('no_description')}
function haversine(lat1,lon1,lat2,lon2){const R=6371000,dLat=(lat2-lat1)*Math.PI/180,dLon=(lon2-lon1)*Math.PI/180,a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a))}
function formatDistance(m){return m<1000?Math.round(m)+' '+t('m_away'):(m/1000).toFixed(1)+' '+t('km_away')}
function getTypeIcon(type){return type==='cafe'?'☕':type==='bar'?'🍷':'🍽️'}
function getTypeName(type){return type==='cafe'?t('type_cafe'):type==='bar'?t('type_bar'):t('type_restaurant')}

function setLanguage(l){
  lang=l;localStorage.setItem('vs-lang',l);document.documentElement.lang=l;
  document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.getAttribute('data-i18n'))});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{el.placeholder=t(el.getAttribute('data-i18n-ph'))});
  document.querySelectorAll('#sortSel option').forEach(o=>{o.textContent=t(o.getAttribute('data-i18n'))});
  document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('on',b.getAttribute('data-lang')===l));
  $('fitBtn').title=t('fit_title');$('locBtn').title=t('loc_title');
  if(loadFailed)renderError();else applyFilters();
}

function setType(type){
  state.placeType=type;
  document.querySelectorAll('.type-btn').forEach(b=>b.classList.toggle('on',b.getAttribute('data-type')===type));
  applyFilters();
}

async function submitReview(e, placeId){
  e.preventDefault();
  const form=e.target;
  const data={
    place_id:placeId,
    author_name:form.querySelector('input[name="author"]').value.trim(),
    comment:form.querySelector('textarea[name="comment"]').value.trim(),
    rating:parseInt(form.querySelector('select[name="rating"]').value)
  };
  if(!data.author_name){toast('⚠️ '+t('your_name'));return;}
  try{
    const r=await fetch('/api/reviews',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    if(r.ok){toast(t('review_added'));form.reset();loadReviews(placeId);}
    else{toast(t('review_error'));}
  }catch(err){toast(t('review_error'));}
}

async function loadReviews(placeId){
  const el=document.getElementById('reviews-'+placeId);
  if(!el)return;
  try{
    const r=await fetch('/api/reviews/'+placeId);
    const reviews=await r.json();
    if(!reviews||reviews.length===0){el.innerHTML='<div style="font-size:11px;color:var(--muted)">'+t('no_reviews')+'</div>';return;}
    el.innerHTML=reviews.slice(0,3).map(rv=>{
      const stars='⭐'.repeat(Math.min(5,Math.max(1,rv.rating||5)));
      return '<div class="pop-review"><b>'+esc(rv.author_name)+'</b> <span class="stars">'+stars+'</span><span class="cmt">'+esc(rv.comment||'')+'</span></div>';
    }).join('');
  }catch(err){el.innerHTML='<div style="font-size:11px;color:var(--muted)">'+t('review_load_err')+'</div>';}
}

function makeIcon(p){
  const v=p.vibe_attributes,fav=favs.has(p.id);
  return L.divIcon({className:'vs-pin-wrap',html:'<span class="pin'+(fav?' fav':'')+'" style="background:'+noiseColor(v.noise_level)+'">'+(fav?'♥':'')+'</span>',iconSize:[22,22],iconAnchor:[11,11],popupAnchor:[0,-10]});
}

function popupHTML(p){
  const v=p.vibe_attributes,fav=favs.has(p.id);
  const imgHTML=p.image_url?'<img class="pop-img" src="'+esc(p.image_url)+'" alt="'+esc(p.name)+'" onerror="this.style.display=\'none\'">':'';
  const distHTML=userLocation?'<div class="pop-dist">📍 '+formatDistance(haversine(userLocation[0],userLocation[1],p.latitude,p.longitude))+'</div>':'';
  const typeBadge='<span class="type-badge '+p.place_type+'">'+getTypeIcon(p.place_type)+' '+getTypeName(p.place_type)+'</span>';
  return imgHTML+distHTML+'<div class="pop-t">'+esc(p.name)+' '+typeBadge+'</div><div class="pop-a">'+esc(p.address||t('address_unknown'))+'</div>'
  +'<div class="pop-m"><div><b>'+v.noise_level.toFixed(1)+'</b><span>'+t('noise')+'</span></div><div><b>'+v.laptop_friendly.toFixed(1)+'</b><span>'+t('work')+'</span></div><div><b>'+v.romantic.toFixed(1)+'</b><span>'+t('romantic')+'</span></div></div>'
  +'<div class="pop-s">'+esc(summaryFor(v))+'</div>'
  +'<div class="pop-reviews"><h4>💬 '+t('reviews')+'</h4><div id="reviews-'+p.id+'"><div style="font-size:11px;color:var(--muted)">'+t('loading')+'</div></div>'
  +'<form class="pop-review-form" onsubmit="submitReview(event,'+p.id+')"><input type="text" name="author" placeholder="'+esc(t('your_name'))+'" required maxlength="100"><textarea name="comment" placeholder="'+esc(t('comment'))+'" maxlength="1000"></textarea><select name="rating"><option value="5">⭐⭐⭐⭐⭐</option><option value="4">⭐⭐⭐⭐</option><option value="3">⭐⭐⭐</option><option value="2">⭐⭐</option><option value="1">⭐</option></select><button type="submit">'+esc(t('submit_review'))+'</button></form></div>'
  +'<div class="pop-acts"><a target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination='+p.latitude+','+p.longitude+'">'+t('route')+'</a><button data-fav="'+p.id+'" class="'+(fav?'on':'')+'" aria-pressed="'+fav+'" onclick="toggleFav('+p.id+')">♥</button></div>';
}

function renderMarkers(list){
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
}

function met(label,val,color){
  return '<div class="met"><span class="met-l">'+label+'</span><span class="met-v">'+val.toFixed(1)+'</span><span class="bar"><i style="width:'+Math.round(val*100)+'%;background:'+color+'"></i></span></div>';
}

function cardHTML(p){
  const v=p.vibe_attributes,fav=favs.has(p.id);
  const imgHTML=p.image_url?'<img class="card-img" src="'+esc(p.image_url)+'" alt="'+esc(p.name)+'" onerror="this.outerHTML=\'<div class=card-img-placeholder>☕</div>\'">':'<div class="card-img-placeholder">☕</div>';
  const distHTML=userLocation?'<div class="dist">📍 '+formatDistance(haversine(userLocation[0],userLocation[1],p.latitude,p.longitude))+'</div>':'';
  const typeBadge='<span class="type-badge '+p.place_type+'">'+getTypeIcon(p.place_type)+' '+getTypeName(p.place_type)+'</span>';
  return '<article class="card" style="--spine:'+noiseColor(v.noise_level)+'">'+imgHTML
  +'<div class="card-body"><div class="card-top"><h3>'+esc(p.name)+' '+typeBadge+'</h3><button class="heart'+(fav?' on':'')+'" data-fav="'+p.id+'" aria-pressed="'+fav+'" onclick="toggleFav('+p.id+')" aria-label="favorite">♥</button></div>'
  +'<p class="addr">'+esc(p.address||t('address_unknown'))+'</p>'+distHTML
  +'<div class="mets">'+met(t('noise'),v.noise_level,noiseColor(v.noise_level))+met(t('work'),v.laptop_friendly,'#3E7CA6')+met(t('romantic'),v.romantic,'#7C2D3E')+'</div>'
  +'<p class="sum">'+esc(summaryFor(v))+'</p>'
  +'<div class="acts"><a class="btn primary" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination='+p.latitude+','+p.longitude+'">'+t('route')+'</a><button class="btn ghost" onclick="focusPlace('+p.id+')">'+t('show_map')+'</button></div></div></article>';
}

function emptyHTML(){return '<div class="notice"><div class="cup">☕</div><h3>'+t('nothing_found')+'</h3><p>'+t('nothing_hint')+'</p><button class="btn ghost" onclick="resetAll()">'+t('reset')+'</button></div>';}
function renderError(){$('stats').textContent='';$('places').innerHTML='<div class="notice"><div class="cup">⚠️</div><h3>'+t('error_title')+'</h3><button class="btn primary" onclick="loadPlaces()">'+t('retry')+'</button></div>';}

function applyFilters(){
  const nMin=+$('nMin').value,nMax=+$('nMax').value,lMin=+$('lMin').value,lMax=+$('lMax').value,rMin=+$('rMin').value,rMax=+$('rMax').value;
  $('noiseVal').textContent=nMin.toFixed(1)+' – '+nMax.toFixed(1);
  $('laptopVal').textContent=lMin.toFixed(1)+' – '+lMax.toFixed(1);
  $('romanticVal').textContent=rMin.toFixed(1)+' – '+rMax.toFixed(1);
  let list=places.filter(p=>{
    const v=p.vibe_attributes;
    if(state.favOnly&&!favs.has(p.id))return false;
    if(state.placeType!=='all'&&p.place_type!==state.placeType)return false;
    if(state.q){const hay=((p.name||'')+' '+(p.address||'')+' '+(v.summary||'')+' '+(v.summary_ru||'')+' '+(v.summary_it||'')+' '+(v.summary_en||'')).toLowerCase();if(hay.indexOf(state.q)===-1)return false;}
    return v.noise_level>=nMin&&v.noise_level<=nMax&&v.laptop_friendly>=lMin&&v.laptop_friendly<=lMax&&v.romantic>=rMin&&v.romantic<=rMax;
  });
  const k=state.sort;
  list.sort((a,b)=>{
    const va=a.vibe_attributes,vb=b.vibe_attributes;
    if(k==='quiet')return va.noise_level-vb.noise_level;
    if(k==='work')return vb.laptop_friendly-va.laptop_friendly;
    if(k==='romantic')return vb.romantic-va.romantic;
    if(k==='name')return String(a.name).localeCompare(String(b.name));
    if(k==='nearby'&&userLocation){return haversine(userLocation[0],userLocation[1],a.latitude,a.longitude)-haversine(userLocation[0],userLocation[1],b.latitude,b.longitude);}
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
function fitAll(){if(!map||!places.length)return;const city=citiesData.find(c=>c.id===state.currentCity);if(city){map.setView([city.lat,city.lng],city.zoom||14);}map.fitBounds(L.latLngBounds(places.map(p=>[p.latitude,p.longitude])),{padding:[36,36],maxZoom:16});}
function focusPlace(id){const p=places.find(x=>x.id===id);if(!p||!map)return;$('mapWrap').scrollIntoView({behavior:'smooth',block:'start'});map.setView([p.latitude,p.longitude],17,{animate:true});if(markers[id])markers[id].openPopup();}
function locate(){
  if(!navigator.geolocation){toast(t('loc_err'));return;}
  navigator.geolocation.getCurrentPosition(pos=>{
    userLocation=[pos.coords.latitude,pos.coords.longitude];
    if(userMarker)map.removeLayer(userMarker);
    userMarker=L.marker(userLocation,{icon:L.divIcon({className:'vs-pin-wrap',html:'<span class="me"></span>',iconSize:[18,18],iconAnchor:[9,9]})}).addTo(map);
    map.setView(userLocation,15,{animate:true});
    if(state.sort==='nearby')applyFilters();else toast('📍 OK');
  },()=>toast(t('loc_err')),{timeout:8000,enableHighAccuracy:true});
}

function updateFavCount(){$('favCount').textContent=favs.size}
function setFav(id,on){
  if(on)favs.add(id);else favs.delete(id);
  localStorage.setItem('vs-favs',JSON.stringify(Array.from(favs)));
  document.querySelectorAll('[data-fav="'+id+'"]').forEach(b=>{b.classList.toggle('on',on);b.setAttribute('aria-pressed',on);});
  const p=places.find(x=>x.id===id);if(p&&markers[id])markers[id].setIcon(makeIcon(p));
  updateFavCount();if(state.favOnly)applyFilters();
}
function toggleFav(id){const on=!favs.has(id);setFav(id,on);if(on)toast(t('fav_add'));else toast(t('fav_remove'),t('undo'),function(){setFav(id,true)});}
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
  state.q='';state.sort='default';state.favOnly=false;state.preset=null;state.placeType='all';state.currentCity='bologna';
  $('q').value='';$('sortSel').value='default';
  ['nMin','lMin','rMin'].forEach(id=>$(id).value=0);['nMax','lMax','rMax'].forEach(id=>$(id).value=1);
  document.querySelectorAll('.type-btn').forEach(b=>b.classList.toggle('on',b.getAttribute('data-type')==='all'));
  applyFilters();fitAll();
}

function loadPlaces(){
  loadFailed=false;$('stats').textContent=t('loading');$('places').innerHTML='';
  fetch('/api/places',{cache:'no-store'})
  .then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
  .then(data=>{
    if(!Array.isArray(data))throw new Error('bad data');
    places=data.filter(p=>p&&p.latitude!=null&&p.longitude!=null).map(p=>{
      let v=p.vibe_attributes;if(Array.isArray(v))v=v[0]||{};if(!v||typeof v!=='object')v={};
      p.vibe_attributes={noise_level:num(v.noise_level),laptop_friendly:num(v.laptop_friendly),romantic:num(v.romantic),summary:v.summary||'',summary_ru:v.summary_ru||'',summary_it:v.summary_it||'',summary_en:v.summary_en||''};
      if(!p.place_type)p.place_type='cafe';
      return p;
    });
    initMap();fitAll();applyFilters();
  }).catch(err=>{loadFailed=true;console.error(err);renderError();});
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
$('resetBtn').onclick=resetAll;$('fitBtn').onclick=fitAll;$('locBtn').onclick=locate;
window.addEventListener('resize',()=>{if(map)map.invalidateSize();});

let deferredPrompt;
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;$('installBanner').classList.add('show');});
$('installBtn').onclick=async()=>{if(!deferredPrompt)return;deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null;$('installBanner').classList.remove('show');};
if('serviceWorker' in navigator){navigator.serviceWorker.register('/service-worker.js').catch(()=>{});}

setLanguage(lang);updateFavCount();loadCities();loadPlaces();

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
        '<button class="city-btn' + (c.id === saved ? ' on' : '') + '" data-city="' + c.id + '" onclick="setCity(\'' + c.id + '\')">' + 
        '🏛️ ' + c['name_' + lang] + '</button>'
      ).join('');
    }
    const city = data.find(c => c.id === saved);
    if(city && map){
      map.setView([city.lat, city.lng], city.zoom || 14);
    }
  }).catch(() => {});
}


function toggleTheme(){
  document.body.classList.toggle('dark');
  const isDark=document.body.classList.contains('dark');
  localStorage.setItem('vs-theme',isDark?'dark':'light');
  document.getElementById('themeBtn').textContent=isDark?'☀️':'🌙';
}
function applySavedTheme(){
  const saved=localStorage.getItem('vs-theme');
  if(saved==='dark'){
    document.body.classList.add('dark');
    document.getElementById('themeBtn').textContent='☀️';
  }
}

</script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
